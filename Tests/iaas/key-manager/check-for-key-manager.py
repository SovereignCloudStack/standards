"""Mandatory APIs checker
This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether a key manager APi endpoint is present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
"""

import argparse
import json
import logging
import os

import openstack


logger = logging.getLogger(__name__)


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud
    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :returns: openstack.connnection.Connection
    """
    return openstack.connect(
        cloud=cloud_name,
    )


def check_for_member_role(conn: openstack.connection.Connection
                          ) -> None:
    """Checks whether the current user has at maximum privileges
    of the member role.
    :param connection:
        The current connection to an OpenStack cloud.
    :returns: boolean, when role with most priviledges is member
    """

    auth_data = conn.auth
    auth_dict = {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": auth_data['username'],
                    "domain": {"name": auth_data['project_domain_name']},
                    "password": auth_data['password']
                }
            },
        },
        "scope": {
            "project": {
                "domain": {"name": auth_data['project_domain_name']},
                "name": auth_data['project_name']
            }
        }
    }

    has_member_role = False
    request = conn.session.request(auth_data['auth_url'] + '/v3/auth/tokens',
                                   'POST',
                                   json={'auth': auth_dict})
    for role in json.loads(request.content)["token"]["roles"]:
        role_name = role["name"]
        if role_name == "admin" or role_name == "manager":
            return False
        elif role_name == "member":
            print("User has member role.")
            has_member_role = True
        elif role_name == "reader":
            print("User has reader role.")
        else:
            print("User has custom role.")
            return False
    return has_member_role


def check_presence_of_key_manager(cloud_name: str):
    try:
        connection = connect(cloud_name)
        services = connection.service_catalog
    except Exception as e:
        print(str(e))
        raise Exception(
            f"Connection to cloud '{cloud_name}' was not successfully. "
            f"The Catalog endpoint could not be accessed. "
            f"Please check your cloud connection and authorization."
        )

    for svc in services:
        svc_type = svc['type']
        if svc_type == "key-manager":
            # key-manager is present
            # now we want to check whether a user with member role
            # can create and access secrets
            check_key_manager_permissions(connection)
            return 0

    # we did not find the key-manager service
    logger.warning("There is no key-manager endpoint in the cloud.")
    # we do not fail, until a key-manager MUST be present
    return 0


def check_key_manager_permissions(conn: openstack.connection.Connection
                                  ) -> None:
    """
    After checking that the current user only has the member and maybe the
    reader role, this method verifies that the user with a member role
    has sufficient access to the Key Manager API functionality.
    """
    secret_name = "scs-member-role-test-secret"
    if not check_for_member_role(conn):
        logger.warning("Cannot test key-manager permissions. "
                       "User has wrong roles")
        return None

    def _find_secret(secret_name_or_id: str):
        """Replacement method for finding secrets.

        Mimicks the behavior of Connection.key_manager.find_secret()
        but fixes an issue with the internal implementation raising an
        exception due to an unexpected microversion parameter.
        """
        secrets = conn.key_manager.secrets()
        for s in secrets:
            if s.name == secret_name_or_id or s.id == secret_name_or_id:
                return s
        return None

    try:
        existing_secret = _find_secret(secret_name)
        if existing_secret:
            conn.key_manager.delete_secret(existing_secret)

        conn.key_manager.create_secret(
            name=secret_name,
            payload_content_type="text/plain",
            secret_type="opaque",
            payload="foo"
        )

        new_secret = _find_secret(secret_name)
        assert new_secret, (
            f"Secret created with name '{secret_name}' was not discoverable by "
            f"the user"
        )
        conn.key_manager.delete_secret(new_secret)
    except openstack.exceptions.ForbiddenException as e:
        print(
            "Users of the 'member' role can use Key Manager API: FAIL"
        )
        print(
            f"ERROR: {str(e)}"
        )
        exit(1)
    print(
        "Users of the 'member' role can use Key Manager API: PASS"
    )


def main():
    parser = argparse.ArgumentParser(
        description="SCS Mandatory IaaS Service Checker")
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

    return check_presence_of_key_manager(cloud)


if __name__ == "__main__":
    main()
