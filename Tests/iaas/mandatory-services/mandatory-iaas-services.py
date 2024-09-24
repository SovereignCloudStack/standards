"""Mandatory APIs checker
This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether all mandatory APi endpoints, are present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
As the s3 endpoint might differ, a missing one will only result in a warning.
"""

import argparse
import boto3
from collections import Counter
import logging
import os
import re
import sys
import uuid

import openstack


TESTCONTNAME = "scs-test-container"

logger = logging.getLogger(__name__)
mandatory_services = ["compute", "identity", "image", "network",
                      "load-balancer", "placement", "object-store"]
block_storage_service = ["volume", "volumev3", "block-storage"]


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
        if svc_type in block_storage_service:
            block_storage_service.remove(svc_type)

    bs_service_not_present = 0
    if len(block_storage_service) == 3:
        # neither block-storage nor volume nor volumev3 is present
        # we must assume, that there is no volume service
        logger.error("FAIL: No block-storage (volume) endpoint found.")
        mandatory_services.append(block_storage_service[0])
        bs_service_not_present = 1
    if not mandatory_services:
        # every mandatory service API had an endpoint
        return 0 + bs_service_not_present
    else:
        # there were multiple mandatory APIs not found
        logger.error(f"FAIL: The following endpoints are missing: "
                     f"{mandatory_services}")
        return len(mandatory_services) + bs_service_not_present


def list_containers(conn):
    "Gets a list of buckets"
    return [cont.name for cont in conn.object_store.containers()]


def create_container(conn, name):
    "Creates a test container"
    conn.object_store.create_container(name)
    return list_containers(conn)


def del_container(conn, name):
    "Deletes a test container"
    conn.object_store.delete(name)
    # return list_containers(conn)


def s3_conn(creds, conn=None):
    "Return an s3 client conn"
    vrfy = True
    cacert = conn.config.config.get("cacert")
    # TODO: Handle self-signed certs (from ca_cert in openstack config)
    if cacert:
        print("WARNING: Trust all Certificates in S3, "
              f"OpenStack uses {cacert}", file=sys.stderr)
        vrfy = False
    return boto3.resource('s3', aws_access_key_id=creds["AKI"],
                          aws_secret_access_key=creds["SAK"],
                          endpoint_url=creds["HOST"],
                          verify=vrfy)


def list_s3_buckets(s3):
    "Get a list of s3 buckets"
    return [buck.name for buck in s3.buckets.all()]


def create_bucket(s3, name):
    "Create an s3 bucket"
    # bucket = s3.Bucket(name)
    # bucket.create()
    s3.create_bucket(Bucket=name)
    return list_s3_buckets(s3)


def del_bucket(s3, name):
    "Delete an s3 bucket"
    buck = s3.Bucket(name=name)
    buck.delete()
    # s3.delete_bucket(Bucket=name)


def s3_from_env(creds, fieldnm, env, prefix=""):
    "Set creds[fieldnm] to os.environ[env] if set"
    if env in os.environ:
        creds[fieldnm] = prefix + os.environ[env]
    if fieldnm not in creds:
        print(f"WARNING: s3_creds[{fieldnm}] not set", file=sys.stderr)


def s3_from_ostack(creds, conn, endpoint):
    "Set creds from openstack swift/keystone"
    rgx = re.compile(r"^(https*://[^/]*)/")
    match = rgx.match(endpoint)
    if match:
        creds["HOST"] = match.group(1)
    # Use first ec2 cred if one exists
    ec2_creds = [cred for cred in conn.identity.credentials()
                 if cred.type == "ec2"]
    if len(ec2_creds):
        # FIXME: Assume cloud is not evil
        ec2_dict = eval(ec2_creds[0].blob, {"null": None})
        creds["AKI"] = ec2_dict["access"]
        creds["SAK"] = ec2_dict["secret"]
        return
    # Generate keyid and secret
    aki = uuid.uuid4().hex
    sak = uuid.uuid4().hex
    blob = f'{{"access": "{aki}", "secret": "{sak}"}}'
    try:
        conn.identity.create_credential(type="ec2", blob=blob,
                                        user_id=conn.current_user_id,
                                        project_id=conn.current_project_id)
        creds["AKI"] = aki
        creds["SAK"] = sak
    except BaseException as exc:
        print(f"WARNING: ec2 creds creation failed: {exc!s}", file=sys.stderr)
        # pass


def check_for_s3_and_swift(cloud_name: str):
    try:
        connection = connect(cloud_name)
        connection.authorize()
    except Exception as e:
        print(str(e))
        raise Exception(
            f"Connection to cloud '{cloud_name}' was not successfully. "
            f"The Catalog endpoint could not be accessed. "
            f"Please check your cloud connection and authorization."
        )
    s3_creds = {}
    try:
        endpoint = connection.object_store.get_endpoint()
    except Exception as e:
        logger.error(
            f"FAIL: No object store endpoint found. No testing for "
            f"the s3 service possible."
            )
        return 1
    # Get S3 endpoint (swift) and ec2 creds from OpenStack (keystone)
    s3_from_ostack(s3_creds, connection, endpoint)
    # Overrides (var names are from libs3, in case you wonder)
    s3_from_env(s3_creds, "HOST", "S3_HOSTNAME", "https://")
    s3_from_env(s3_creds, "AKI", "S3_ACCESS_KEY_ID")
    s3_from_env(s3_creds, "SAK", "S3_SECRET_ACCESS_KEY")

    s3 = s3_conn(s3_creds, connection)
    s3_buckets = list_s3_buckets(s3)
    if not s3_buckets:
        s3_buckets = create_bucket(s3, TESTCONTNAME)
        assert s3_buckets

    # If we got till here, s3 is working, now swift
    swift_containers = list_containers(connection)
    # if not swift_containers:
    #    swift_containers = create_container(connection, TESTCONTNAME)
    result = 0
    if Counter(s3_buckets) != Counter(swift_containers):
        print("WARNING: S3 buckets and Swift Containers differ:\n"
              f"S3: {sorted(s3_buckets)}\nSW: {sorted(swift_containers)}")
        result = 1
    else:
        print("SUCCESS: S3 and Swift exist and agree")
    # Clean up
    # FIXME: Cleanup created EC2 credential
    # if swift_containers == [TESTCONTNAME]:
    #    del_container(connection, TESTCONTNAME)
    # Cleanup created S3 bucket
    if s3_buckets == [TESTCONTNAME]:
        del_bucket(s3, TESTCONTNAME)
    return result

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

    result = check_presence_of_mandatory_services(cloud)
    result = result + check_for_s3_and_swift(cloud)

    return result


if __name__ == "__main__":
    main()
