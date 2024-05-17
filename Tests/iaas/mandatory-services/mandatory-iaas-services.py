"""Mandatory APIs checker

This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether all mandatory APi endpoints, are present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
As the s3 endpoint might differ, a missing one will only result in a warning.
"""

import argparse
import getpass
import logging
import os

import openstack


logger = logging.getLogger(__name__)
mandatory_services = ["compute", "identity", "image", "block-storage",
                      "network", "load-balancer", "s3", "placement"]


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud
    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :returns: openstack.connnection.Connection
    """
    return openstack.connect(
        cloud=cloud_name,
    )


def check_presence_of_mandatory_services(cloud_name: str):
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
        if svc_type in mandatory_services:
            mandatory_services.remove(svc_type)

    if not mandatory_services:
        # every mandatory service API had an endpoint
        return 0
    else:
        # if only s3 is not available, that might be named differently
        if mandatory_services == ["s3"]:
            logger.warning("No s3 endpoint found.")
            return 0
        else:
            # there were multiple mandatory APIs not found
            logger.error(f"The following endpoints are missing: "
                         f"{mandatory_services}")
            return len(mandatory_services)


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

    return check_presence_of_mandatory_services(cloud)


if __name__ == "__main__":
    main()
