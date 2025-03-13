#!/usr/bin/env python3
"""Mandatory APIs checker
This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and checks whether all mandatory APi endpoints, are present.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.
As the s3 endpoint might differ, a missing one will only result in a warning.
"""

import argparse
from collections import Counter
import logging
import os
import re
import sys
import uuid
import boto3

import openstack


TESTCONTNAME = "scs-test-container"

logger = logging.getLogger(__name__)
mandatory_services = ["compute", "identity", "image", "network",
                      "load-balancer", "placement", "object-store"]
block_storage_service = ["volume", "volumev3", "block-storage"]


def check_presence_of_mandatory_services(conn: openstack.connection.Connection, s3_credentials=None):
    services = conn.service_catalog

    if s3_credentials:
        mandatory_services.remove("object-store")
    for svc in services:
        svc_type = svc['type']
        if svc_type in mandatory_services:
            mandatory_services.remove(svc_type)
        elif svc_type in block_storage_service:
            block_storage_service.remove(svc_type)

    bs_service_not_present = 0
    if len(block_storage_service) == 3:
        # neither block-storage nor volume nor volumev3 is present
        # we must assume, that there is no volume service
        logger.error("No block-storage (volume) endpoint found.")
        mandatory_services.append(block_storage_service[0])
        bs_service_not_present = 1
    if mandatory_services:
        # some mandatory APIs were not found
        logger.error(f"The following endpoints are missing: "
                     f"{', '.join(mandatory_services)}.")
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
    if conn:
        cacert = conn.config.config.get("cacert")
        # TODO: Handle self-signed certs (from ca_cert in openstack config)
        if cacert:
            logger.warning(f"Trust all Certificates in S3, OpenStack uses {cacert}")
            vrfy = False
    return boto3.resource('s3', aws_access_key_id=creds["AK"],
                          aws_secret_access_key=creds["SK"],
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
        logger.warning(f"s3_creds[{fieldnm}] not set")


def s3_from_ostack(creds, conn, endpoint):
    """Set creds from openstack swift/keystone
       Returns credential ID *if* an ec2 credential was created,
       None otherwise."""
    rgx = re.compile(r"^(https*://[^/]*)/")
    match = rgx.match(endpoint)
    if match:
        creds["HOST"] = match.group(1)
    # Use first ec2 cred that matches the project (if one exists)
    project_id = conn.identity.get_project_id()
    ec2_creds = [cred for cred in conn.identity.credentials()
                 if cred.type == "ec2" and cred.project_id == project_id]
    if len(ec2_creds):
        # FIXME: Assume cloud is not evil
        ec2_dict = eval(ec2_creds[0].blob, {"null": None})
        creds["AK"] = ec2_dict["access"]
        creds["SK"] = ec2_dict["secret"]
        return None
    # Generate keyid and secret
    ak = uuid.uuid4().hex
    sk = uuid.uuid4().hex
    blob = f'{{"access": "{ak}", "secret": "{sk}"}}'
    try:
        crd = conn.identity.create_credential(type="ec2", blob=blob,
                                              user_id=conn.current_user_id,
                                              project_id=conn.current_project_id)
        creds["AK"] = ak
        creds["SK"] = sk
        return crd.id
    except BaseException as excn:
        logger.warning(f"ec2 creds creation failed: {excn!s}")
        # pass
    return None


def check_for_s3_and_swift(conn: openstack.connection.Connection, s3_credentials=None):
    # If we get credentials, we assume that there is no Swift and only test s3
    if s3_credentials:
        try:
            s3 = s3_conn(s3_credentials)
        except Exception:
            logger.debug("details", exc_info=True)
            logger.error("Connection to S3 failed.")
            return 1
        s3_buckets = list_s3_buckets(s3) or create_bucket(s3, TESTCONTNAME)
        if not s3_buckets:
            raise RuntimeError("failed to create S3 bucket")
        if s3_buckets == [TESTCONTNAME]:
            del_bucket(s3, TESTCONTNAME)
        # everything worked, and we don't need to test for Swift:
        logger.info("SUCCESS: S3 exists")
        return 0
    # there were no credentials given, so we assume s3 is accessable via
    # the service catalog and Swift might exist too
    s3_creds = {}
    try:
        endpoint = conn.object_store.get_endpoint()
    except Exception:
        logger.exception(
            "No object store endpoint found. No testing for the s3 service possible."
        )
        return 1
    # Get S3 endpoint (swift) and ec2 creds from OpenStack (keystone)
    ec2_cred = s3_from_ostack(s3_creds, conn, endpoint)
    # Overrides (var names are from libs3, in case you wonder)
    s3_from_env(s3_creds, "HOST", "S3_HOSTNAME", "https://")
    s3_from_env(s3_creds, "AK", "S3_ACCESS_KEY_ID")
    s3_from_env(s3_creds, "SK", "S3_SECRET_ACCESS_KEY")

    # This is to be used for local debugging purposes ONLY
    # logger.info(f"using credentials {s3_creds}")

    s3 = s3_conn(s3_creds, conn)
    s3_buckets = list_s3_buckets(s3) or create_bucket(s3, TESTCONTNAME)
    if not s3_buckets:
        raise RuntimeError("failed to create S3 bucket")

    # If we got till here, s3 is working, now swift
    swift_containers = list_containers(conn)
    # if not swift_containers:
    #    swift_containers = create_container(conn, TESTCONTNAME)
    result = 0
    # Compare number of buckets/containers
    # FIXME: Could compare list of sorted names
    if Counter(s3_buckets) != Counter(swift_containers):
        logger.error("S3 buckets and Swift Containers differ:\n"
                     f"S3: {sorted(s3_buckets)}\nSW: {sorted(swift_containers)}")
        result = 1
    else:
        logger.info("SUCCESS: S3 and Swift exist and agree")
    # No need to clean up swift container, as we did not create one
    # (If swift and S3 agree, there will be a S3 bucket that we clean up with S3.)
    # if swift_containers == [TESTCONTNAME]:
    #    del_container(conn, TESTCONTNAME)
    # Cleanup created S3 bucket
    if s3_buckets == [TESTCONTNAME]:
        del_bucket(s3, TESTCONTNAME)
    # Clean up ec2 cred IF we created one
    if ec2_cred:
        conn.identity.delete_credential(ec2_cred)
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
        "--s3-endpoint", type=str,
        help="URL to the s3 service."
    )
    parser.add_argument(
        "--s3-access", type=str,
        help="Access Key to connect to the s3 service."
    )
    parser.add_argument(
        "--s3-access-secret", type=str,
        help="Access secret to connect to the s3 service."
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable OpenStack SDK debug logging"
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
    )
    openstack.enable_logging(debug=False)

    # parse cloud name for lookup in clouds.yaml
    cloud = args.os_cloud or os.environ.get("OS_CLOUD", None)
    if not cloud:
        raise RuntimeError(
            "You need to have the OS_CLOUD environment variable set to your "
            "cloud name or pass it via --os-cloud"
        )

    s3_credentials = None
    if args.s3_endpoint:
        if (not args.s3_access) or (not args.s3_access_secret):
            logger.warning("test for external s3 needs access key and access secret.")
        s3_credentials = {
            "AK": args.s3_access,
            "SK": args.s3_access_secret,
            "HOST": args.s3_endpoint
        }
    elif args.s3_access or args.s3_access_secret:
        logger.warning("access to s3 was given, but no endpoint provided.")

    with openstack.connect(cloud) as conn:
        result = check_presence_of_mandatory_services(conn, s3_credentials)
        result += check_for_s3_and_swift(conn, s3_credentials)

    print('service-apis-check: ' + ('PASS', 'FAIL')[min(1, result)])

    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        logging.debug("traceback", exc_info=True)
        logging.critical(str(exc))
        sys.exit(1)
