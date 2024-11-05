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
import time
import typing

import openstack

# prefix to be included in the names of any Keystone resources created
# used by the cleanup routine to identify resources that can be safely deleted
DEFAULT_PREFIX = "scs-test-"

# timeout in seconds for resource availability checks
# (e.g. a volume becoming available)
WAIT_TIMEOUT = 60


def wait_for_resource(
    get_func: typing.Callable[[str], openstack.resource.Resource],
    resource_id: str,
    expected_status=("available", ),
    timeout=WAIT_TIMEOUT,
) -> None:
    seconds_waited = 0
    resource = get_func(resource_id)
    while resource is None or resource.status not in expected_status:
        time.sleep(1.0)
        seconds_waited += 1
        if seconds_waited >= timeout:
            raise RuntimeError(
                f"Timed out after {seconds_waited} s: waiting for {resource_type} {resource_id} "
                f"to be in status {expected_status} (current: {resource and resource.status})"
            )
        resource = get_func(resource_id)


def test_backup(conn: openstack.connection.Connection,
                prefix=DEFAULT_PREFIX, timeout=WAIT_TIMEOUT) -> None:
    """Execute volume backup tests on the connection

    This will create an empty volume, a backup of that empty volume and then
    attempt to restore the backup onto a new volume.
    Purpose of these tests is to verify that the volume backup API is working
    correctly.
    """

    # CREATE VOLUME
    volume_name = f"{prefix}volume"
    logging.info(f"Creating volume '{volume_name}' ...")
    volume = conn.block_storage.create_volume(name=volume_name, size=1)
    if volume is None:
        raise RuntimeError(f"Creation of initial volume '{volume_name}' failed")
    volume_id = volume.id
    if conn.block_storage.get_volume(volume_id) is None:
        raise RuntimeError(f"Retrieving initial volume by ID '{volume_id}' failed")

    logging.info(
        f"↳ waiting for volume with ID '{volume_id}' to reach status "
        f"'available' ..."
    )
    wait_for_resource(conn.block_storage.get_volume, volume_id, timeout=timeout)
    logging.info("Create empty volume: PASS")

    # CREATE BACKUP
    logging.info("Creating backup from volume ...")
    backup = conn.block_storage.create_backup(name=f"{prefix}volume-backup", volume_id=volume_id)
    if backup is None:
        raise RuntimeError("Backup creation failed")
    backup_id = backup.id
    if conn.block_storage.get_backup(backup_id) is None:
        raise RuntimeError("Retrieving backup by ID failed")

    logging.info(f"↳ waiting for backup '{backup_id}' to become available ...")
    wait_for_resource(conn.block_storage.get_backup, backup_id, timeout=timeout)
    logging.info("Create backup from volume: PASS")

    # RESTORE BACKUP
    restored_volume_name = f"{prefix}restored-backup"
    logging.info(f"Restoring backup to volume '{restored_volume_name}' ...")
    conn.block_storage.restore_backup(backup_id, name=restored_volume_name)

    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to be created ..."
    )
    wait_for_resource(conn.block_storage.find_volume, restored_volume_name, timeout=timeout)
    # wait for the volume restoration to finish
    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to reach 'available' status ..."
    )
    volume_id = conn.block_storage.find_volume(restored_volume_name).id
    wait_for_resource(conn.block_storage.get_volume, volume_id, timeout=timeout)
    logging.info("Restore volume from backup: PASS")


def cleanup(conn: openstack.connection.Connection, prefix=DEFAULT_PREFIX,
            timeout=WAIT_TIMEOUT) -> bool:
    """
    Looks up volume and volume backup resources matching the given prefix and
    deletes them.
    Returns False if there were any errors during cleanup which might leave
    resources behind. Otherwise returns True to indicate cleanup success.
    """

    logging.info(f"Performing cleanup for resources with the '{prefix}' prefix ...")

    cleanup_issues = 0  # count failed cleanup operations
    backups = conn.block_storage.backups()
    for backup in backups:
        if not backup.name.startswith(prefix):
            continue
        try:
            # we can only delete if status is available or error, so try and wait
            wait_for_resource(
                conn.block_storage.get_backup,
                backup.id,
                expected_status=("available", "error"),
                timeout=timeout,
            )
            logging.info(f"↳ deleting volume backup '{backup.id}' ...")
            conn.block_storage.delete_backup(backup.id)
        except openstack.exceptions.ResourceNotFound:
            # if the resource has vanished on its own in the meantime ignore it
            continue
        except Exception as e:
            # Most common exception would be a timeout in wait_for_resource.
            # We do not need to increment cleanup_issues here since
            # any remaining ones will be caught in the next loop down below anyway.
            logging.debug("traceback", exc_info=True)
            logging.warning(str(e))

    # wait for all backups to be cleaned up before attempting to remove volumes
    seconds_waited = 0
    while len(
        # list of all backups whose name starts with the prefix
        [b for b in conn.block_storage.backups() if b.name.startswith(prefix)]
    ) > 0:
        time.sleep(1.0)
        seconds_waited += 1
        if seconds_waited >= timeout:
            cleanup_issues += 1
            logging.warning(
                f"Timeout reached while waiting for all backups with prefix "
                f"'{prefix}' to finish deletion during cleanup after "
                f"{seconds_waited} seconds"
            )
            break

    volumes = conn.block_storage.volumes()
    for volume in volumes:
        if not volume.name.startswith(prefix):
            continue
        try:
            wait_for_resource(
                conn.block_storage.get_volume,
                volume.id,
                expected_status=("available", "error"),
                timeout=timeout,
            )
            logging.info(f"↳ deleting volume '{volume.id}' ...")
            conn.block_storage.delete_volume(volume.id)
        except openstack.exceptions.ResourceNotFound:
            # if the resource has vanished on its own in the meantime ignore it
            continue
        except Exception as e:
            logging.debug("traceback", exc_info=True)
            logging.warning(str(e))
            cleanup_issues += 1
    
    if cleanup_issues:
        logging.info(
            f"Some resources with the '{prefix}' prefix were not cleaned up!"
        )

    return not cleanup_issues


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
        "--timeout", type=int,
        default=WAIT_TIMEOUT,
        help=f"Timeout in seconds for operations waiting for resources to "
        f"become available such as creating volumes and volume backups "
        f"(default: '{WAIT_TIMEOUT}')"
    )
    parser.add_argument(
        "--cleanup-only", action="store_true",
        help="Instead of executing tests, cleanup all resources "
        "with the prefix specified via '--prefix' (or its default)"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=args.debug)
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
        if not cleanup(conn, prefix=args.prefix, timeout=args.timeout):
            raise RuntimeError(f"Initial cleanup failed")
        if args.cleanup_only:
            logging.info("Cleanup-only run finished.")
            return
        try:
            test_backup(conn, prefix=args.prefix, timeout=args.timeout)
        except BaseException:
            print('volume-backup-check: FAIL')
            raise
        else:
            print('volume-backup-check: PASS')
        finally:
            cleanup(conn, prefix=args.prefix, timeout=args.timeout)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        logging.debug("traceback", exc_info=True)
        logging.critical(str(exc))
        sys.exit(1)
