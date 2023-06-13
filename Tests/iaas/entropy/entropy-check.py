#!/usr/bin/env python3
"""Entropy checker

Return codes:
0:    Enough entropy is available, no errors or warnings during execution

1:    The cloud parameter wasn't provided
2:    The used parameters were incorrect
3:    No connection to the OpenStack Cloud possible

10:   At least one VM doesn't have the required fixed entropy available
11:   At least one VM had too many FIPS 140-2 failures during the test
19:   Error during the VM requirements check routine

20:   At least one image is missing the recommended HWRNG attributes
29:   Error during the image attribute check routine

30:   At least one flavor is missing the recommended HWRNG attributes
31:   At least one flavor doesn't have the optionally recommended HWRNG attributes
39:   Error during the flavor attribute check routine

40:   At least one VM doesn't provide the recommended RNG daemon
49:   Error during the VM service check routine

All return codes between (and including) 1-19 as well as all return codes ending on 9
can be seen as failures.

Check given cloud for conformance with SCS standard regarding
entropy, to be found under /Standards/scs-0101-v1-entropy.md
"""
import errno
import getopt
import os
import re
import sys
import time

import fabric
import keystoneauth1.exceptions
import openstack
from openstack.cloud import exc

server_name = "test"
security_group_name = "test-group"
keypair_name = "test-keypair"


def print_usage(file=sys.stderr):
    """help output"""
    print("""Usage: entropy-check.py [options]
Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD
 and checks for the presence of the mandatory SCS flavors (read from mand.yaml)
 and reports inconsistencies, errors etc. It returns 0 on success.
""", end='', file=file)


class InternalProcessException(Exception):
    """Raised when an error happens during an internal process"""
    pass


def check_image_attributes(conn):
    return_code = 0

    image_attributes = ["hw_rng_model"]

    for image in conn.image.images():
        image_info = conn.image.get_image(image['id'])
        image_info = image_info.to_dict()

        if image_info[image_attributes[0]] is not None and \
                image_info[image_attributes[0]] == "virtio":
            pass
        else:
            print(f"INFO: Image {image_info['name']} doesn't have recommended attribute {image_attributes[0]}")
            return_code = 20
    return return_code


def check_flavor_attributes(conn):
    return_code = 0

    flavor_attributes = ["hw_rng:allowed", "hw_rng:rate_bytes", "hw_rng:rate_period"]

    for flavor in conn.compute.flavors():
        flavor_info = conn.compute.get_flavor(flavor['id'], get_extra_specs=True)
        flavor_info = flavor_info.to_dict()

        for k, v in flavor_info['extra_specs'].items():
            for attr in flavor_attributes:
                if k == attr and v:
                    pass
                else:
                    print(f"INFO: Flavor {flavor_info['name']} doesn't have recommended attribute {attr}")
                    if attr == "hw_rng:allowed":
                        return_code = 30
                    else:
                        return_code = 31
    return return_code


def check_vm_requirements(host, user):
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})

        entropy_avail = fconn.run('cat /proc/sys/kernel/random/entropy_avail', hide=True).stdout

        _ = fconn.run('sudo apt-get update && sudo apt-get install rng-tools', hide=True).stdout
        try:
            fips_data = fconn.run('cat /dev/random | rngtest -c 1000', hide=True).stderr
        except Exception as e:
            fips_data = e.result.stderr
            pass
    except Exception as e:
        raise InternalProcessException(str(e))
    finally:
        fconn.close()

    if int(entropy_avail) != 256:
        print(f"ERROR: The tested VM doesn't have a fixed amount of entropy available. "
              f"Excepted 256, got {entropy_avail}.")
        return str(5)

    failure_re = re.search(r'failures:\s\d+', fips_data, flags=re.MULTILINE)
    fips_failures = failure_re.string[failure_re.regs[0][0]:failure_re.regs[0][1]].split(" ")[1]
    if int(fips_failures) > 3:
        print(f"ERROR: The tested VM didn't pass the FIPS 140-2 testing."
              f"Excepted a maximum of 3 failures, got {fips_data}.")
        return 11
    return 0


def check_services(host, user):
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})

        service_status = fconn.run('sudo systemctl status rngd', hide=True).stdout
        if "could not be found" in service_status:
            print(f"INFO: VM {host} doesn't provide the recommended service rngd")
            return 30
    except Exception as e:
        if "could not be found" in e.result.stderr:
            print(f"INFO: VM {host} doesn't provide the recommended service rngd")
            return 30
        else:
            raise InternalProcessException(str(e))
    finally:
        fconn.close()
    return 0


