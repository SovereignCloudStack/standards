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
import json
import logging
import os

import openstack
from keystoneauth1.exceptions.http import Unauthorized

logger = logging.getLogger(__name__)

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def connect(cloud_name: str) -> openstack.connection.Connection:
    """
    Create a connection to an OpenStack cloud
    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :returns: openstack.connnection.Connection
    """
    return openstack.connect(
        cloud=cloud_name,
    )


def synth_auth_url(auth_url: str):
    """
    Synthesize URL for role request
    :param string auth_url:
        The authentification URL from clouds.yaml.
    :returns: URL for role request
    """
    if "/v3/" in auth_url:
        re_auth_url = auth_url + "auth/tokens"
    elif "/v3" in auth_url:
        re_auth_url = auth_url + "/auth/tokens"
    else:
        re_auth_url = auth_url + "/v3/auth/tokens"
    return re_auth_url


def check_for_member_role(
    conn: openstack.connection.Connection, cloud_name: str
) -> None:
    """Checks whether the current user has at maximum privileges
    of the member role.
    :param connection:
        The current connection to an OpenStack cloud.
    :returns: boolean, when role with most priviledges is member
    """
    auth_data = conn.auth
    token = conn.session.get_token()
    auth_url = synth_auth_url(auth_data["auth_url"])
    has_member_role = False
    try:
        # Make the POST request using the current session
        auth_payload = {
            "auth": {
                "identity": {"methods": ["token"], "token": {"id": token}},
                "scope": {
                    "project": {
                        "domain": {"name": conn.auth["project_domain_name"]},
                        "name": conn.auth["project_name"],
                    }
                },
            }
        }
        request = conn.session.request(
            url=auth_url,
            method="POST",
            json=auth_payload,  # The JSON payload for the request
            headers={"X-Auth-Token": token},  # Pass the token in the header
        )
    except Unauthorized as auth_err:
        print(f"Unauthorized scope (401): {auth_err}")

        # Make the POST request without special scope
        print("Make a new request without specifying the project domain")
        auth_payload = {
            "auth": {"identity": {"methods": ["token"], "token": {"id": token}}}
        }

        request = conn.session.request(
            url=auth_url,
            method="POST",
            json=auth_payload,
            headers={"X-Auth-Token": token},
        )
        print(f"Response Status new request: {request.status_code}")

    for role in json.loads(request.content)["token"]["roles"]:
        role_name = role["name"]
        if role_name == "admin" or role_name == "manager":
            return False
        elif role_name == "member":
            print(f"{GREEN}User has member role.{RESET}")
            has_member_role = True
        elif role_name == "reader":
            print("User has reader role.")
        else:
            print("User has custom role.")
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
        svc_type = svc["type"]
        if svc_type == "key-manager":
            # key-manager is present
            # now we want to check whether a user with member role
            # can create and access secrets
            print(f"{GREEN}Key-Manager is present{RESET}")
            check_key_manager_permissions(connection, cloud_name)
            return 0

    # we did not find the key-manager service
    logger.warning(f"{RED}There is no key-manager endpoint in the cloud.{RESET}")
    # we do not fail, until a key-manager MUST be present
    return 0


def check_key_manager_permissions(
    conn: openstack.connection.Connection, cloud_name
) -> None:
    """
    After checking that the current user only has the member and maybe the
    reader role, this method verifies that the user with a member role
    has sufficient access to the Key Manager API functionality.
    """
    secret_name = "scs-member-role-test-secret"
    if not check_for_member_role(conn, cloud_name):
        logger.warning("Cannot test key-manager permissions. " "User has wrong roles")
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
        assert new_secret, (
            f"Secret created with name '{secret_name}' was not discoverable by "
            f"the user"
        )
        conn.key_manager.delete_secret(new_secret)

    except openstack.exceptions.ForbiddenException as e:
        print(
            f"Users with the 'member' role can use Key Manager API: {RED}FAIL "
            f"- According to the Key Manager Standard, users with the "
            f"'member' role should be able to use the Key Manager API.{RESET}"
        )
        print(f"ERROR: {str(e)}")
        exit(1)
    print(
        f"Users with the 'member' role can use Key Manager API: {GREEN}PASS "
        f"- This is compliant to the Key Manager Standard.{RESET}"
    )


def main():
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
