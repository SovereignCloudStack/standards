#!/usr/bin/env python3
"""Default Security Group Rules Checker

This script tests the absence of any ingress default security group rule
except for ingress rules from the same Security Group. Furthermore the
presence of default rules for egress traffic is checked.
"""
import argparse
from collections import Counter
import logging
import os
import sys

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
        check_default_rules(sg.security_group_rules, short=True)
    finally:
        delete_security_group(connection, sg_id)


def test_rules(connection: openstack.connection.Connection):
    try:
        rules = list(connection.network.default_security_group_rules())
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
        altern_test_rules(connection)
    else:
        check_default_rules(rules)


class CountingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        self.bylevel = Counter()

    def handle(self, record):
        self.bylevel[record.levelno] += 1


def main():
    parser = argparse.ArgumentParser(
        description="SCS Default Security Group Rules Checker",
    )
    parser.add_argument(
        "--os-cloud",
        type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging",
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=False)  # never leak sensitive data (enable this locally)
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    # count the number of log records per level (used for summary and return code)
    counting_handler = CountingHandler(level=logging.INFO)
    logger.addHandler(counting_handler)

    # parse cloud name for lookup in clouds.yaml
    cloud = args.os_cloud or os.environ.get("OS_CLOUD", None)
    if not cloud:
        raise ValueError(
            "You need to have the OS_CLOUD environment variable set to your cloud "
            "name or pass it via --os-cloud"
        )

    with openstack.connect(cloud) as conn:
        test_rules(conn)

    c = counting_handler.bylevel
    logger.debug(f"Total critical / error / warning: {c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.WARNING]}")
    if not c[logging.CRITICAL]:
        print("security-groups-default-rules-check: " + ('PASS', 'FAIL')[min(1, c[logging.ERROR])])
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        logging.debug("traceback", exc_info=True)
        logging.critical(str(exc))
        sys.exit(1)
