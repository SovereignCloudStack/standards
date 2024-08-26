#!/usr/bin/env python3
"""Entropy checker

Check given cloud for conformance with SCS standard regarding
entropy, to be found under /Standards/scs-0101-v1-entropy.md

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    WARNING   for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
from collections import Counter, defaultdict
import getopt
import logging
import os
import re
import sys
import time
import warnings

import openstack
import openstack.cloud


logger = logging.getLogger(__name__)

# prefix ephemeral resources with '_scs-' to rule out any confusion with important resources
# (this enables us to automatically dispose of any lingering resources should this script be killed)
NETWORK_NAME = "_scs-0101-net"
SUBNET_NAME = "_scs-0101-subnet"
ROUTER_NAME = "_scs-0101-router"
SERVER_NAME = "_scs-0101-server"
SECURITY_GROUP_NAME = "_scs-0101-group"
KEYPAIR_NAME = "_scs-0101-keypair"

IMAGE_ATTRIBUTES = {
    # https://docs.openstack.org/glance/2023.1/admin/useful-image-properties.html#image-property-keys-and-values
    # type: str
    "hw_rng_model": "virtio",
}
FLAVOR_ATTRIBUTES = {
    # https://docs.openstack.org/nova/2023.1/configuration/extra-specs.html#hw-rng
    # type: bool
    "hw_rng:allowed": "True",  # testing showed that it is indeed a string?
}
FLAVOR_OPTIONAL = ("hw_rng:rate_bytes", "hw_rng:rate_period")


# we need to set package source on Ubuntu, because the default is not fixed and can lead to Heisenbugs
SERVER_USERDATA_GENERIC = """
#cloud-config
# apt-placeholder
packages:
  - rng-tools5
runcmd:
  - echo '_scs-test-entropy-avail'; cat /proc/sys/kernel/random/entropy_avail
  - echo '_scs-test-fips-test'; cat /dev/random | rngtest -c 1000
  - echo '_scs-test-rngd'; sudo systemctl status rngd
  - echo '_scs-test-virtio-rng'; cat /sys/devices/virtual/misc/hw_random/rng_available; sudo /bin/sh -c 'od -vAn -N2 -tu2 < /dev/hwrng'
  - echo '_scs-test-end'
final_message: "_scs-test-end"
""".strip()
SERVER_USERDATA = {
    'ubuntu': SERVER_USERDATA_GENERIC.replace('# apt-placeholder', """apt:
  primary:
    - arches: [default]
      uri: http://az1.clouds.archive.ubuntu.com/ubuntu/
  security: []"""),
    'debian': SERVER_USERDATA_GENERIC.replace('# apt-placeholder', """apt:
  primary:
    - arches: [default]
      uri: https://mirror.plusserver.com/debian/debian/
  security: []"""),
}


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: entropy-check.py [options]
This tool checks the requested images and flavors according to the SCS Standard 0101 "Entropy".
Options:
 [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
 [-d/--debug] enables DEBUG logging channel
 [-i/--images IMAGE_LIST] sets images to be tested, separated by comma.
""", end='', file=file)


def check_image_attributes(images, attributes=IMAGE_ATTRIBUTES):
    candidates = [
        (image.name, [f"{key}={value}" for key, value in attributes.items() if image.get(key) != value])
        for image in images
    ]
    # drop those candidates that are fine
    offenders = [candidate for candidate in candidates if candidate[1]]
    for name, wrong in offenders:
        logger.warning(f"Image '{name}' missing recommended attributes: {', '.join(wrong)}")
    return not offenders


def check_flavor_attributes(flavors, attributes=FLAVOR_ATTRIBUTES, optional=FLAVOR_OPTIONAL):
    offenses = 0
    for flavor in flavors:
        extra_specs = flavor['extra_specs']
        wrong = [f"{key}={value}" for key, value in attributes.items() if extra_specs.get(key) != value]
        miss_opt = [key for key in optional if extra_specs.get(key) is None]
        if wrong:
            offenses += 1
            message = f"Flavor '{flavor.name}' missing recommended attributes: {', '.join(wrong)}"
            # only report missing optional attributes if recommended are missing as well
            # reasoning here is that these optional attributes are merely a hint for implementers
            # and if the recommended attributes are present, we assume that implementers have done their job already
            if miss_opt:
                message += f"; additionally, missing optional attributes: {', '.join(miss_opt)}"
            logger.warning(message)
    return not offenses


