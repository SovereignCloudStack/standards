import logging

import openstack
from openstack.exceptions import ResourceNotFound


logger = logging.getLogger(__name__)

SG_NAME = "scs-test-default-sg"
DESCRIPTION = "scs-test-default-sg"


def check_default_rules(rules, short=False):
    """
    counts all verall ingress rules and egress rules, depending on the requested testing mode

    :param bool short
        if short is True, the testing mode is set on short for older OpenStack versions
    """
    ingress_rules = egress_rules = 0
    egress_vars = {'IPv4': {}, 'IPv6': {}}
    for key, value in egress_vars.items():
        value['default'] = 0
        if not short:
            value['custom'] = 0
    if not rules:
        logger.info("No default security group rules defined.")
    for rule in rules:
        direction = rule["direction"]
        ethertype = rule["ethertype"]
        if direction == "ingress":
            if not short:
                # we allow ingress from the same security group
                # but only for the default security group
                if rule.remote_group_id == "PARENT" and not rule["used_in_non_default_sg"]:
                    continue
            ingress_rules += 1
        elif direction == "egress" and ethertype in egress_vars:
            egress_rules += 1
            if short:
                egress_vars[ethertype]['default'] += 1
                continue
            if rule.remote_ip_prefix:
                # this rule does not allow traffic to all external ips
                continue
            # note: these two are not mutually exclusive
            if rule["used_in_default_sg"]:
                egress_vars[ethertype]['default'] += 1
            if rule["used_in_non_default_sg"]:
                egress_vars[ethertype]['custom'] += 1
    # test whether there are no unallowed ingress rules
    if ingress_rules:
        logger.error(f"Expected no default ingress rules, found {ingress_rules}.")
    # test whether all expected egress rules are present
    missing = [(key, key2) for key, val in egress_vars.items() for key2, val2 in val.items() if not val2]
    if missing:
        logger.error(
            "Expected rules for egress for IPv4 and IPv6 both for default and custom security groups. "
            f"Missing rule types: {', '.join(str(x) for x in missing)}"
        )
    logger.info(str({
        "Unallowed Ingress Rules": ingress_rules,
        "Egress Rules": egress_rules,
    }))
    return not ingress_rules and not missing


def create_security_group(conn, sg_name: str = SG_NAME, description: str = DESCRIPTION):
    """Create security group in openstack

    :returns:
        ~openstack.network.v2.security_group.SecurityGroup: The new security group or None
    """
    sg = conn.network.create_security_group(name=sg_name, description=description)
    return sg.id


def delete_security_group(conn, sg_id):
    conn.network.delete_security_group(sg_id)
    # in case of a successful delete finding the sg will throw an exception
    try:
        conn.network.find_security_group(name_or_id=sg_id)
    except ResourceNotFound:
        logger.debug(f"Security group {sg_id} was deleted successfully.")
    except Exception:
        logger.critical(f"Security group {sg_id} was not deleted successfully")
        raise


def altern_test_rules(connection: openstack.connection.Connection):
    sg_id = create_security_group(connection)
    try:
        sg = connection.network.find_security_group(name_or_id=sg_id)
        return check_default_rules(sg.security_group_rules, short=True)
    finally:
        delete_security_group(connection, sg_id)


def compute_scs_0115_default_rules(conn: openstack.connection.Connection) -> bool:
    """
    This test checks the absence of any ingress default security group rule
    except for ingress rules from the same security group. Furthermore the
    presence of default rules for egress traffic is checked.
    """
    try:
        rules = list(conn.network.default_security_group_rules())
    except (ResourceNotFound, AttributeError) as exc:
        # older versions of OpenStack don't have the endpoint and give ResourceNotFound
        if isinstance(exc, ResourceNotFound) and 'default-security-group-rules' not in str(exc):
            raise
        # why we see the AttributeError in some environments is a mystery
        if isinstance(exc, AttributeError) and 'default_security_group_rules' not in str(exc):
            raise
        logger.info(
            "API call failed. OpenStack components might not be up to date. "
            "Falling back to old-style test method. "
        )
        return altern_test_rules(conn)
    else:
        return check_default_rules(rules)
