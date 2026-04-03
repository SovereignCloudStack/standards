import argparse
import getpass
import os
import typing

import openstack

CORE_ROLES = {
    "reader",
    "member",
    "admin",
    "service"
}


def connect(cloud_name: str, password: typing.Optional[str] = None
            ) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :param string password:
        Optional password override for the connection.

    :returns: openstack.connnection.Connection
    """

    if password:
        return openstack.connect(
            cloud=cloud_name,
            password=password
        )
    else:
        return openstack.connect(
            cloud=cloud_name,
        )


def check_list_of_roles(conn: openstack.connection.Connection,
                        expected_roles: typing.Iterable[str]) -> None:
    """
    Retrieves the list of roles from the Identity API and verifies that
    it contains all role names specified in the given expected_roles list.
    """
    actual_roles = [role.name for role in conn.identity.roles()]
    for role in expected_roles:
        assert role in actual_roles, (
            f"Expected role '{role}' was not found."
        )
        print(f"Role '{role}' is present: PASS")


def main():
    parser = argparse.ArgumentParser(
        description="SCS Standard Roles Conformance Checker")
    parser.add_argument(
        "--os-cloud", type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable"
    )
    parser.add_argument(
        "--ask",
        help="Ask for password interactively instead of reading it from the "
        "clouds.yaml",
        action="store_true"
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
        "You need to have the OS_CLOUD environment variable set to your "
        "cloud name or pass it via --os-cloud"
    )
    conn = connect(
        cloud,
        password=getpass.getpass("Enter password: ") if args.ask else None
    )

    check_list_of_roles(conn, CORE_ROLES)


if __name__ == "__main__":
    main()