def check_entropy_avail(lines, image_name):
    entropy_avail = lines[0].strip()
    if entropy_avail != "256":
        logger.error(
            f"VM '{image_name}' didn't have a fixed amount of entropy available. "
            f"Expected 256, got {entropy_avail}."
        )
        return False
    return True


def check_rngd(lines, image_name):
    if "could not be found" in '\n'.join(lines):
        logger.warning(f"VM '{image_name}' doesn't provide the recommended service rngd")
        return False
    return True


def check_fips_test(lines, image_name):
    try:
        fips_data = '\n'.join(lines)
        failure_re = re.search(r'failures:\s\d+', fips_data, flags=re.MULTILINE)
        if failure_re:
            fips_failures = failure_re.string[failure_re.regs[0][0]:failure_re.regs[0][1]].split(" ")[1]
            if int(fips_failures) <= 3:
                return True  # this is the single 'successful' code path
            logger.error(
                f"VM '{image_name}' didn't pass the FIPS 140-2 testing. "
                f"Expected a maximum of 3 failures, got {fips_failures}."
            )
        else:
            logger.error(f"VM '{image_name}': failed to determine fips failures")
            logger.debug(f"stderr following:\n{fips_data}")
    except BaseException:
        logger.critical(f"Couldn't check VM '{image_name}' requirements", exc_info=True)
    return False  # any unsuccessful path should end up here


def check_virtio_rng(lines, image, flavor):
    try:
        # Check the existence of the HRNG -- can actually be skipped if the flavor
        # or the image doesn't have the corresponding attributes anyway!
        if image.hw_rng_model != "virtio" or flavor.extra_specs.get("hw_rng:allowed") != "True":
            logger.debug("Not looking for virtio-rng because required attributes are missing")
            return False
        # `cat` can fail with return code 1 if special file does not exist
        hw_device = lines[0]
        if not hw_device.strip() or "No such device" in lines[1]:
            logger.warning(f"VM '{image.name}' doesn't provide a hardware device.")
            return False
        return True
    except BaseException:
        logger.critical(f"Couldn't check VM '{image.name}' recommends", exc_info=True)


class TestEnvironment:
    def __init__(self, conn):
        self.conn = conn
        self.keypair = None
        self.keyfile = None
        self.network = None
        self.subnet = None
        self.router = None
        self.sec_group = None

    def prepare(self):
        try:
            # create network, subnet, router, connect everything
            self.network = self.conn.create_network(NETWORK_NAME)
            # Note: The IP range/cidr here needs to match the one in the pre_cloud.yaml
            # playbook calling cleanup.py
            self.subnet = self.conn.create_subnet(
                self.network.id,
                cidr="10.1.0.0/24",
                gateway_ip="10.1.0.1",
                enable_dhcp=True,
                allocation_pools=[{
                    "start": "10.1.0.100",
                    "end": "10.1.0.199",
                }],
                dns_nameservers=["9.9.9.9"],
                name=SUBNET_NAME,
            )
            external_networks = list(self.conn.network.networks(is_router_external=True))
            if not external_networks:
                raise RuntimeError("No external network found!")
            if len(external_networks) > 1:
                logger.debug(
                    "More than one external network found: "
                    + ', '.join([n.id for n in external_networks])  # noqa: W503
                )
            external_gateway_net_id = external_networks[0].id
            logger.debug(f"Using external network {external_gateway_net_id}.")
            self.router = self.conn.create_router(
                ROUTER_NAME, ext_gateway_net_id=external_gateway_net_id,
            )
            self.conn.add_router_interface(self.router, subnet_id=self.subnet.id)
        except BaseException:
            # if `prepare` doesn't go through, we want to revert to a clean state
            # (in my opinion, the user should only need to call `clean` when `prepare` goes through)
            self.clean()
            raise

    def clean(self):
        if self.router is not None:
            try:
                self.conn.remove_router_interface(self.router, subnet_id=self.subnet.id)
            except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
                logger.debug("Router interface couldn't be deleted.", exc_info=True)
            try:
                self.conn.delete_router(self.router.id)
            except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
                logger.debug(f"The router {self.router.id} couldn't be deleted.", exc_info=True)
            self.router = None

        if self.subnet is not None:
            try:
                self.conn.delete_subnet(self.subnet.id)
            except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
                logger.debug(f"The network {self.subnet.id} couldn't be deleted.", exc_info=True)
            self.subnet = None

        if self.network is not None:
            try:
                self.conn.delete_network(self.network.id)
            except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
                logger.debug(f"The network {self.network.name} couldn't be deleted.", exc_info=True)
            self.network = None

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clean()


