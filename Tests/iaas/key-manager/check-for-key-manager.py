#!/usr/bin/env python3
"""Key Manager service checker
This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether a key manager API endpoint is present.
It then checks, whether a user with the maximum of a member role can create secrets.
This will only work after policy adjustments or with the new secure RBAC roles and policies.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
"""

import argparse
import logging
import os

import openstack

logger = logging.getLogger(__name__)


def initialize_logging():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)


def check_for_member_role(conn: openstack.connection.Connection) -> None:
    """Checks whether the current user has at maximum privileges
    of the member role.
    :param connection:
        The current connection to an OpenStack cloud.
    :returns: boolean, when role with most priviledges is member
    """
    role_names = set(conn.session.auth.get_access(conn.session).role_names)
    if role_names & {"admin", "manager"}:
        return False
    if "reader" in role_names:
        logger.info("User has reader role.")
    if role_names - {"reader", "member"}:
        logger.info("User has custom role.")
    return "member" in role_names


def check_presence_of_key_manager(conn: openstack.connection.Connection) -> None:
    try:
        services = conn.service_catalog
    except Exception as e:
        logger.error(str(e))
        raise Exception(
            "The Catalog endpoint could not be accessed. "
            "Please check your cloud connection and authorization."
        )

    for svc in services:
        svc_type = svc["type"]
        if svc_type == "key-manager":
            # key-manager is present
            # now we want to check whether a user with member role
            # can create and access secrets
            logger.info("Key-Manager is present")
            check_key_manager_permissions(conn)
            return

    # we did not find the key-manager service
    logger.warning("There is no key-manager endpoint in the cloud.")
    # we do not fail, until a key-manager MUST be present


def check_key_manager_permissions(conn: openstack.connection.Connection) -> None:
    """
    After checking that the current user only has the member and maybe the
    reader role, this method verifies that the user with a member role
    has sufficient access to the Key Manager API functionality.
    """
    secret_name = "scs-member-role-test-secret"
    if not check_for_member_role(conn):
        logger.warning("Cannot test key-manager permissions. User has wrong roles")
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
            payload="foo",
        )
        new_secret = _find_secret(secret_name)

        if not new_secret:
            raise ValueError(
                f"Secret created with name '{secret_name}' was not discoverable by the user"
            )
        conn.key_manager.delete_secret(new_secret)

    except openstack.exceptions.ForbiddenException as e:
        logger.info(
            "Users with the 'member' role can use Key Manager API: FAIL "
            "- According to the Key Manager Standard, users with the "
            "'member' role should be able to use the Key Manager API."
        )
        logger.error(f"ERROR: {str(e)}")
        exit(1)
    logger.info(
        "Users with the 'member' role can use Key Manager API: PASS "
        "- This is compliant to the Key Manager Standard."
    )


def main():
    initialize_logging()
    parser = argparse.ArgumentParser(description="SCS Mandatory IaaS Service Checker")
    parser.add_argument(
        "--os-cloud",
        type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable OpenStack SDK debug logging"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=args.debug)

    # parse cloud name for lookup in clouds.yaml
    cloud = args.os_cloud or os.environ.get("OS_CLOUD", None)
    if not cloud:
        raise RuntimeError(
            "You need to have the OS_CLOUD environment variable set to your cloud "
            "name or pass it via --os-cloud"
        )

    with openstack.connect(cloud=cloud) as conn:
        return check_presence_of_key_manager(conn)


if __name__ == "__main__":
    main()