def create_vm(conn):
    try:
        # Create a keypair and save both parts for later usage
        keypair = conn.compute.create_keypair(name=keypair_name)

        try:
            os.mkdir("./")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        with open('key.priv', 'w') as f:
            f.write("%s" % keypair.private_key)
            f.close()
        os.chmod('key.priv', 0o400)

        # Create a new security group and give it some simple rules in order to access it via SSH
        example_sec_group = conn.network.create_security_group(
            name=security_group_name
        )

        _ = conn.network.create_security_group_rule(
            security_group_id=example_sec_group.id,
            direction='ingress',
            remote_ip_prefix='0.0.0.0/0',
            protocol='icmp',
            port_range_max=None,
            port_range_min=None,
            ethertype='IPv4',
        )
        _ = conn.network.create_security_group_rule(
            security_group_id=example_sec_group.id,
            direction='ingress',
            remote_ip_prefix='0.0.0.0/0',
            protocol='tcp',
            port_range_max=22,
            port_range_min=22,
            ethertype='IPv4',
        )

        # Pick an image and a flavor and create a server with both of them and
        # the previously created keys and security group
        image = None
        flavor = None
        for i in conn.image.images():
            image = i
            if 'Ubuntu' in i.to_dict()['name']:
                break

        j = 0
        for f in conn.compute.flavors():
            flavor = f
            j += 1
            if j == 2:
                break

        server = conn.create_server(server_name, image=image, flavor=flavor, key_name=keypair.name,
                                    security_groups=['test-group'], wait=True, auto_ip=True)

        return [server.to_dict(), image.to_dict()]
    except exc.OpenStackCloudException as e:
        raise e


def delete_vm(conn):
    try:
        _ = conn.delete_server(server_name, wait=True)
    except exc.OpenStackCloudException:
        print(f"DEBUG: The server {server_name} couldn't be deleted.")
        pass

    try:
        for sg in conn.network.security_groups():
            sg = sg.to_dict()
            if sg['name'] == "test-group":
                _ = conn.network.delete_security_group(sg['id'])
    except (exc.OpenStackCloudException, exc.OpenStackCloudUnavailableFeature):
        print(f"DEBUG: The security group {security_group_name} couldn't be deleted.")
        pass

    try:
        fips = conn.list_floating_ips()
        for fip in fips:
            if fip.status == 'DOWN':
                _ = conn.delete_floating_ip(fip.id, retry=5)
    except exc.OpenStackCloudException:
        print(f"DEBUG: The floating_ip {fip} couldn't be deleted.")
        pass

    try:
        os.remove("./key.priv")
    except OSError:
        print("DEBUG: The key file 'key.priv' couldn't be deleted.")
        pass

    try:
        _ = conn.compute.delete_keypair(keypair_name)
    except exc.OpenStackCloudException:
        print(f"DEBUG: The keypair {keypair_name} couldn't be deleted.")
        pass


def main(argv):
    try:
        opts, args = getopt.gnu_getopt(argv, "c:h", ["os-cloud=", "help"])
    except getopt.GetoptError as exc:
        print(f"{exc}", file=sys.stderr)
        print_usage()
        return 1

    cloud = os.environ.get("OS_CLOUD")
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        else:
            print_usage()
            return 2

    if not cloud:
        print("ERROR: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        return 1

    try:
        conn = openstack.connect(cloud=cloud, timeout=32)
    except keystoneauth1.exceptions.MissingRequiredOptions:
        print("ERROR: Connection to the OpenStack cloud wasn't possible.")
        return 3

    return_code = 0

    # Check the images for HWRNG attributes (RECOMMENDED)
    try:
        return_code = check_image_attributes(conn)
    except BaseException:
        return_code = 19
        pass

    # Check the flavors for HWRNG attributes (RECOMMENDED)
    try:
        rc = check_flavor_attributes(conn)
        if rc != 0:
            return_code = rc
    except BaseException:
        return_code = 29
        pass

    # Check a VM for services and requirements
    try:
        si = create_vm(conn)

        # Sleep, in order for the VM to show up completely
        time.sleep(30)

        host = si[0]['public_v4']
        user = si[1]['properties']['standarduser']

        # Check the VM for running services (RECOMMENDED)
        try:
            rc = check_services(host, user)
            if rc != 0:
                return_code = rc
        except InternalProcessException:
            return_code = 39
            pass

        # Check the VM for specific requirements (REQUIRED)
        try:
            rc = check_vm_requirements(host, user)
            if rc != 0:
                return_code = rc
        except InternalProcessException:
            return_code = 19
            pass
    except (BaseException, InternalProcessException, exc.OpenStackCloudException):
        pass
    finally:
        delete_vm(conn)

    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
