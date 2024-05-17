import argparse
import getpass
import os
import typing

import openstack

CORE_ROLES = {
    "member",
    "admin",
    "service"
}

# The dict index key here equals the corresponding endpoint type as per
# Keystone's service catalog. Those roles will only be checked if that
# endpoint type is registered.
# Denoted by a colon, optionally the service name can also be matched against.
SERVICE_ROLES = {
    "load-balancer": {
        "load-balancer_observer",
        "load-balancer_global_observer",
        "load-balancer_member",
        "load-balancer_quota_admin",
        "load-balancer_admin ",
    },
    "identity": {
        "manager",
    },
    "key-manager": {
        "key-manager:service-admin",
        "creator",
        "observer",
        "audit",
    },
    "object-store:swift": {
        "ResellerAdmin",
    },
    "orchestration:heat": {
        "heat_stack_user",
    }
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


def reconnect_with_role(conn: openstack.connection.Connection,
                        target_role_name: str
                        ) -> openstack.connection.Connection:
    """
    Uses the existing cloud connection to create a new application credential
    in the Identity API limited to the role specified via target_role_name.
    Creates a new cloud connection using the application credential and
    returns it, effectively scoping the returned connection to the specific
    role.
    """
    credential_name = f"scs-{target_role_name}-role-credential"
    existing_credential = conn.identity.find_application_credential(
        conn.current_user_id,
        credential_name
    )
    if existing_credential:
        conn.identity.delete_application_credential(
            conn.current_user_id,
            existing_credential
        )
    app_credential = conn.identity.create_application_credential(
        conn.current_user_id,
        credential_name,
        roles=[{"name": target_role_name}]
    )

    # Open a new connection using the application credential
    new_conn = openstack.connect(
        region_name=conn.config.config["region"],
        auth_type="v3applicationcredential",
        auth={
            "auth_url": conn.auth["auth_url"],
            "application_credential_id": app_credential.id,
            "application_credential_secret": app_credential.secret,
        },
    )

    return new_conn


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


def check_key_manager_permissions(conn: openstack.connection.Connection
                                  ) -> None:
    """
    Limits the authentication to the "member" role using an application
    credentials restricted to that role and verifies that the member role
    has sufficient access to the Key Manager API functionality.
    """
    secret_name = "scs-member-role-test-secret"
    member_conn = reconnect_with_role(conn, "member")

    def _find_secret(secret_name_or_id: str):
        """Replacement method for finding secrets.

        Mimicks the behavior of Connection.key_manager.find_secret()
        but fixes an issue with the internal implementation raising an
        exception due to an unexpected microversion parameter.
        """
        secrets = member_conn.key_manager.secrets()
        for s in secrets:
            if s.name == secret_name_or_id or s.id == secret_name_or_id:
                return s
        return None

    try:
        existing_secret = _find_secret(secret_name)
        if existing_secret:
            member_conn.key_manager.delete_secret(existing_secret)

        member_conn.key_manager.create_secret(
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
        member_conn.key_manager.delete_secret(new_secret)
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
    service_catalog = [
        (svc.get("type"), svc.get("name")) for svc in conn.service_catalog
    ]

    check_list_of_roles(conn, CORE_ROLES)
    for service_identifier in SERVICE_ROLES:
        if ":" in service_identifier:
            # match both service type and service name
            svc_type, svc_name = service_identifier.split(":", 1)
            if (svc_type, svc_name) not in service_catalog:
                # if the service is not present, do not check its roles
                continue
        else:
            # match only service type
            if service_identifier not in [svc[0] for svc in service_catalog]:
                # if the service is not present, do not check its roles
                continue
        print(f"INFO: service '{service_identifier}' is present and its "
              f"roles will be checked ...")
        check_list_of_roles(conn, SERVICE_ROLES[service_identifier])

    check_key_manager_permissions(conn)


if __name__ == "__main__":
    main()
