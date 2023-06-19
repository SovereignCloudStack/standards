#!/usr/bin/env python3
"""Entropy checker

Check given cloud for conformance with SCS standard regarding
entropy, to be found under /Standards/scs-0101-v1-entropy.md

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    INFO      for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
from collections import Counter
import getopt
import logging
import os
import re
import sys
import tempfile
import time
import warnings

import fabric
import openstack
import openstack.cloud


logger = logging.getLogger(__name__)

# use telling names here, maybe even reuse the security group in case of a leak?
SERVER_NAME = "scs-0101-server"
SECURITY_GROUP_NAME = "scs-0101-group"
KEYPAIR_NAME = "scs-0101-keypair"

IMAGE_ATTRIBUTES = {
    # https://docs.openstack.org/glance/latest/admin/useful-image-properties.html#image-property-keys-and-values
    # type: str
    "hw_rng_model": "virtio",
}
FLAVOR_ATTRIBUTES = {
    # https://docs.openstack.org/nova/latest/configuration/extra-specs.html#hw-rng
    # type: bool
    "hw_rng:allowed": True,
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
    for image in images:
        wrong = [f"{key}={value}" for key, value in attributes.items() if image.get(key) != value]
        if wrong:
            logger.info(f"Image '{image.name}' missing recommended attributes: {', '.join(wrong)}")


def check_flavor_attributes(flavors, attributes=FLAVOR_ATTRIBUTES):
    for flavor in flavors:
        extra_specs = flavor['extra_specs']
        wrong = [f"{key}={value}" for key, value in attributes.items() if extra_specs.get(key) != value]
        if wrong:
            logger.info(f"Flavor '{flavor.name}' missing recommended attributes: {', '.join(wrong)}")


def check_vm_requirements(fconn, image_name):
    try:
        entropy_avail = fconn.run('cat /proc/sys/kernel/random/entropy_avail', hide=True).stdout.strip()
        # use ; instead of && to chain commands here because the installation via apt-get
        # can fail for mysterious reasons (such as, and I kid you not,
        #    Problem executing scripts APT::Update::Post-Invoke-Success
        # ) without actually blocking us from running the command
        # FIXME the following won't work with CentOS etc.
        fips_data = fconn.run(
            'sudo apt-get update > /dev/null ; '
            'sudo apt-get install -y rng-tools > /dev/null ; '
            'cat /dev/random | rngtest -c 1000',
            hide=True, warn=True,
        ).stderr

        if entropy_avail != "256":
            logger.error(
                f"VM '{image_name}' didn't have a fixed amount of entropy available. "
                f"Expected 256, got {entropy_avail}."
            )

        failure_re = re.search(r'failures:\s\d+', fips_data, flags=re.MULTILINE)
        if failure_re:
            fips_failures = failure_re.string[failure_re.regs[0][0]:failure_re.regs[0][1]].split(" ")[1]
            if int(fips_failures) > 3:
                logger.error(
                    f"VM '{image_name}' didn't pass the FIPS 140-2 testing. "
                    f"Expected a maximum of 3 failures, got {fips_failures}."
                )
        else:
            logger.error(f"VM '{image_name}': failed to determine fips failures")
            logger.debug(f"stderr following:\n{fips_data}")
    except BaseException:
        logger.critical(f"Couldn't check VM '{image_name}' requirements", exc_info=True)


def check_vm_recommends(fconn, image, flavor):
    try:
        result = fconn.run('sudo systemctl status rngd', hide=True, warn=True)
        if "could not be found" in result.stdout or "could not be found" in result.stderr:
            logger.info(f"VM '{image.name}' doesn't provide the recommended service rngd")
        # Check the existence of the HRNG -- can actually be skipped if the flavor
        # or the image doesn't have the corresponding attributes anyway!
        if image.hw_rng_model != "virtio" or not flavor.extra_specs.get("hw_rng:allowed"):
            logger.debug("Not looking for virtio-rng because required attributes are missing")
        else:
            # `cat` can fail with return code 1 if special file does not exist
            hw_device = fconn.run('cat /sys/devices/virtual/misc/hw_random/rng_available', hide=True, warn=True).stdout
            result = fconn.run("sudo su -c 'od -vAn -N2 -tu2 < /dev/hwrng'", hide=True, warn=True)
            if not hw_device.strip() or "No such device" in result.stdout or "No such " in result.stderr:
                logger.info(f"VM '{image.name}' doesn't provide a hardware device.")
    except BaseException:
        logger.critical(f"Couldn't check VM '{image.name}' recommends", exc_info=True)


class TestEnvironment:
    def __init__(self, conn):
        self.conn = conn
        self.keypair = None
        self.keyfile = None
        self.sec_group = None

    def prepare(self):
        # Create a keypair and save both parts for later usage
        self.keypair = self.conn.compute.create_keypair(name=KEYPAIR_NAME)

        self.keyfile = tempfile.NamedTemporaryFile()
        self.keyfile.write(self.keypair.private_key.encode("ascii"))
        self.keyfile.flush()

        # Create a new security group and give it some simple rules in order to access it via SSH
        self.sec_group = self.conn.network.create_security_group(
            name=SECURITY_GROUP_NAME
        )

        _ = self.conn.network.create_security_group_rule(
            security_group_id=self.sec_group.id,
            direction='ingress',
            remote_ip_prefix='0.0.0.0/0',
            protocol='icmp',
            port_range_max=None,
            port_range_min=None,
            ethertype='IPv4',
        )
        _ = self.conn.network.create_security_group_rule(
            security_group_id=self.sec_group.id,
            direction='ingress',
            remote_ip_prefix='0.0.0.0/0',
            protocol='tcp',
            port_range_max=22,
            port_range_min=22,
            ethertype='IPv4',
        )

    def clean(self):
        try:
            _ = self.conn.network.delete_security_group(self.sec_group)
        except (openstack.cloud.OpenStackCloudException, openstack.cloud.OpenStackCloudUnavailableFeature):
            logger.debug(f"The security group {self.sec_group.name} couldn't be deleted.", exc_info=True)

        self.keyfile.close()
        self.keyfile = None

        try:
            _ = self.conn.compute.delete_keypair(self.keypair)
        except openstack.cloud.OpenStackCloudException:
            logger.debug(f"The keypair '{self.keypair.name}' couldn't be deleted.")
        self.keypair = None

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clean()


def create_vm(env, all_flavors, image, server_name=SERVER_NAME):
    # Pick a flavor matching the image
    flavors = [flv for flv in all_flavors if flv.disk >= image.min_disk and flv.ram >= image.min_ram]
    # if at all possible, prefer a flavor that provides hw_rng:allowed!
    flavors_hrng = [flv for flv in flavors if flv.extra_specs.get("hw_rng:allowed")]
    if flavors_hrng:
        flavors = flavors_hrng
    elif flavors:
        logger.debug(f"Unable to pick flavor with hw_rng:allowed=True for image '{image.name}'")
    else:
        logger.critical(f"No flavor could be found for the image '{image.name}'")
        return

    # try to pick a frugal flavor
    flavor = min(flavors, key=lambda flv: flv.vcpus)
    # create a server with the image and the flavor as well as
    # the previously created keys and security group
    logger.debug(f"Creating instance of image '{image.name}' using flavor '{flavors[0].name}'")
    server = env.conn.create_server(
        server_name, image=image, flavor=flavor, key_name=env.keypair.name,
        security_groups=[env.sec_group.name], wait=True, timeout=300, auto_ip=True,
    )
    logger.debug(f"Server '{server_name}' ('{server.id}') has been created")
    return server


def delete_vm(conn, server_name=SERVER_NAME):
    logger.debug(f"Deleting server '{server_name}'")
    try:
        _ = conn.delete_server(server_name, delete_ips=True, timeout=300, wait=True)
    except openstack.cloud.OpenStackCloudException:
        logger.debug(f"The server '{server_name}' couldn't be deleted.")


def retry(func, exc_type, timeouts=(8, 7, 15, 10)):
    timeout_iter = iter(timeouts)
    # do an initial sleep because func is known fail at first anyway
    time.sleep(next(timeout_iter))
    while True:
        try:
            func()
        except Exception as e:
            timeout = next(timeout_iter, None)
            if timeout is None or e.__class__.__name__ != exc_type:
                raise
            # logger.debug(f"Caught {e!r} while {func!r}; waiting {timeout} s before retry")
            time.sleep(timeout)
        else:
            break


class CountingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        self.bylevel = Counter()

    def handle(self, record):
        self.bylevel[record.levelno] += 1


def main(argv):
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    logging.getLogger("fabric").propagate = False
    logging.getLogger("invoke").propagate = False
    logging.getLogger("paramiko").propagate = False
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
                images = all_images[:1]
                logger.debug(f"Selected image: {images[0].name}")

            logger.debug("Checking images and flavors for recommended attributes")
            check_image_attributes(all_images)
            check_flavor_attributes(all_flavors)

            logger.debug("Checking dynamic instance properties")
            with TestEnvironment(conn) as env:
                # Check a VM for services and requirements
                for image in images:
                    try:
                        # ugly: create the server inside the try-block because the call
                        # can be interrupted via Ctrl-C, and then the instance will be
                        # started without us knowing its id
                        server = create_vm(env, all_flavors, image)
                        with fabric.Connection(
                            host=server.public_v4,
                            user=image.properties['standarduser'],
                            connect_kwargs={"key_filename": env.keyfile.name},
                        ) as fconn:
                            # need to retry because it takes time for sshd to come up
                            retry(fconn.open, exc_type="NoValidConnectionsError")
                            check_vm_recommends(fconn, image, server.flavor)
                            check_vm_requirements(fconn, image.name)
                    finally:
                        delete_vm(conn)
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)

    c = counting_handler.bylevel
    logger.debug(f"Total critical / error / info: {c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.INFO]}")
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
