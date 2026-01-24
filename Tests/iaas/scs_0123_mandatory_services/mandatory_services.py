import json
import logging
import re
import uuid

import boto3
import openstack


TESTCONTNAME = "scs-test-container"
EC2MARKER = "TmpMandSvcTest"

logger = logging.getLogger(__name__)
# NOTE suppress excessive logging (who knows what sensitive data might be in there)
# For the time being, I don't know where else to do it, but I guess it's fine.
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3.resources').setLevel(logging.WARNING)


def compute_scs_0123_service_presence(services_lookup, *names):
    services = []
    for name in names:
        services.extend(services_lookup.get(name, ()))
    if not services:
        logger.error(f"No service of type(s) {', '.join(names)} found.")
    return bool(services)


def s3_conn(creds, conn):
    """Return an s3 client conn"""
    cacert = conn.config.config.get("cacert")
    # TODO: Handle self-signed certs (from ca_cert in openstack config)
    if cacert:
        logger.warning(f"Trust all Certificates in S3, OpenStack uses {cacert}")
    return boto3.resource(
        's3', endpoint_url=creds["HOST"], verify=not cacert,
        aws_access_key_id=creds["AK"], aws_secret_access_key=creds["SK"],
    )


def _parse_blob(cred):
    try:
        return json.loads(cred.blob)
    except Exception as exc:
        logger.debug(f"unable to parse credential {cred!r}: {exc!r}")
        return None


def get_usable_credentials(conn):
    """
    get all ec2 credentials for this project that carry meaningful data

    returns list of pairs (credential, parsed ec2 data)
    """
    project_id = conn.identity.get_project_id()
    candidates = [
        (cred, _parse_blob(cred))
        for cred in conn.identity.credentials()
        if cred.type == "ec2" and cred.project_id == project_id
    ]
    return [
        (cred, parsed)
        for cred, parsed in candidates
        if parsed and parsed.get('access') and parsed.get('secret')
    ]


def remove_leftovers(usable_credentials, conn):
    """
    makes sure to delete any leftover set of ec2 credentials
    """
    result = []
    for item in usable_credentials:
        cred, parsed = item
        if parsed.get("owner") == EC2MARKER:
            logger.debug(f"Removing leftover credential {parsed['access']}")
            conn.identity.delete_credential(cred)
        else:
            result.append(item)
    return result


def ensure_ec2_credentials(usable_credentials, conn):
    if usable_credentials:
        return usable_credentials
    parsed = {
        "access": uuid.uuid4().hex,
        "secret": uuid.uuid4().hex,
        "owner": EC2MARKER,
    }
    blob = json.dumps(parsed)
    try:
        crd = conn.identity.create_credential(
            type="ec2", blob=blob, user_id=conn.current_user_id, project_id=conn.current_project_id,
        )
    except BaseException:
        logger.warning("ec2 creds creation failed", exc_info=True)
        raise
    usable_credentials.append((crd, parsed))
    return usable_credentials  # also return for chaining


def s3_from_ostack(usable_credentials, conn, rgx=re.compile(r"^(https*://[^/]*)/")):
    """Set creds from openstack swift/keystone"""
    # just use the first usable set of ec2 credentials
    _, parsed = usable_credentials[0]
    s3_creds = {
        "AK": parsed["access"],
        "SK": parsed["secret"],
    }
    m = rgx.match(conn.object_store.get_endpoint())
    if m:
        s3_creds["HOST"] = m.group(1)
    return s3_creds


def compute_scs_0123_swift_s3(services_lookup, conn: openstack.connection.Connection):
    """
    This test ensures that S3 can be used to access object storage using EC2 credentials from the identity API.
    """
    if 'object-store' not in services_lookup:
        logger.error('scs-0123-swift-s3 test requires catalog entry')
        return False
    # we assume s3 is accessible via the service catalog, and Swift might exist too
    usable_credentials = []
    s3_buckets = []
    # Get S3 endpoint (swift) and ec2 creds from OpenStack (keystone)
    try:
        usable_credentials = remove_leftovers(get_usable_credentials(conn), conn)
        # we could use any credential from the list usable_credentials, but let's not do that,
        # because they could be stale
        del usable_credentials[:]
        s3_creds = s3_from_ostack(ensure_ec2_credentials(usable_credentials, conn), conn)

        # This is to be used for local debugging purposes ONLY
        # logger.debug(f"using credentials {s3_creds}")

        s3 = s3_conn(s3_creds, conn)
        buckets = list(s3.buckets.all())
        if not buckets:
            s3.create_bucket(Bucket=TESTCONTNAME)
            buckets = list(s3.buckets.all())
        if not buckets:
            raise RuntimeError("failed to create S3 bucket")

        # actual test: buckets must equal containers (sort in case the order is different)
        s3_buckets = sorted([b.name for b in buckets])
        sw_containers = sorted([c.name for c in conn.object_store.containers()])
        if s3_buckets == sw_containers:
            return True
        logger.error(
            "S3 buckets and Swift containers differ:\n"
            f"S3: {s3_buckets}\n"
            f"SW: {sw_containers}"
        )
        return False
    finally:
        # Cleanup created S3 bucket
        if TESTCONTNAME in s3_buckets:
            # contrary to Boto docs at
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_bucket.html
            # , the following fails with
            # AttributeError: 's3.ServiceResource' object has no attribute 'delete_bucket'. Did you mean: 'create_bucket'?
            # s3.delete_bucket(Bucket=TESTCONTNAME)
            # workaround:
            s3.Bucket(name=TESTCONTNAME).delete()
        # Clean up ec2 cred IF we created one
        remove_leftovers(usable_credentials, conn)