def create_vm(conn, all_flavors, image, server_name=SERVER_NAME):
    # Pick a flavor matching the image
    flavors = [flv for flv in all_flavors if flv.ram >= image.min_ram]
    # if at all possible, prefer a flavor that provides hw_rng:allowed!
    flavors_hrng = [flv for flv in flavors if flv.extra_specs.get("hw_rng:allowed", "").lower() == "true"]
    if flavors_hrng:
        flavors = flavors_hrng
    elif flavors:
        logger.debug(f"Unable to pick flavor with hw_rng:allowed=true for image '{image.name}'")
    else:
        logger.critical(f"No flavor could be found for the image '{image.name}'")
        return

    # try to pick a frugal flavor
    flavor = min(flavors, key=lambda flv: flv.vcpus + flv.ram / 3.0 + flv.disk / 10.0)
    userdata = SERVER_USERDATA.get(image.os_distro, SERVER_USERDATA_GENERIC)
    logger.debug(f"Using userdata:\n{userdata}")
    volume_size = max(image.min_disk, 8)  # sometimes, the min_disk property is not set correctly
    # create a server with the image and the flavor as well as
    # the previously created keys and security group
    logger.debug(
        f"Creating instance of image '{image.name}' using flavor '{flavor.name}' and "
        f"{volume_size} GiB ephemeral boot volume"
    )
    server = conn.create_server(
        server_name, image=image, flavor=flavor, userdata=userdata, wait=True, timeout=500,
        boot_from_volume=True, terminate_volume=True, volume_size=volume_size,
    )
    logger.debug(f"Server '{server_name}' ('{server.id}') has been created")
    # next, do an explicit get_server because, beginning with version 3.2.0, the openstacksdk no longer
    # sets the interface attributes such as `public_v4`
    # I (mbuechse) consider this a bug in openstacksdk; it was introduced with
    # https://opendev.org/openstack/openstacksdk/commit/a8adbadf0c4cdf1539019177fb1be08e04d98e82
    # I also consider openstacksdk architecture with the Mixins etc. smelly to say the least
    return conn.get_server(server.id)


def delete_vm(conn, server_name=SERVER_NAME):
    logger.debug(f"Deleting server '{server_name}'")
    try:
        _ = conn.delete_server(server_name, delete_ips=True, timeout=300, wait=True)
    except openstack.cloud.OpenStackCloudException:
        logger.debug(f"The server '{server_name}' couldn't be deleted.", exc_info=True)


def retry(func, exc_type, timeouts=(8, 7, 15, 10, 20, 30, 60)):
    if isinstance(exc_type, str):
        exc_type = exc_type.split(',')
    timeout_iter = iter(timeouts)
    # do an initial sleep because func is known fail at first anyway
    time.sleep(next(timeout_iter))
    retries = 0
    while True:
        try:
            func()
        except Exception as e:
            retries += 1
            timeout = next(timeout_iter, None)
            if timeout is None or e.__class__.__name__ not in exc_type:
                raise
            logger.debug(f"Initiating retry in {timeout} s due to {e!r} during {func!r}")
            time.sleep(timeout)
        else:
            break
    if retries:
        logger.debug(f"Operation {func!r} successful after {retries} retries")


class CountingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        self.bylevel = Counter()

    def handle(self, record):
        self.bylevel[record.levelno] += 1


# the following functions are used to map any OpenStack Image to a pair of integers
# used for sorting the images according to fitness for our test
# - debian take precedence over ubuntu
# - higher versions take precedence over lower ones

# only list stable versions here
DEBIAN_CODENAMES = {
    "buster": 10,
    "bullseye": 11,
    "bookworm": 12,
}


def _deduce_sort_debian(os_version, debian_ver=re.compile(r"\d+\Z")):
    if debian_ver.match(os_version):
        return 2, int(os_version)
    return 2, DEBIAN_CODENAMES.get(os_version, 0)


def _deduce_sort_ubuntu(os_version, ubuntu_ver=re.compile(r"\d\d\.\d\d\Z")):
    if ubuntu_ver.match(os_version):
        return 1, int(os_version.replace(".", ""))
    return 1, 0


# map lower-case distro name to version deducing function
DISTROS = {
    "ubuntu": _deduce_sort_ubuntu,
    "debian": _deduce_sort_debian,
}


