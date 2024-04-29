"""Networking API extension checker for DNS functionality

This script uses the OpenStack SDK to check conformance to the SCS standard
concerning DNS API extensions.
"""

import openstack
import os
import sys
import argparse


def connect(cloud_name: str,
            auth_overrides: dict = None) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :param dict auth_overrides:
        A dict that overrides option of the auth section of the cloud
        configuration of the loaded clouds.yaml. Allows to authenticate
        as a different user based on the same general cloud settings.
        Example:

            {
                "username": "claudia",
                "password": "foobar123!%",
                "project_name": "customer1"
            }

    :returns: openstack.connnection.Connection
    """

    if auth_overrides:
        return openstack.connect(
            cloud=cloud_name,
            auth=auth_overrides
        )
    else:
        return openstack.connect(
            cloud=cloud_name,
        )


def has_extension(conn: openstack.connection.Connection, name: str) -> bool:
    """Checks whether a given Networking API extension is present.

    Connects to the Extension API of the Networking API and checks if the
    extension given by `name` is present and in case it is returns True.
    Otherwise returns False.
    """
    ext = conn.network.find_extension(name, ignore_missing=True)
    if ext:
        # note that ext.name is a human-readable description, the name as
        # referenced in the standard is the ext.alias
        return ext.alias == name
    else:
        return False


def has_dns_api(conn: openstack.connection.Connection) -> bool:
    """Checks whether the OpenStack DNS API is offered by the connected cloud.

    Returns True if the DNS API is offered and False otherwise.
    """
    # "[...] the dns member of a Connection object [...]"
    # "[...] will only be added if the service is detected."
    # see https://docs.openstack.org/openstacksdk/latest/user/proxies/dns.html
    return hasattr(conn, "dns")


def main():
    parser = argparse.ArgumentParser(
        description="SCS Domain Manager Conformance Checker")
    parser.add_argument(
        "--os-cloud", type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable OpenStack SDK debug logging"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=args.debug)

    # parse cloud name for lookup in clouds.yaml
    cloud = os.environ.get("OS_CLOUD", None)
    if args.os_cloud:
        cloud = args.os_cloud
    assert cloud, (
        "You need to have the OS_CLOUD environment variable set to your cloud "
        "name or pass it via --os-cloud"
    )
    conn = connect(cloud)

    # bare minimum: dns-integration extension
    if has_extension(conn, "dns-integration"):
        print(
            "Networking API MUST offer 'dns-integration' extension: PASS"
        )
    else:
        print(
            "Networking API MUST offer 'dns-integration' extension: FAIL"
        )
        sys.exit(1)

    has_designate = has_dns_api(conn)
    print("Is DNS API present (OPTIONAL):", has_designate)

    if has_designate:
        if has_extension(conn, "dns-domain-ports"):
            print(
                "When the DNS API is present, the Networking API MUST offer "
                "the 'dns-domain-ports' extension: PASS"
            )
        else:
            print(
                "When the DNS API is present, the Networking API MUST offer "
                "the 'dns-domain-ports' extension: FAIL"
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
