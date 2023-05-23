#!/usr/bin/env python3
"""
Check given cloud for conformance with SCS standard regarding
entropy, to be found under /Standards/scs-0101-v1-entropy.md
"""
import errno
import getopt
import os
import sys
import time

import openstack
import fabric


def print_usage(file=sys.stderr):
    """help output"""
    print("""Usage: entropy-check.py [options]
Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD
 and checks for the presence of the mandatory SCS flavors (read from mand.yaml)
 and reports inconsistencies, errors etc. It returns 0 on success.
""", end='', file=file)


def get_kernel_version(kernel):
    nv = kernel.split(" ")[1]
    nvd = nv.split("-")
    _v = nvd[0].split(".")

    version = {
        'major': int(_v[0]),
        'minor': int(_v[1]),
        'patch': int(_v[2]),
        'pre-release': int(nvd[1])
    }
    return version


def print_results(results, theme):
    print(f"{theme}")
    for key, value in results.items():
        print(f"{key}")
        for k, v in value.items():
            if v:
                if k in ["version", "rng_available"]:
                    print(f"    - {k} {v}")
                else:
                    print(f"    \33[32m- {k} ✓\33[0m")
            else:
                print(f"    \33[31m- {k} ×\33[0m")


def test_vm(server_image):
    # We need to sleep here, to get the server completely up
    time.sleep(30)

    host = server_image[0]['public_v4']
    user = server_image[1]['properties']['standarduser']
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})
        kernel_version = fconn.run('uname -smr', hide=True).stdout
    except Exception as e:
        raise e

    return kernel_version


def test_flavors(conn):
    flavor_list = dict()
    list_to_test = ("hw_rng:allowed", "hw_rng:rate_bytes", "hw_rng:rate_period")
    for flavor in conn.compute.flavors():
        flavor_info = conn.compute.get_flavor(flavor['id'], get_extra_specs=True)
        flavor_info = flavor_info.to_dict()
        flavor_dict = dict()
        for k, v in flavor_info['extra_specs'].items():
            for ltt in list_to_test:
                if k == ltt and (v is not False or v is not None):
                    flavor_dict[ltt] = True
                else:
                    flavor_dict[ltt] = False
        flavor_list[flavor_info['name']] = flavor_dict
    print_results(flavor_list, "Flavors")


def test_images(conn):
    image_list = dict()
    for image in conn.image.images():
        image_info = conn.image.get_image(image['id'])
        image_info = image_info.to_dict()
        if image_info['hw_rng_model'] is not None:
            image_list[image_info['name']] = {"hw_rng_model": True}
        else:
            image_list[image_info['name']] = {"hw_rng_model": False}
    print_results(image_list, "Images")


def test_services(server_image):
    service_list = dict()

    host = server_image[0]['public_v4']
    user = server_image[1]['properties']['standarduser']
    try:
        fconn = fabric.Connection(host=host, user=user, connect_kwargs={"key_filename": "./key.priv"})

        service_list['kernel'] = dict()
        try:
            service_list['kernel']['version'] = fconn.run('uname -smr', hide=True).stdout.replace("\n", "")
        except BaseException:
            service_list['kernel']['version'] = False

        service_list['haveged'] = dict()
        try:
            service_list['haveged']['status'] = fconn.run('sudo systemctl status haveged', hide=True).stdout
        except BaseException:
            service_list['haveged']['status'] = False

        service_list['rng-tools'] = dict()
        try:
            service_list['rng-tools']['status'] = fconn.run('sudo systemctl status rng-tools', hide=True).stdout
        except BaseException:
            service_list['rng-tools']['status'] = False

        service_list['hw-random'] = dict()
        try:
            hwr = fconn.run('cat /sys/devices/virtual/misc/hw_random/rng_available', hide=True).stdout.replace("\n", "")
            service_list['hw-random']['rng_available'] = hwr
        except BaseException:
            service_list['hw-random']['rng_available'] = False
    except Exception as e:
        raise e

    print_results(service_list, "Services")


def test_routine(conn, server_image):
    kernel_version = test_vm(server_image)

    kernel_version = get_kernel_version(kernel_version)
    if (kernel_version['major'] == 5 and kernel_version['minor'] < 18) or \
       (kernel_version['major'] < 5):
        test_services(server_image)
        test_images(conn)
        test_flavors(conn)


def create_vm(conn):
    try:
        keypair = conn.compute.create_keypair(name='test')

        try:
            os.mkdir("./")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        with open('key.priv', 'w') as f:
            f.write("%s" % keypair.private_key)
            f.close()
        os.chmod('key.priv', 0o400)

        # ---------------------------------------------------------------------
        example_sec_group = conn.network.create_security_group(
            name='test-group'
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
        # ---------------------------------------------------------------------
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
        server = conn.create_server('test', image=image, flavor=flavor, key_name=keypair.name,
                                    security_groups=['test-group'], wait=True, auto_ip=True)
        return [server.to_dict(), image.to_dict()]
    except Exception as e:
        raise e


def delete_vm(conn):
    try:
        _ = conn.delete_server('test', wait=True)
    except BaseException:
        pass
    try:
        for sg in conn.network.security_groups():
            sg = sg.to_dict()
            if sg['name'] == "test-group":
                _ = conn.network.delete_security_group(sg['id'])
    except BaseException:
        pass
    try:
        fips = conn.list_floating_ips()
        for fip in fips:
            if fip.status == 'DOWN':
                _ = conn.delete_floating_ip(fip.id, retry=5)
    except BaseException:
        pass
    try:
        os.remove("./key.priv")
    except BaseException:
        pass
    try:
        _ = conn.compute.delete_keypair('test')
    except BaseException:
        pass


def main(argv):
    try:
        opts, args = getopt.gnu_getopt(argv, "c:h", ("os-cloud=", "help", ))
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
        # optionally also: print_usage()
        return 1

    conn = openstack.connect(cloud=cloud, timeout=32)
    try:
        si = create_vm(conn)
        test_routine(conn, si)
    except BaseException:
        pass
    finally:
        delete_vm(conn)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
