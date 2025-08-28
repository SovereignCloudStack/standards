#!/usr/bin/env python3
import logging
import re
import time

import openstack


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


TIMEOUT = 5 * 60  # timeout in seconds after which we no longer wait for the VM to complete the run
MARKER = '_scs-test-'
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
# we need to set package source on Ubuntu, because the default is not fixed and can lead to Heisenbugs
SERVER_USERDATA = {
    'ubuntu': SERVER_USERDATA_GENERIC.replace('# apt-placeholder', """apt:
  primary:
    - arches: [default]
      uri: http://az1.clouds.archive.ubuntu.com/ubuntu/"""),
    'debian': SERVER_USERDATA_GENERIC.replace('# apt-placeholder', """apt:
  primary:
    - arches: [default]
      uri: https://mirror.plusserver.com/debian/debian/"""),
}


def compute_scs_0101_image_property(images, attributes=IMAGE_ATTRIBUTES):
    """This test ensures that each image has the relevant properties."""
    candidates = [
        (image.name, [f"{key}={value}" for key, value in attributes.items() if image.get(key) != value])
        for image in images
    ]
    # drop those candidates that are fine
    offenders = [candidate for candidate in candidates if candidate[1]]
    for name, wrong in offenders:
        logger.error(f"Image '{name}' missing recommended attributes: {', '.join(wrong)}")
    return not offenders


def compute_scs_0101_flavor_property(flavors, attributes=FLAVOR_ATTRIBUTES, optional=FLAVOR_OPTIONAL):
    """This test ensures that each flavor has the relevant extra_spec."""
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
            logger.error(message)
    return not offenses


def compute_scs_0101_entropy_avail(collected_vm_output, image_name):
    """This test ensures that the `entropy_avail` value is correct for a test VM."""
    lines = collected_vm_output['entropy-avail']
    entropy_avail = lines[0].strip()
    if entropy_avail != "256":
        logger.error(
            f"VM '{image_name}' didn't have a fixed amount of entropy available. "
            f"Expected 256, got {entropy_avail}."
        )
        return False
    return True


def compute_scs_0101_rngd(collected_vm_output, image_name):
    """This test ensures that the `rngd` service is running on a test VM."""
    lines = collected_vm_output['rngd']
    if "could not be found" in '\n'.join(lines):
        logger.error(f"VM '{image_name}' doesn't provide the recommended service rngd")
        return False
    return True


def compute_scs_0101_fips_test(collected_vm_output, image_name):
    """This test ensures that the 'fips test' via `rngtest` is passed on a test VM."""
    lines = collected_vm_output['fips-test']
    try:
        fips_data = '\n'.join(lines)
        failure_re = re.search(r'failures:\s\d+', fips_data, flags=re.MULTILINE)
        if failure_re:
            fips_failures = failure_re.string[failure_re.regs[0][0]:failure_re.regs[0][1]].split(" ")[1]
            if int(fips_failures) <= 3:
                return True  # strict test passed
            logger.info(
                f"VM '{image_name}' didn't pass the strict FIPS 140-2 testing. "
                f"Expected a maximum of 3 failures, got {fips_failures}."
            )
            if int(fips_failures) <= 5:
                return True  # lenient test passed
            logger.error(
                f"VM '{image_name}' didn't pass the FIPS 140-2 testing. "
                f"Expected a maximum of 5 failures, got {fips_failures}."
            )
        else:
            logger.error(f"VM '{image_name}': failed to determine fips failures")
            logger.debug(f"stderr following:\n{fips_data}")
    except BaseException:
        logger.critical(f"Couldn't check VM '{image_name}' requirements", exc_info=True)
    return False  # any unsuccessful path should end up here


# FIXME this is not actually being used AFAICT -- mbuechse
def compute_scs_0101_virtio_rng(collected_vm_output, image_name):
    """This test ensures that the virtualized rng device is value inside a test VM."""
    lines = collected_vm_output['virtio-rng']
    try:
        # `cat` can fail with return code 1 if special file does not exist
        hw_device = lines[0]
        if not hw_device.strip() or "No such device" in lines[1]:
            logger.error(f"VM '{image_name}' doesn't provide a hardware device.")
            return False
        return True
    except BaseException:
        logger.critical(f"Couldn't check VM '{image_name}' recommends", exc_info=True)


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


