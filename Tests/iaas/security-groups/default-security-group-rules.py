"""Default Security Group Rules Checker

This script tests the absence of any ingress default security group rule.
"""

import openstack
import os
import argparse


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :returns: openstack.connnection.Connection
    """
    return openstack.connect(
        cloud=cloud_name,
    )


def test_rules(cloud_name: str):
    try:
        connection = connect(cloud_name)
        rules = connection.network.default_security_group_rules()
    except Exception as e:
        print(str(e))
        raise Exception(
            f"Connection to cloud '{cloud_name}' was not successfully. "
            f"The default Security Group Rules could not be accessed. "
            f"Please check your cloud connection and authorization."
        )

    # count all overall ingress rules and egress rules.
    ingress_rules = 0
    ingress_from_same_sg = 0
    egress_rules = 0
    if not rules:
        print("No default security group rules defined.")
    else:
        for rule in rules:
            if rule.direction == "ingress":
                ingress_rules += 1
                # we allow ingress from the same security group
                # but only for the default security group
                if (rule.remote_group_id == "PARENT" and 
                  not rule.used_in_non_default_sg):
                    ingress_from_same_sg += 1
            elif rule.direction == "egress":
                egress_rules += 1

    # test whether there are no other than the allowed ingress rules
    assert ingress_rules == ingress_from_same_sg, (
        f"Expected only ingress rules for default security groups, "
        f"that allow ingress traffic from the same group. "
        f"But there are more - in total {ingress_rules} ingress rules. "
        f"There should be only {ingress_from_same_sg} ingress rules.")

    result_dict = {
        "Ingress Rules": ingress_rules,
        "Egress Rules": egress_rules
    }
    return result_dict


def main():
    parser = argparse.ArgumentParser(
        description="SCS Default Security Group Rules Checker")
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

    print(test_rules(cloud))


if __name__ == "__main__":
    main()
