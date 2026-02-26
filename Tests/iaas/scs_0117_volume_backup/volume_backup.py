from functools import partial
import logging
import time
import typing

import openstack


# prefix to be included in the names of any Keystone resources created
# used by the cleanup routine to identify resources that can be safely deleted
DEFAULT_PREFIX = "scs-test-"


def check_resources(
    get_func: typing.Callable[[], list[openstack.resource.Resource]],
    prefix: str,
) -> None:
    remaining = [b for b in get_func() if b.name.startswith(prefix)]
    if remaining:
        raise RuntimeError(f"unexpected resources: {remaining}")


def check_resource(
    get_func: typing.Callable[[str], openstack.resource.Resource],
    resource_id: str,
    expected_status=("available", ),
) -> None:
    resource = get_func(resource_id)
    if resource is None:
        raise RuntimeError(f"resource {resource_id} not found")
    if resource.status not in expected_status:
        raise RuntimeError(
            f"Expect resource {resource_id} in "
            f"to be in status {expected_status} (current: {resource.status})"
        )


class TimeoutError(Exception):
    pass


def retry(
    func: callable,
    timeouts=(2, 3, 5, 10, 15, 25, 50),
) -> None:
    seconds_waited = 0
    timeout_iter = iter(timeouts)
    while True:
        try:
            func()
        except Exception as e:
            wait_delay = next(timeout_iter, None)
            if wait_delay is None:
                raise TimeoutError(f"Timed out after {seconds_waited} s: {e!s}")
            time.sleep(wait_delay)
            seconds_waited += wait_delay
        else:
            break


def wait_for_resource(
    get_func: typing.Callable[[str], openstack.resource.Resource],
    resource_id: str,
    expected_status=("available", ),
) -> None:
    retry(partial(check_resource, get_func, resource_id, expected_status))


def wait_for_resources(
    get_func: typing.Callable[[], list[openstack.resource.Resource]],
    prefix: str,
):
    retry(partial(check_resources, get_func, prefix))


def test_backup(conn: openstack.connection.Connection, prefix=DEFAULT_PREFIX) -> None:
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
    wait_for_resource(conn.block_storage.get_volume, volume_id)
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
    wait_for_resource(conn.block_storage.get_backup, backup_id)
    logging.info("Create backup from volume: PASS")

    # RESTORE BACKUP
    restored_volume_name = f"{prefix}restored-backup"
    logging.info(f"Restoring backup to volume '{restored_volume_name}' ...")
    conn.block_storage.restore_backup(backup_id, name=restored_volume_name)

    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to be created ..."
    )
    wait_for_resource(conn.block_storage.find_volume, restored_volume_name)
    # wait for the volume restoration to finish
    logging.info(
        f"↳ waiting for restoration target volume '{restored_volume_name}' "
        f"to reach 'available' status ..."
    )
    volume_id = conn.block_storage.find_volume(restored_volume_name).id
    wait_for_resource(conn.block_storage.get_volume, volume_id)
    logging.info("Restore volume from backup: PASS")


def cleanup(conn: openstack.connection.Connection, prefix=DEFAULT_PREFIX) -> bool:
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
            )
            logging.info(f"↳ deleting volume backup '{backup.id}' ...")
            conn.block_storage.delete_backup(backup.id, ignore_missing=False)
        except Exception as e:
            if isinstance(e, (openstack.exceptions.ResourceNotFound, openstack.exceptions.NotFoundException)):
                # if the resource has vanished on its own in the meantime ignore it
                # however, ResourceNotFound will also be thrown if the service 'cinder-backup' is missing
                if 'cinder-backup' in str(e):
                    raise
                continue
            # Most common exception would be a timeout in wait_for_resource.
            # We do not need to increment cleanup_issues here since
            # any remaining ones will be caught in the next loop down below anyway.
            logging.warning(str(e))

    # wait for all backups to be cleaned up before attempting to remove volumes
    try:
        wait_for_resources(conn.block_storage.backups, prefix)
    except TimeoutError as e:
        cleanup_issues += 1
        logging.warning(str(e))

    volumes = conn.block_storage.volumes()
    for volume in volumes:
        if not volume.name.startswith(prefix):
            continue
        try:
            wait_for_resource(
                conn.block_storage.get_volume,
                volume.id,
                expected_status=("available", "error"),
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


def compute_scs_0117_test_backup(conn, prefix=DEFAULT_PREFIX):
    """
    This test verifies that a properly configured backup driver is present to the extent
    that backup and restore operations succeed on the API level. It does not verify that
    the restored volume is correct (for the sake  of simplicity, it only uses empty volumes
    and does not look at data).
    """
    try:
        if not cleanup(conn, prefix=prefix):
            # what we're usually seeing here is either a problem with cinder-backup or with volumes
            # -- either way, consider this a FAIL, not an ABORT (these things have to work!)
            logging.error("Initial cleanup failed")
            return False
        try:
            test_backup(conn, prefix=prefix)
        finally:
            cleanup(conn, prefix=prefix)
    except BaseException:
        logging.error('Backup test failed.')
        logging.debug('exception details', exc_info=True)
        return False
    else:
        return True
