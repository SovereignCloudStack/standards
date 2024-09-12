"""Default Security Group Rules Checker

This script tests the absence of any ingress default security group rule
except for ingress rules from the same Security Group. Furthermore the
presence of default rules for egress traffic is checked.
"""

import openstack
import os
import argparse
import yaml
from openstack.exceptions import ResourceNotFound


###### debugging. TODO remove #####################
def load_env_from_yaml(cloudname):
    with open(".sandbox/clouds.yaml", "r+") as file:
        data = yaml.safe_load(file)
    for cloud in data["clouds"]:
        if cloud == cloudname:
            env = data["clouds"][cloud]
    return env


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :returns: openstack.connnection.Connection
    """
    env = load_env_from_yaml(cloud_name)

    return openstack.connect(
        cloud=cloud_name,
        auth_type=env["auth_type"],
        auth_url=env["auth_url"],
        project_name=env["project_name"],
        username=env["username"],
        password=env["password"],
        user_domain_name=env["user_domain_name"],
        project_domain_name=env["project_domain_name"],
    )


####################################################


def test_rules(cloud_name: str):
    try:
        connection = connect(cloud_name)
        print("test_rules")
        rules = connection.network.default_security_group_rules()
        print("After test_rules")
    except Exception as e:
        print("except test_rules")
        print(str(e))
        raise Exception(
            f"Connection to cloud '{cloud_name}' was not successful. "
            f"The default Security Group Rules could not be accessed. "
            f"Please check your cloud connection and authorization."
        )

    # count all overall ingress rules and egress rules.
    ingress_rules = 0
    ingress_from_same_sg = 0
    egress_rules = 0
    egress_ipv4_default_sg = 0
    egress_ipv4_custom_sg = 0
    egress_ipv6_default_sg = 0
    egress_ipv6_custom_sg = 0
    if not rules:
        print("No default security group rules defined.")
    else:
        for rule in rules:
            direction = rule["direction"]
            ethertype = rule["ethertype"]
            r_custom_sg = rule["used_in_non_default_sg"]
            r_default_sg = rule["used_in_default_sg"]
            r_custom_sg = rule.used_in_non_default_sg
            r_default_sg = rule.used_in_default_sg
            if direction == "ingress":
                ingress_rules += 1
                # we allow ingress from the same security group
                # but only for the default security group
                r_group_id = rule.remote_group_id
                if r_group_id == "PARENT" and not r_custom_sg:
                    ingress_from_same_sg += 1
            elif direction == "egress" and ethertype == "IPv4":
                egress_rules += 1
                if rule.remote_ip_prefix:
                    # this rule does not allow traffic to all external ips
                    continue
                if r_custom_sg:
                    egress_ipv4_custom_sg += 1
                if r_default_sg:
                    egress_ipv4_default_sg += 1
            elif direction == "egress" and ethertype == "IPv6":
                egress_rules += 1
                if rule.remote_ip_prefix:
                    # this rule does not allow traffic to all external ips
                    continue
                if r_custom_sg:
                    egress_ipv6_custom_sg += 1
                if r_default_sg:
                    egress_ipv6_default_sg += 1

    # test whether there are no other than the allowed ingress rules
    assert ingress_rules == ingress_from_same_sg, (
        f"Expected only ingress rules for default security groups, "
        f"that allow ingress traffic from the same group. "
        f"But there are more - in total {ingress_rules} ingress rules. "
        f"There should be only {ingress_from_same_sg} ingress rules."
    )
    assert (
        egress_rules > 0
    ), f"Expected to have more than {egress_rules} egress rules present."
    var_list = [
        egress_ipv4_default_sg,
        egress_ipv4_custom_sg,
        egress_ipv6_default_sg,
        egress_ipv6_custom_sg,
    ]
    assert all([var > 0 for var in var_list]), (
        "Not all expected egress rules are present. "
        "Expected rules for egress for IPv4 and IPv6 "
        "both for default and custom security groups."
    )

    result_dict = {"Ingress Rules": ingress_rules, "Egress Rules": egress_rules}
    return result_dict


def create_security_group(
    conn, sg_name: str = "default-test-sg", description: str = "default-test-sg"
):
    """Create security group in openstack

    Args:
        sec_group_name (str): Name of security group
        description (str): Description of security group

    Returns:
        ~openstack.network.v2.security_group.SecurityGroup: The new security group or None
    """
    sg = conn.network.create_security_group(name=sg_name, description=description)
    return sg.id


def delete_security_group(conn, sg_id):
    conn.network.delete_security_group(sg_id)
    print(f"security group {sg_id} deleted")


def altern_test_rules(cloud_name: str):
    try:
        connection = connect(cloud_name)
    except Exception as e:
        print(str(e))
        raise Exception(
            f"Connection to cloud '{cloud_name}' was not successful. "
            f"The default Security Group Rules could not be accessed. "
            f"Please check your cloud connection and authorization."
        )

    sg_id = create_security_group(connection)
    print(f"!!! created security group {sg_id}")
    rules = connection.network.find_security_group(name_or_id=sg_id)
    # rules = connection.network.security_group_rules()
    print(f"!! worked: altern_rules {type(rules)} {rules}")

    # count all overall ingress rules and egress rules.
    ingress_rules = 0
    ingress_from_same_sg = 0
    egress_rules = 0
    egress_ipv4_default_sg = 0
    egress_ipv4_custom_sg = 0
    egress_ipv6_default_sg = 0
    egress_ipv6_custom_sg = 0
    if not rules:
        print("No default security group rules defined.")
    else:
        for rule in rules.security_group_rules:
            print (f"#############{rule}")
            direction = rule['direction']
            ethertype = rule['ethertype']
            # r_custom_sg = rule['used_in_non_default_sg']
            # r_default_sg = rule['used_in_default_sg']
            # r_custom_sg = rule.used_in_non_default_sg
            # r_default_sg = rule.used_in_default_sg

            print(f"#############{direction}")
            print(f"#############{ethertype}")

            if direction == "ingress":
                ingress_rules += 1
                # we allow ingress from the same security group
                # but only for the default security group
                # r_group_id = rule.remote_group_id
                # if (r_group_id == "PARENT" and not r_custom_sg):
                #     ingress_from_same_sg += 1
            elif direction == "egress" and ethertype == "IPv4":
                egress_rules += 1
                # if rule.remote_ip_prefix:
                #     # this rule does not allow traffic to all external ips
                #     continue
                # if r_custom_sg:
                #     egress_ipv4_custom_sg += 1
                # if r_default_sg:
                #     egress_ipv4_default_sg += 1
            elif direction == "egress" and ethertype == "IPv6":
                egress_rules += 1
                # if rule.remote_ip_prefix:
                #     # this rule does not allow traffic to all external ips
                #     continue
                # if r_custom_sg:
                #     egress_ipv6_custom_sg += 1
                # if r_default_sg:
                #     egress_ipv6_default_sg += 1

    # test whether there are no other than the allowed ingress rules
    # assert ingress_rules == ingress_from_same_sg, (
    #     f"Expected only ingress rules for default security groups, "
    #     f"that allow ingress traffic from the same group. "
    #     f"But there are more - in total {ingress_rules} ingress rules. "
    #     f"There should be only {ingress_from_same_sg} ingress rules."
    # )
    assert (
        egress_rules > 0
    ), f"Expected to have more than {egress_rules} egress rules present."
    var_list = [
        egress_ipv4_default_sg,
        egress_ipv4_custom_sg,
        egress_ipv6_default_sg,
        egress_ipv6_custom_sg,
    ]
    assert all([var > 0 for var in var_list]), (
        "Not all expected egress rules are present. "
        "Expected rules for egress for IPv4 and IPv6 "
        "both for default and custom security groups."
    )


    delete_security_group(connection, sg_id)
    result_dict = {"Ingress Rules": ingress_rules, "Egress Rules": egress_rules}
    return result_dict


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
    cloud = os.environ.get("OS_CLOUD", None)
    if args.os_cloud:
        cloud = args.os_cloud
    assert cloud, (
        "You need to have the OS_CLOUD environment variable set to your cloud "
        "name or pass it via --os-cloud"
    )
    altern_test_rules(cloud)
    # try:
    #     print(test_rules(cloud))
    # except ResourceNotFound as e:
    #     print(
    #         "##### Ressource could not be found."
    #         f"Error: {e}"
    #         "Openstack components are not up to date and might soon be depricated!"
    #         f"{altern_test_rules(cloud)}"
    #     )
    # except Exception as e:
    #     print(f"Error occured: {e}")


if __name__ == "__main__":
    main()