def _deduce_sort(img):
    # avoid private images here
    # (note that with SCS, public images MUST have os_distro and os_version, but we check nonetheless)
    if img.visibility != 'public' or not img.os_distro or not img.os_version:
        return 0, 0
    deducer = DISTROS.get(img.os_distro.strip().lower())
    if deducer is None:
        return 0, 0
    return deducer(img.os_version.strip().lower())


def select_deb_image(images):
    """From a list of OpenStack image objects, select a recent Debian derivative."""
    return max(images, key=_deduce_sort, default=None)


def print_result(check_id, passed):
    print(check_id + ": " + ('FAIL', 'PASS')[bool(passed)])


def evaluate_output(lines, image, flavor):
    section = None
    indent = 0
    collected = defaultdict(list)
    for line in lines:
        idx = line.find("_scs-test-")
        if idx != -1:
            section = line[idx + 10:].split()[0]
            if section == 'end':
                section = None
            indent = idx
            continue
        if section:
            collected[section].append(line[indent:])
    # virtio-rng is not an official test case according to testing notes,
    # but for some reason we check it nonetheless (call it informative)
    check_virtio_rng(collected['virtio-rng'], image, flavor)
    print_result('entropy-check-entropy-avail', check_entropy_avail(collected['entropy-avail'], image.name))
    print_result('entropy-check-rngd', check_rngd(collected['rngd'], image.name))
    print_result('entropy-check-fips-test', check_fips_test(collected['fips-test'], image.name))


def main(argv):
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    warnings.filterwarnings("ignore", "search_floating_ips")
    # count the number of log records per level (used for summary and return code)
    counting_handler = CountingHandler(level=logging.INFO)
    logger.addHandler(counting_handler)

    try:
        opts, args = getopt.gnu_getopt(argv, "c:i:hd", ["os-cloud=", "images=", "help", "debug"])
    except getopt.GetoptError as exc:
        logger.critical(f"{exc}")
        print_usage()
        return 1

    cloud = os.environ.get("OS_CLOUD")
    image_names = set()
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-i" or opt[0] == "--images":
            image_names.update([img.strip() for img in opt[1].split(',')])
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-d" or opt[0] == "--debug":
            logging.getLogger().setLevel(logging.DEBUG)

    if not cloud:
        logger.critical("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.")
        return 1

    try:
        logger.debug(f"Connecting to cloud '{cloud}'")
        with openstack.connect(cloud=cloud, timeout=32) as conn:
            all_images = conn.list_images()
            all_flavors = conn.list_flavors(get_extra=True)

            if image_names:
                # find images by the names given, BAIL out if some image is missing
                images = sorted([img for img in all_images if img.name in image_names], key=lambda img: img.name)
                names = [img.name for img in images]
                logger.debug(f"Selected images: {', '.join(names)}")
                missing_names = image_names - set(names)
                if missing_names:
                    logger.critical(f"Missing images: {', '.join(missing_names)}")
                    return 1
            else:
                images = [select_deb_image(all_images) or all_images[0]]
                logger.debug(f"Selected image: {images[0].name} ({images[0].id})")

            logger.debug("Checking images and flavors for recommended attributes")
            print_result('entropy-check-image-properties', check_image_attributes(all_images))
            print_result('entropy-check-flavor-properties', check_flavor_attributes(all_flavors))

            logger.debug("Checking dynamic instance properties")
            # Check a VM for services and requirements
            with TestEnvironment(conn):
                for image in images:
                    try:
                        # ugly: create the server inside the try-block because the call
                        # can be interrupted via Ctrl-C, and then the instance will be
                        # started without us knowing its id
                        server = create_vm(conn, all_flavors, image)
                        console = conn.compute.get_server_console_output(server)
                        while True:
                            if "Failed to run module scripts-user" in console['output']:
                                raise RuntimeError(f"Failed tests for {server.id}")
                            if "_scs-test-end" in console['output']:
                                break
                            time.sleep(1.0)
                            console = conn.compute.get_server_console_output(server)
                        evaluate_output(console['output'].splitlines(), image, server.flavor)
                    finally:
                        delete_vm(conn)
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)

    c = counting_handler.bylevel
    logger.debug(
        "Total critical / error / warning: "
        f"{c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.WARNING]}"
    )
    # include this one for backwards compatibility
    if not c[logging.CRITICAL]:
        print("entropy-check: " + ('PASS', 'FAIL')[min(1, c[logging.ERROR])])
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
