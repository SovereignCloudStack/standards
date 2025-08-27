#!/usr/bin/env python3
"""Volume Backup API tester for Block Storage API

This test script executes basic operations on the Block Storage API centered
around volume backups. Its purpose is to verify that the Volume Backup API is
available and working as expected using simple operations such as creating and
restoring volume backups.

It verifies that a properly configured backup driver is present to the extent
that aforementioned operations succeed on the API level. It does not by any
means verify that the backup and restore procedures actual handle the data
correctly (it only uses empty volumes and does not look at data for the sake
of simplicity).
"""

import argparse
import getpass
import logging
import os
import sys

import openstack


from volume_backup import DEFAULT_PREFIX, cleanup, compute_scs_0117_test_backup


def main():
    parser = argparse.ArgumentParser(
        description="SCS Volume Backup API Conformance Checker")
    parser.add_argument(
        "--os-cloud", type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable"
    )
    parser.add_argument(
        "--ask",
        help="Ask for password interactively instead of reading it from the "
        "clouds.yaml",
        action="store_true"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable OpenStack SDK debug logging"
    )
    parser.add_argument(
        "--prefix", type=str,
        default=DEFAULT_PREFIX,
        help=f"OpenStack resource name prefix for all resources to be created "
        f"and/or cleaned up by this script within the configured domains "
        f"(default: '{DEFAULT_PREFIX}')"
    )
    parser.add_argument(
        "--cleanup-only", action="store_true",
        help="Instead of executing tests, cleanup all resources "
        "with the prefix specified via '--prefix' (or its default)"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=False)
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    # parse cloud name for lookup in clouds.yaml
    cloud = args.os_cloud or os.environ.get("OS_CLOUD", None)
    if not cloud:
        raise Exception(
            "You need to have the OS_CLOUD environment variable set to your "
            "cloud name or pass it via --os-cloud"
        )
    password = getpass.getpass("Enter password: ") if args.ask else None

    with openstack.connect(cloud, password=password) as conn:
        if args.cleanup_only:
            if not cleanup(conn, prefix=args.prefix):
                raise RuntimeError("cleanup failed")
        else:
            compute_scs_0117_test_backup(conn, prefix=args.prefix)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        logging.debug("traceback", exc_info=True)
        logging.critical(str(exc))
        sys.exit(1)
