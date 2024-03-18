"""Default Security Group Rules Checker

This script tests the absence of any ingress default security group rule.
"""

import openstack
import os
import yaml
import argparse
import keystoneauth1


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
	egress_rules = 0
	if not rules:
		print("No default security group rules defined.")
	else:
		for rule in rules:
			if rule.direction == "ingress":
				ingress_rules += 1
			elif rule.direction == "egress":
				egress_rules += 1

	# test whether there are no ingress_rules allowed
	assert ingress_rules == 0, (
		f"expected 0 default ingress rules, "
	    f"but there are {ingress_rules}")

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