def select_flavor_for_image(all_flavors, image):
    # Pick a flavor matching the image
    flavors = [flv for flv in all_flavors if flv.ram >= image.min_ram]
    # if at all possible, prefer a flavor that provides hw_rng:allowed!
    flavors_hrng = [flv for flv in flavors if flv.extra_specs.get("hw_rng:allowed", "").lower() == "true"]
    if flavors_hrng:
        flavors = flavors_hrng
    elif flavors:
        logger.debug(f"Unable to pick flavor with hw_rng:allowed=true for image '{image.name}'")
    else:
        raise RuntimeError(f"No flavor could be found for the image '{image.name}'")

    # try to pick a frugal flavor
    return min(flavors, key=lambda flv: flv.vcpus + flv.ram / 3.0 + flv.disk / 10.0)


def create_vm(conn, flavor, image, network, userdata=None, server_name=SERVER_NAME):
    volume_size = max(image.min_disk, 8)  # sometimes, the min_disk property is not set correctly
    # create a server with the image and the flavor as well as
    # the previously created keys and security group
    logger.debug(
        f"Creating instance of image '{image.name}' using flavor '{flavor.name}' and "
        f"{volume_size} GiB ephemeral boot volume"
    )
    logger.debug(f"Using userdata:\n{userdata}")
    # explicitly set auto_ip=False, we may still get a (totally unnecessary) floating IP assigned
    server = conn.create_server(
        server_name, image=image, flavor=flavor, userdata=userdata, wait=True, timeout=500, auto_ip=False,
        boot_from_volume=True, terminate_volume=True, volume_size=volume_size, network=network,
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


# the following functions are used to map any OpenStack Image to a pair of integers
# used for sorting the images according to fitness for our test
# - debian take precedence over ubuntu
# - higher versions take precedence over lower ones

# only list stable versions here
DEBIAN_CODENAMES = {
    "buster": 10,
    "bullseye": 11,
    "bookworm": 12,
    "trixie": 13,
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
    if not img.os_distro or not img.os_version:
        return 0, 0
    deducer = DISTROS.get(img.os_distro.strip().lower())
    if deducer is None:
        return 0, 0
    return deducer(img.os_version.strip().lower())


def compute_canonical_image(all_images):
    """From a list of OpenStack image objects, select a recent Debian derivative."""
    return max(all_images, key=_deduce_sort, default=None)


def _convert_to_collected(lines, marker=MARKER):
    # parse lines from console output
    # removing any "indent", stuff that looks like '[   70.439502] cloud-init[513]: '
    section = None
    indent = 0
    collected = {}
    for line in lines:
        idx = line.find(marker)
        if idx != -1:
            section = line[idx + len(marker):].strip()
            if section == 'end':
                section = None
            indent = idx
            continue
        if section:
            collected.setdefault(section, []).append(line[indent:])
    return collected


def compute_collected_vm_output(conn, all_flavors, image):
    """Creates a test VM, collects and returns its output for later evaluation."""
    logger.debug(f"Selected image: {image.name} ({image.id})")
    flavor = select_flavor_for_image(all_flavors, image)
    userdata = SERVER_USERDATA.get(image.os_distro, SERVER_USERDATA_GENERIC)
    with TestEnvironment(conn) as env:
        try:
            # ugly: create the server inside the try-block because the call
            # can be interrupted via Ctrl-C, and then the instance will be
            # started without us knowing its id
            server = create_vm(env.conn, flavor, image, env.network, userdata)
            remainder = TIMEOUT
            console = conn.compute.get_server_console_output(server)
            while True:
                if "_scs-test-end" in console['output']:
                    break
                if remainder <= 0:
                    raise RuntimeError("timeout while waiting for VM to complete computation")
                if "Failed to run module scripts-user" in console['output']:
                    raise RuntimeError(f"Failed tests for {server.id}")
                time.sleep(1.0)
                remainder -= 1
                console = conn.compute.get_server_console_output(server)
            return _convert_to_collected(console['output'].splitlines())
        finally:
            delete_vm(conn)
