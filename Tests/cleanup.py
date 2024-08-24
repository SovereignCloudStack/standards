#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0

# taken from https://github.com/osism/testbed/blob/main/terraform/scripts/cleanup.py
# with minor adaptations:
#  - names really start with the prefix (e.g., PREFIX-net-X instead of net-PREFIX-X)
#  - collect the original functions inside the class Janitor
#  - provide command-line interface in addition to environment variables
#  - prefix log messages with channel (can be useful for counting errors)

import getopt
import logging
import os
import sys
import time

import openstack


logger = logging.getLogger(__name__)


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: cleanup.py [options]
This tool cleans the cloud environment CLOUD by removing any resources whose name start with PREFIX.
Options:
 [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
 [-i/--prefix PREFIX] sets prefix (default from PREFIX env)
""", end='', file=file)


class Janitor:
    def __init__(self, conn, prefix=""):
        self.conn = conn
        self.prefix = prefix

    def disconnect_routers(self):
        logger.debug("disconnect routers")
        routers = list(self.conn.network.routers())
        for router in routers:
            if not router.name.startswith(self.prefix):
                continue
            logger.info(router.name)
            ports = list(self.conn.network.ports(device_id=router.id))
            for port in ports:
                self.conn.network.remove_interface_from_router(router.id, port_id=port["id"])

    def cleanup_routers(self):
        logger.debug("clean up routers")
        routers = list(self.conn.network.routers())
        for router in routers:
            if not router.name.startswith(self.prefix):
                continue
            logger.info(router.name)
            self.conn.network.remove_gateway_from_router(router)
            self.conn.network.delete_router(router)

    def cleanup_networks(self):
        logger.debug("clean up networks")
        networks = list(self.conn.network.networks(shared=False))
        for network in networks:
            if not network.name.startswith(self.prefix):
                continue
            logger.info(network.name)
            self.conn.network.delete_network(network)

    def cleanup_subnets(self):
        logger.debug("clean up subnets")
        subnets = list(self.conn.network.subnets())
        for subnet in subnets:
            if not subnet.name.startswith(self.prefix):
                continue
            logger.info(subnet.name)
            self.conn.network.delete_subnet(subnet)

    def cleanup_ports(self):
        logger.debug("clean up ports")
        # FIXME: We can't filter for device_owner = '' unfortunately
        ports = list(self.conn.network.ports(status="DOWN"))
        for port in ports:
            if port.device_owner:
                continue
            # Filter for IP range 10.1.0.0/24
            found = False
            fixed_adrs = port.fixed_ips
            for fixed_adr in fixed_adrs:
                ip_addr = fixed_adr["ip_address"]
                if not ip_addr:
                    continue
                if ip_addr.startswith("10.1.0."):
                    found = True
                    continue
            if not found:
                continue
            logger.info(port.id)
            self.conn.network.delete_port(port)

    def cleanup_volumes(self):
        logger.debug("clean up volumes")
        volumes = list(self.conn.block_storage.volumes())
        for volume in volumes:
            if not volume.name.startswith(self.prefix):
                continue
            logger.info(volume.name)
            self.conn.block_storage.delete_volume(volume)

    def cleanup_servers(self):
        logger.debug("clean up servers")
        # nova supports regex filtering
        servers = list(self.conn.compute.servers(name=f"^{self.prefix}"))
        for server in servers:
            if not server.name.startswith(self.prefix):
                continue

            logger.info(server.name)
            try:
                self.conn.compute.delete_server(server, force=True)
            except openstack.exceptions.HttpException:
                self.conn.compute.delete_server(server)

    def wait_servers_gone(self):
        logger.debug("wait for servers to be gone")
        count = 0
        found = []
        while count < 100:
            del found[:]
            # nova supports regex filtering
            servers = list(self.conn.compute.servers(name=f"^{self.prefix}"))
            for server in servers:
                if server.name.startswith(self.prefix):
                    found.append(server.name)
            if not found:
                break
            count += 1
            time.sleep(2)

        if count >= 100:
            logger.error("timeout waiting for servers to vanish: %s" % found)

    def cleanup_keypairs(self):
        logger.debug("clean up keypairs")
        keypairs = list(self.conn.compute.keypairs())
        for keypair in keypairs:
            if not keypair.name.startswith(self.prefix):
                continue
            logger.info(keypair.name)
            self.conn.compute.delete_keypair(keypair)

    def cleanup_security_groups(self):
        logger.debug("clean up security groups")
        for security_group in self.conn.network.security_groups():
            if not security_group.name.startswith(self.prefix):
                continue
            logger.info(security_group.name)
            self.conn.network.delete_security_group(security_group)

    def cleanup_floating_ips(self):
        # Note: FIPs have no name, so we might clean up unrelated
        #  currently unused FIPs here.
        logger.debug("clean up floating ips")
        floating_ips = list(self.conn.search_floating_ips())
        for floating_ip in floating_ips:
            if floating_ip["port_id"]:
                continue
            logger.info(floating_ip.floating_ip_address)
            self.conn.delete_floating_ip(floating_ip.id)

    def cleanup(self):
        self.cleanup_servers()
        self.cleanup_keypairs()
        self.wait_servers_gone()
        self.cleanup_ports()
        self.cleanup_volumes()
        self.disconnect_routers()
        self.cleanup_subnets()
        self.cleanup_networks()
        self.cleanup_security_groups()
        self.cleanup_floating_ips()
        self.cleanup_routers()


def main(argv):
    logging.basicConfig(
        format='%(levelname)s: [%(asctime)s] %(message)s',
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    prefix = os.environ.get("PREFIX", None)
    cloud = os.environ.get("OS_CLOUD")

    try:
        opts, args = getopt.gnu_getopt(argv, "c:p:h", ["os-cloud=", "prefix=", "help"])
    except getopt.GetoptError as exc:
        logger.critical(f"{exc}")
        print_usage()
        return 1

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-p" or opt[0] == "--prefix":
            prefix = opt[1]
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]

    if prefix is None:
        # check for None, because supplying --prefix '' shall be permitted
        logger.critical("You need to have PREFIX set or pass --prefix=PREFIX.")
        return 1

    if not cloud:
        logger.critical("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.")
        return 1

    with openstack.connect(cloud=cloud) as conn:
        Janitor(conn, prefix).cleanup()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        logger.critical(repr(exc))
        sys.exit(1)
