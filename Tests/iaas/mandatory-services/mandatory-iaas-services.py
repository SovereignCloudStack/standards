"""Mandatory APIs checker

This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether all mandatory APi endpoints, are present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
As the s3 endpoint might differ, a missing one will only result in a warning.
"""

import argparse
import logging
import os

import openstack


logger = logging.getLogger(__name__)
mandatory_services = ["compute", "identity", "image", "block-storage",
                      "network", "load-balancer", "placement",
                      "object-store"]
# object_store_service = ["s3", "object-store"]


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
            continue
        # the follwing code was used for mulitple object-store names
        # if svc_type in object_store_service:
        #     object_store_service.remove(svc_type)

    # if len(object_store_service) == 2:
        # neither s3 nor object-store is available,
        # but might be named differently
    #     logger.warning("No s3 or object-store endpoint found.")
    if not mandatory_services:
        # every mandatory service API had an endpoint
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
