"""Mandatory APIs checker
This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether a key manager APi endpoint is present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
"""

import argparse
import logging
import os

import openstack


logger = logging.getLogger(__name__)


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud
    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :returns: openstack.connnection.Connection
    """
    return openstack.connect(
        cloud=cloud_name,
    )


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
        svc_type = svc['type']
        if svc_type == "key-manager":
            # key-manager is present
            return 0

    # we did not find the key-manager service
    logger.warning("There is no key-manager endpoint in the cloud.")
    # we do not fail, until a key-manager MUST be present
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SCS Mandatory IaaS Service Checker")
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

    return check_presence_of_key_manager(cloud)


if __name__ == "__main__":
    main()
