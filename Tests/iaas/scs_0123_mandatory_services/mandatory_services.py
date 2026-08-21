import logging
import re

import boto3
import openstack


HOST_REGEX = re.compile(r"^(https*://[^/]*)/")

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
    cfg = conn.config.config
    # Take insecure/verify/cacert parameter from clouds.yaml and pass it to boto3.resource.
    # If insecure is False/None and verify is True/None in clouds.yaml, fall back to cacert or None.
    # In the latter case (None), the default boto3 behavior is applied (where config file or env
    # variables can still be used, and otherwise, boto3 defaults to verify=True).
    # Note: cacert must be used to pass the certificate; don't use verify for that; cf.
    # https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html#ssl-settings
    if cfg.get("insecure") or not cfg.get("verify", True):
        verify = False
    else:
        verify = cfg.get("cacert")
    return boto3.resource(
        's3', endpoint_url=creds["HOST"], verify=verify,
        aws_access_key_id=creds["AK"], aws_secret_access_key=creds["SK"],
    )


def compute_scs_0123_swift_s3(services_lookup, conn: openstack.connection.Connection):
    """
    This test ensures that S3 is present next to Swift.
    """
    if 'object-store' not in services_lookup:
        logger.info('skipping scs-0123-swift-s3 because object-store not present')
        return True
    m = HOST_REGEX.match(conn.object_store.get_endpoint())
    s3_creds = {
        "AK": "doesnotexist",
        "SK": "",
        "HOST": m and m.group(1),
    }
    try:
        list(s3_conn(s3_creds, conn).buckets.all())
    except Exception as error:
        txt = str(error)
        return "InvalidAccessKeyId" in txt or "NoSuchKey" in txt
    else:
        raise RuntimeError("this can not happen")
