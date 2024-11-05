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
import os
import time
import typing
import logging

import openstack

# prefix to be included in the names of any Keystone resources created
# used by the cleanup routine to identify resources that can be safely deleted
DEFAULT_PREFIX = "scs-test-"

# timeout in seconds for resource availability checks
# (e.g. a volume becoming available)
WAIT_TIMEOUT = 60


class ConformanceTestException(Exception):
    pass


def ensure(condition: bool, error_message: str):
    """
    Custom replacement for the `assert` statement that is not removed by the
    -O optimization parameter.
    If the condition does not evaluate to `True`, a ConformanceTestException
    will be raised containing the specified error_message string.
    """
    if not condition:
        raise ConformanceTestException(error_message)


def connect(cloud_name: str, password: typing.Optional[str] = None
            ) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :param string password:
        Optional password override for the connection.

    :returns: openstack.connnection.Connection
    """

    if password:
        return openstack.connect(
            cloud=cloud_name,
            password=password
        )
    else:
        return openstack.connect(
            cloud=cloud_name,
        )


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
    volume = conn.block_storage.create_volume(
        name=volume_name,
        size=1
    )
    ensure(
        volume is not None,
        f"Creation of initial volume '{volume_name}' failed"
    )
    volume_id = volume.id
    ensure(
        conn.block_storage.get_volume(volume_id) is not None,
        f"Retrieving initial volume by ID '{volume_id}' failed"
    )

    logging.info(
        f"↳ waiting for volume with ID '{volume_id}' to reach status "
        f"'available' ..."
    )
    seconds_waited = 0
    while conn.block_storage.get_volume(volume_id).status != "available":
        time.sleep(1.0)
        seconds_waited += 1
        ensure(
            seconds_waited < timeout,
            f"Timeout reached while waiting for volume to reach status "
            f"'available' (volume id: {volume_id}) after {seconds_waited} "
            f"seconds"
        )
    logging.info("Create empty volume: PASS")

    # CREATE BACKUP
    logging.info("Creating backup from volume ...")
    backup = conn.block_storage.create_backup(
        name=f"{prefix}volume-backup",
        volume_id=volume_id
    )
    ensure(
        backup is not None,
        "Backup creation failed"
    )
    backup_id = backup.id
    ensure(
        conn.block_storage.get_backup(backup_id) is not None,
        "Retrieving backup by ID failed"
    )

    logging.info(f"↳ waiting for backup '{backup_id}' to become available ...")
    seconds_waited = 0
    while conn.block_storage.get_backup(backup_id).status != "available":
        time.sleep(1.0)
        seconds_waited += 1
        ensure(
            seconds_waited < timeout,
            f"Timeout reached while waiting for backup to reach status "
            f"'available' (backup id: {backup_id}) after {seconds_waited} "
            f"seconds"
        )
    logging.info("Create backup from volume: PASS")

    # RESTORE BACKUP
    restored_volume_name = f"{prefix}restored-backup"
    logging.info(f"Restoring backup to volume '{restored_volume_name}' ...")
    conn.block_storage.restore_backup(
        backup_id,
        name=restored_volume_name
    )

    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to be created ..."
    )
    seconds_waited = 0
    while conn.block_storage.find_volume(restored_volume_name) is None:
        time.sleep(1.0)
        seconds_waited += 1
        ensure(
            seconds_waited < timeout,
            f"Timeout reached while waiting for restored volume to be created "
            f"(volume name: {restored_volume_name}) after {seconds_waited} "
            f"seconds"
        )
    # wait for the volume restoration to finish
    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to reach 'available' status ..."
    )
    volume_id = conn.block_storage.find_volume(restored_volume_name).id
    while conn.block_storage.get_volume(volume_id).status != "available":
        time.sleep(1.0)
        seconds_waited += 1
        ensure(
            seconds_waited < timeout,
            f"Timeout reached while waiting for restored volume reach status "
            f"'available' (volume id: {volume_id}) after {seconds_waited} "
            f"seconds"
        )
    logging.info("Restore volume from backup: PASS")


def cleanup(conn: openstack.connection.Connection, prefix=DEFAULT_PREFIX,
            timeout=WAIT_TIMEOUT) -> bool:
    """
    Looks up volume and volume backup resources matching the given prefix and
    deletes them.
    Returns False if there were any errors during cleanup which might leave
    resources behind. Otherwise returns True to indicate cleanup success.
    """

    def wait_for_resource(resource_type: str, resource_id: str,
                          expected_status=("available", )) -> None:
        seconds_waited = 0
        get_func = getattr(conn.block_storage, f"get_{resource_type}")
        while get_func(resource_id).status not in expected_status:
            time.sleep(1.0)
            seconds_waited += 1
            ensure(
                seconds_waited < timeout,
                f"Timeout reached while waiting for {resource_type} during "
                f"cleanup to be in status {expected_status} "
                f"({resource_type} id: {resource_id}) after {seconds_waited} "
                f"seconds"
            )

    logging.info(f"Performing cleanup for resources with the "
                 f"'{prefix}' prefix ...")

    cleanup_was_successful = True
    backups = conn.block_storage.backups()
    for backup in backups:
        if backup.name.startswith(prefix):
            try:
                wait_for_resource(
                    "backup", backup.id,
                    expected_status=("available", "error")
                )
            except openstack.exceptions.ResourceNotFound:
                # if the resource has vanished on
                # its own in the meantime ignore it
                continue
            except ConformanceTestException as e:
                # This exception happens if the backup state does not reach any
                # of the desired ones specified above. We do not need to set
                # cleanup_was_successful to False here since any remaining ones
                # will be caught in the next loop down below anyway.
                logging.warning(str(e))
            else:
                logging.info(f"↳ deleting volume backup '{backup.id}' ...")
                # Setting ignore_missing to False here will make an exception
                # bubble up in case the cinder-backup service is not present.
                # Since we already catch ResourceNotFound for the backup above,
                # the absence of the cinder-backup service is the only
                # NotFoundException that is left to be thrown here.
                # We treat this as a fatal due to the cinder-backup service
                # being mandatory.
                conn.block_storage.delete_backup(
                    backup.id, ignore_missing=False)

    # wait for all backups to be cleaned up before attempting to remove volumes
    seconds_waited = 0
    while len(
        # list of all backups whose name starts with the prefix
        [b for b in conn.block_storage.backups() if b.name.startswith(prefix)]
    ) > 0:
        time.sleep(1.0)
        seconds_waited += 1
        if seconds_waited >= timeout:
            cleanup_was_successful = False
            logging.warning(
                f"Timeout reached while waiting for all backups with prefix "
                f"'{prefix}' to finish deletion during cleanup after "
                f"{seconds_waited} seconds"
            )
            break

    volumes = conn.block_storage.volumes()
    for volume in volumes:
        if volume.name.startswith(prefix):
            try:
                wait_for_resource("volume", volume.id, expected_status=("available", "error"))
            except openstack.exceptions.ResourceNotFound:
                # if the resource has vanished on
                # its own in the meantime ignore it
                continue
            except ConformanceTestException as e:
                logging.warning(str(e))
                cleanup_was_successful = False
            else:
                logging.info(f"↳ deleting volume '{volume.id}' ...")
                conn.block_storage.delete_volume(volume.id)

    return cleanup_was_successful


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
    cloud = os.environ.get("OS_CLOUD", None)
    if args.os_cloud:
        cloud = args.os_cloud
    if not cloud:
        raise Exception(
            "You need to have the OS_CLOUD environment variable set to your "
            "cloud name or pass it via --os-cloud"
        )
    conn = connect(
        cloud,
        password=getpass.getpass("Enter password: ") if args.ask else None
    )

    if not cleanup(conn, prefix=args.prefix, timeout=args.timeout):
        raise Exception(
            f"Cleanup was not successful, there may be leftover resources "
            f"with the '{args.prefix}' prefix"
        )
    if args.cleanup_only:
        return
    try:
        test_backup(conn, prefix=args.prefix, timeout=args.timeout)
    finally:
        if not cleanup(conn, prefix=args.prefix, timeout=args.timeout):
            logging.info(
                f"There may be leftover resources with the "
                f"'{args.prefix}' prefix that could not be cleaned up!"
            )


if __name__ == "__main__":
    main()
