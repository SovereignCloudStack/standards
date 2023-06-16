#!/usr/bin/env python3
"""Entropy checker

Return codes:
0:    Enough entropy is available, no errors or warnings during execution

1:    The cloud parameter or OS_CLOUD env variable wasn't provided
2:    No connection to the OpenStack Cloud possible

10:   At least one image of a VM couldn't be found
11:   At least one VM doesn't have the required fixed entropy available
12:   At least one VM had too many FIPS 140-2 failures during the test
19:   Error during the VM requirements check routine

20:   At least one image is missing the recommended HWRNG attributes
29:   Error during the image attribute check routine

30:   At least one flavor is missing the recommended HWRNG attributes
31:   At least one flavor doesn't have the optionally recommended HWRNG attributes
39:   Error during the flavor attribute check routine

40:   At least one VM doesn't provide the recommended RNG daemon
41:   At least one VM doesn't provide the recommended RNG device
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
import openstack.cloud
import invoke


server_name = "test"
security_group_name = "test-group"
keypair_name = "test-keypair"

mand_images = ["Ubuntu 22.04", "Ubuntu 20.04", "Debian 11"]
rec1_images = ["CentOS 8", "Rocky 8", "AlmaLinux 8", "Debian 10", "Fedora 36"]
rec2_images = ["SLES 15SP4", "RHEL 9", "RHEL 8"]
# , "Windows Server 2022", "Windows Server 2019"] we can't test Windows in this case
sugg_images = ["openSUSE Leap 15.4", "Cirros 0.5.2", "Alpine", "Arch"]


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: entropy-check.py [options]\n
This tool checks the requested images and flavors according to the SCS Standard 0101 "Entropy".\n
Options:
\t[-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env) \n
\t[-i/--images IMAGE_LIST] sets the images, which should be tested. Images should be contained in the
\t\tSCS Standard 0102 "Image Metadata". It is possible to either define image names (e.g. Ubuntu),
\t\twhich would trigger a check on their latest version according to the Standard or test one of the
\t\tprovided lists from the Standard. The possibilities include:
\t\t\t* mandatory
\t\t\t* recommended
\t\t\t* recommended+
\t\t\t* suggested
\t\tIt is also possible to test multiple things at once by chaining them with a comma, e.g.
\t\t'-i mandatory,recommended+' would test the mandatory and recommended+ lists respectively.
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


def check_vm_requirements(host, user, image_name):
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})

        entropy_avail = fconn.run('cat /proc/sys/kernel/random/entropy_avail', hide=True).stdout

        _ = fconn.run('sudo apt-get update && sudo apt-get install -y rng-tools', hide=True).stdout
        try:
            fips_data = fconn.run('cat /dev/random | rngtest -c 1000', hide=True).stderr
        except invoke.exceptions.UnexpectedExit as e:
            fips_data = e.result.stderr
            pass
    except (invoke.exceptions.UnexpectedExit, BaseException) as e:
        raise InternalProcessException(str(e))
    finally:
        fconn.close()

    if int(entropy_avail) != 256:
        print(f"ERROR: VM ({image_name}) didn't have a fixed amount of entropy available. "
              f"Excepted 256, got {entropy_avail}.")
        return str(5)

    failure_re = re.search(r'failures:\s\d+', fips_data, flags=re.MULTILINE)
    fips_failures = failure_re.string[failure_re.regs[0][0]:failure_re.regs[0][1]].split(" ")[1]
    if int(fips_failures) > 3:
        print(f"ERROR: VM ({image_name}) didn't pass the FIPS 140-2 testing."
              f"Excepted a maximum of 3 failures, got {fips_failures}.")
        return 11
    return 0


def check_vm_recommends(host, user, image_name):
    return_code = 0
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})

        try:
            service_status = fconn.run('sudo systemctl status rngd', hide=True).stdout
            if "could not be found" in service_status:
                print(f"INFO: VM ({image_name}) doesn't provide the recommended service rngd")
                return_code = 30
        except (invoke.exceptions.UnexpectedExit, BaseException) as e:
            if "could not be found" in e.result.stderr:
                print(f"INFO: VM ({image_name}) doesn't provide the recommended service rngd")
                return_code = 30
            else:
                raise InternalProcessException(str(e))
        try:
            hw_device = fconn.run('cat /sys/devices/virtual/misc/hw_random/rng_available', hide=True).stdout
            if not hw_device.strip("\n"):
                print(f"INFO: VM ({image_name}) doesn't provide a hardware device.")
                return_code = 31
            else:
                hw_device_data = fconn.run("sudo su -c 'od -vAn -N2 -tu2 < /dev/hwrng'", hide=True).stdout
                if "No such device" in hw_device_data:
                    print(f"INFO: VM ({image_name}) doesn't provide a hardware device.")
                    return_code = 31
        except (invoke.exceptions.UnexpectedExit, BaseException) as e:
            if "No such " in e.result.stderr:
                print(f"INFO: VM ({image_name}) doesn't provide a hardware device.")
                return_code = 31
            else:
                raise InternalProcessException(str(e))
    except InternalProcessException as e:
        raise e
    finally:
        fconn.close()
    return return_code


def prepare_environment(conn):
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

        return {"keypair": keypair}
    except openstack.cloud.OpenStackCloudException as e:
        raise e


def clean_environment(conn):

    try:
        for sg in conn.network.security_groups():
            sg = sg.to_dict()
            if sg['name'] == security_group_name:
                _ = conn.network.delete_security_group(sg['id'])
    except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
        print(f"DEBUG: The security group {security_group_name} couldn't be deleted.")
        pass

    fip = None
    try:
        fips = conn.list_floating_ips()
        for fip in fips:
            if fip.status == 'DOWN':
                _ = conn.delete_floating_ip(fip.id, retry=5)
    except openstack.cloud.OpenStackCloudException:
        print(f"DEBUG: The floating_ip {fip} couldn't be deleted.")
        pass

    try:
        os.remove("./key.priv")
    except OSError:
        print("DEBUG: The key file 'key.priv' couldn't be deleted.")
        pass

    try:
        _ = conn.compute.delete_keypair(keypair_name)
    except openstack.cloud.OpenStackCloudException:
        print(f"DEBUG: The keypair {keypair_name} couldn't be deleted.")
        pass


def create_vm(conn, vm_info, requested_image):
    try:
        # Pick an image and a flavor and create a server with both of them and
        # the previously created keys and security group
        image = None
        flavor = None

        for img in conn.image.images():
            if img.os_distro and img.os_version and img.status == "active" and \
               requested_image.lower() in (img.os_distro.lower() + " " + img.os_version.lower()) and \
               requested_image.lower() in img.name.lower():

                image = img
                break

        if not image:
            print(f"ERROR: The requested image {requested_image} couldn't be found")
            raise InternalProcessException("The requested image couldn't be found.")

        for flv in conn.compute.flavors():
            if flv.disk >= image.min_disk and flv.ram >= image.min_ram:
                flavor = flv
                break

        if not flavor:
            print(f"ERROR: No flavor could be found for the image {requested_image}")
            raise InternalProcessException("No flavor for the image was available.")

        server = conn.create_server(server_name, image=image, flavor=flavor, key_name=vm_info['keypair'].name,
                                    security_groups=security_group_name, wait=True, timeout=300, auto_ip=True)

        return [server.to_dict(), image.to_dict()]
    except (openstack.cloud.OpenStackCloudException, InternalProcessException) as e:
        raise e


def delete_vm(conn):
    try:
        _ = conn.delete_server(server_name, timeout=300, wait=True)
    except openstack.cloud.OpenStackCloudException:
        print(f"DEBUG: The server {server_name} couldn't be deleted.")
        pass


def main(argv):
    try:
        opts, args = getopt.gnu_getopt(argv, "c:i:h", ["os-cloud=", "images=", "help"])
    except getopt.GetoptError as exc:
        print(f"{exc}", file=sys.stderr)
        print_usage()
        return 1

    cloud = os.environ.get("OS_CLOUD")
    images = [mand_images[0].lower()]
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-i" or opt[1] == "--images":
            images = []
            for img in opt[1].lower().split(','):
                if img == "mandatory":
                    images += mand_images
                elif img == "recommended":
                    images += rec1_images
                elif img == "recommended+":
                    images += rec2_images
                elif img == "suggested":
                    images += sugg_images
                else:
                    list_length = len(images)
                    for i in (mand_images + rec1_images + rec2_images + sugg_images):
                        if img in i.lower():
                            images.append(i)
                            break
                    if list_length == len(images):
                        images.append(img)

        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]

    if not cloud:
        print("ERROR: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        return 1

    try:
        conn = openstack.connect(cloud=cloud, timeout=32)
    except keystoneauth1.exceptions.MissingRequiredOptions:
        print("ERROR: Connection to the OpenStack cloud wasn't possible.")
        return 2

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

    # Prepare the environment for the VMs
    try:
        vm_info = prepare_environment(conn)

        # Check a VM for services and requirements
        for image in images:
            try:
                try:
                    si = create_vm(conn, vm_info, image)
                except InternalProcessException as e:
                    return_code = 10
                    raise e

                # Sleep, in order for the VM to show up completely
                time.sleep(30)

                host = si[0]['public_v4']
                user = si[1]['properties']['standarduser']

                # Check the VM for running services (RECOMMENDED)
                try:
                    rc = check_vm_recommends(host, user, si[1]['name'])
                    if rc != 0:
                        return_code = rc
                except InternalProcessException:
                    return_code = 39
                    pass

                # Check the VM for specific requirements (REQUIRED)
                try:
                    rc = check_vm_requirements(host, user, si[1]['name'])
                    if rc != 0:
                        return_code = rc
                except InternalProcessException:
                    return_code = 19
                    pass
            except (BaseException, InternalProcessException, openstack.cloud.OpenStackCloudException):
                pass
            finally:
                delete_vm(conn)
    except (BaseException, InternalProcessException, openstack.cloud.OpenStackCloudException):
        pass
    finally:
        clean_environment(conn)

    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
