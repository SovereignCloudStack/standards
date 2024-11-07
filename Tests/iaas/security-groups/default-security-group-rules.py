"""Default Security Group Rules Checker

This script tests the absence of any ingress default security group rule
except for ingress rules from the same Security Group. Furthermore the
presence of default rules for egress traffic is checked.
"""

import argparse
import os

import openstack
from openstack.exceptions import ResourceNotFound

SG_NAME = "default-test-sg"
DESCRIPTION = "default-test-sg"


def count_ingress_egress(rules, short=False):
    """
    counts all verall ingress rules and egress rules, depending on the requested testing mode
    :param object rules
    :param bool short
        if short is true, the testing mode is set on short for older os versions
    :returns:
      ingress_rules integer count
      egress_rules integer count
    """
    ingress_rules = 0
    egress_rules = 0
    egress_vars = {'IPv4': {}, 'IPv6': {}}
    for key, value in egress_vars.items():
        value['default'] = 0
        if not short:
            value['custom'] = 0
    if not rules:
        print("No default security group rules defined.")
    for rule in rules:
        direction = rule["direction"]
        ethertype = rule["ethertype"]
        if direction == "ingress":
            if not short:
                # we allow ingress from the same security group
                # but only for the default security group
                r_group_id = rule.remote_group_id
                if r_group_id == "PARENT" and not rule["used_in_non_default_sg"]:
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
        raise ValueError(
            f"Expected no default ingress rules for security groups, "
            f"But there are {ingress_rules} ingress rules. "
        )
    # test whether all expected egress rules are present
    missing = [(key, key2) for key, val in egress_vars.items() for key2, val2 in val.items() if not val2]
    if missing:
        raise ValueError(
            "Expected rules for egress for IPv4 and IPv6 "
            "both for default and custom security groups. "
            f"Missing rule types: {', '.join(str(x) for x in missing)}"
        )
    return {
        "Unallowed Ingress Rules": ingress_rules,
        "Egress Rules": egress_rules,
    }


def test_rules(connection: openstack.connection.Connection):
    rules = connection.network.default_security_group_rules()
    return count_ingress_egress(rules)


def create_security_group(conn, sg_name: str = SG_NAME, description: str = DESCRIPTION):
    """Create security group in openstack

    :param sec_group_name (str): Name of security group
    :param description (str): Description of security group

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
        print(f"Security group {sg_id} was deleted successfully.")
    except Exception as e:
        print(f"Security group {sg_id} was not deleted successfully" f"Exception: {e}")


def altern_test_rules(connection: openstack.connection.Connection):
    sg_id = create_security_group(connection)
    try:
        sg = connection.network.find_security_group(name_or_id=sg_id)
        return count_ingress_egress(sg.security_group_rules, True)
    finally:
        delete_security_group(connection, sg_id)


def main():
    parser = argparse.ArgumentParser(
        description="SCS Default Security Group Rules Checker"
    )
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
        raise ValueError(
            "You need to have the OS_CLOUD environment variable set to your cloud "
            "name or pass it via --os-cloud"
        )

    with openstack.connect(cloud) as conn:
        try:
            print(test_rules(conn))
        except ResourceNotFound as e:
            print(
                "Resource could not be found. OpenStack components might not be up to date. "
                "Falling back to old-style test method. "
                f"Error: {e}"
            )
            print(altern_test_rules(conn))
        except Exception as e:
            print(f"Error occured: {e}")
            raise


if __name__ == "__main__":
    main()
