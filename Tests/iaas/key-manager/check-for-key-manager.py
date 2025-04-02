#!/usr/bin/env python3
"""Key Manager service checker for scs-0116-v1-key-manager-standard.md

This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether a key manager API endpoint is present.
It then checks whether a user with the maximum of a member role can create secrets.
This will only work after policy adjustments or with the new secure RBAC roles and policies.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
"""

import argparse
import logging
import os
import sys

import openstack

logger = logging.getLogger(__name__)


def initialize_logging():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


def check_for_member_role(conn: openstack.connection.Connection) -> None:
    """Checks whether the current user has at maximum privileges of the member role.

    :param conn: connection to an OpenStack cloud.
    :returns: boolean, when role with most privileges is member
    """
    role_names = set(conn.session.auth.get_access(conn.session).role_names)
    if role_names & {"admin", "manager"}:
        return False
    if "reader" in role_names:
        logger.info("User has reader role.")
    custom_roles = sorted(role_names - {"reader", "member"})
    if custom_roles:
        logger.info(f"User has custom roles {', '.join(custom_roles)}.")
    return "member" in role_names


def check_presence_of_key_manager(conn: openstack.connection.Connection) -> None:
    try:
        services = conn.service_catalog
    except Exception:
        logger.critical("Could not access Catalog endpoint.")
        raise

    for svc in services:
        svc_type = svc["type"]
        if svc_type == "key-manager":
            # key-manager is present
            # now we want to check whether a user with member role
            # can create and access secrets
            logger.info("Key Manager is present")
            return True


def _find_secret(conn: openstack.connection.Connection, secret_name_or_id: str):
    """Replacement method for finding secrets.

    Mimicks the behavior of Connection.key_manager.find_secret()
    but fixes an issue with the internal implementation raising an
    exception due to an unexpected microversion parameter.
    """
    secrets = conn.key_manager.secrets()
    return [ s for s in secrets if s.name == secret_name_or_id or s.id == secret_name_or_id ]

def check_key_manager_permissions(conn: openstack.connection.Connection) -> None:
    """
    After checking that the current user only has the member and maybe the
    reader role, this method verifies that the user with a member role
    has sufficient access to the Key Manager API functionality.
    """
    secret_name = "scs-member-role-test-secret"
    try:
        existing_secrets = _find_secret(conn, secret_name)
        for secret in existing_secrets:
            conn.key_manager.delete_secret(secret.id[secret.id.rfind('/')+1:])

        conn.key_manager.create_secret(
            name=secret_name,
            payload_content_type="text/plain",
            secret_type="opaque",
            payload="foo",
        )
        try:
            new_secret = _find_secret(conn, secret_name)
            if not new_secret:
                raise ValueError(f"Secret '{secret_name}' was not discoverable by the user")
        finally:
            conn.key_manager.delete_secret(new_secret)
    except openstack.exceptions.ForbiddenException:
        logger.debug('exception details', exc_info=True)
        logger.error(
            "Users with the 'member' role can use Key Manager API: FAIL"
        )
        return 1
    logger.info(
        "Users with the 'member' role can use Key Manager API: PASS"
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
    # @mbuechse: I think this is so much as to be unusable!
    # (If necessary, a developer can always uncomment)
    # openstack.enable_logging(debug=args.debug)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # parse cloud name for lookup in clouds.yaml
    cloud = args.os_cloud or os.environ.get("OS_CLOUD", None)
    if not cloud:
        logger.critical(
            "You need to have the OS_CLOUD environment variable set to your cloud "
            "name or pass it via --os-cloud"
        )
        return 2

    with openstack.connect(cloud=cloud) as conn:
        if not check_for_member_role(conn):
            logger.critical("Cannot test key-manager permissions. User has wrong roles")
            return 2
        if check_presence_of_key_manager(conn):
            return check_key_manager_permissions(conn)
        else:
            # not an error, because key manager is merely recommended
            logger.warning("There is no key-manager endpoint in the cloud.")


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except SystemExit as e:
        if e.code < 2:
            print("key-manager-check: " + ('PASS', 'FAIL')[min(1, e.code)])
        raise
    except BaseException:
        logger.critical("exception", exc_info=True)
        sys.exit(2)
