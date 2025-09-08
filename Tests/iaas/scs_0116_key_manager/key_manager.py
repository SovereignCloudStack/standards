from collections import defaultdict
import logging

import openstack


logger = logging.getLogger(__name__)


def ensure_unprivileged(conn: openstack.connection.Connection) -> list:
    """
    Retrieves role names.
    Raises exception if elevated privileges (admin, manager) are present.
    Otherwise returns list of role names.

    :param conn: connection to an OpenStack cloud.
    :returns: list of role names
    """
    role_names = set(conn.session.auth.get_access(conn.session).role_names)
    if role_names & {"admin", "manager"}:
        raise RuntimeError("user privileges too high: admin/manager roles detected")
    if "reader" in role_names:
        logger.info("User has reader role.")
    custom_roles = sorted(role_names - {"reader", "member"})
    if custom_roles:
        logger.info(f"User has custom roles {', '.join(custom_roles)}.")
    return role_names


def compute_services_lookup(conn: openstack.connection.Connection) -> dict:
    try:
        services = conn.service_catalog
    except Exception:
        logger.critical("Could not access Catalog endpoint.")
        raise

    result = defaultdict(list)
    for svc in services:
        svc_type = svc["type"]
        result[svc_type].append(svc)
    return result


def compute_scs_0116_presence(services_lookup: dict) -> bool:
    """This test checks that a service of type key-manager is present."""
    services = services_lookup.get("key-manager", ())
    if not services:
        logger.error("key-manager service not found")
    return bool(services)


def _find_secrets(conn: openstack.connection.Connection, secret_name_or_id: str) -> list:
    """Replacement method for finding secrets.

    Mimicks the behavior of Connection.key_manager.find_secret()
    but fixes an issue with the internal implementation raising an
    exception due to an unexpected microversion parameter.
    Unlike find_secret(), we return a list with all secrets that match.
    """
    secrets = conn.key_manager.secrets()
    return [s for s in secrets if s.name == secret_name_or_id or s.id == secret_name_or_id]


def _delete_secret(conn: openstack.connection.Connection, secret: openstack.key_manager.v1.secret.Secret):
    """Replacement method for deleting secrets
    _delete_secret(connection, secret object)

    Workaround for SDK bugs:
     - The id field in reality is a href (containg the UUID at the end)
     - The delete_secret() function contrary to the documentation does
       not accept openstack.key_manager.v1.secret.Secret objects nor the
       hrefs, just plain UUIDs.
     - It does not return an error when I try to delete a secret passing
       an object or href, just silently does nothing.
    The code here assumes that the SDK (when fixed) will continue to
    accept UUIDs as argument for delete_secret() in the future.
    Code is robust against those being passed directly in the .id attr
    of the objects. (It would be even more robust to try to pass the
    object first, then the href, then the UUID extracted from the href,
    each time checking whether it was effective. But that's three delete
    plus list calls and very ugly.)
    """
    uuid = secret.id.rsplit('/', 1)[-1]
    conn.key_manager.delete_secret(uuid)


def compute_scs_0116_permissions(conn: openstack.connection.Connection, services_lookup) -> bool:
    """
    After checking that the current user is not privileged, this test verifies that the user has
    sufficient access to the Key Manager API functionality by creating and deleting a secret.
    """
    if "member" not in ensure_unprivileged(conn):
        raise RuntimeError("Cannot test key-manager permissions. User has wrong roles")
    if not services_lookup.get("key-manager", ()):
        # this testcase only applies when a key manager is present
        return True
    secret_name = "scs-member-role-test-secret"
    try:
        existing_secrets = _find_secrets(conn, secret_name)
        for secret in existing_secrets:
            _delete_secret(conn, secret)

        if existing_secrets:
            logger.debug(f'Deleted {len(existing_secrets)} secrets')

        conn.key_manager.create_secret(
            name=secret_name,
            payload_content_type="text/plain",
            secret_type="opaque",
            payload="foo",
        )
        try:
            new_secret = _find_secrets(conn, secret_name)
            if not new_secret:
                raise RuntimeError(f"Secret '{secret_name}' was not discoverable by the user")
        finally:
            _delete_secret(conn, new_secret[0])
    except (RuntimeError, openstack.exceptions.ForbiddenException):
        logger.debug('exception details', exc_info=True)
        logger.error("Unsuccessful at using Key Manager API")
        return False
    return True
