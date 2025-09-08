import calendar
from collections import Counter
import logging
import sys
import time


logger = logging.getLogger(__name__)


ARCHITECTURES = ("x86_64", "aarch64", "risc-v")
HW_DISK_BUSES = ("virtio", "scsi", None)  # FIXME why None?
HYPERVISOR_TYPES = ("qemu", "kvm", "xen", "hyper-v", "esxi", None)
HW_RNG_MODELS = ("virtio", None)
# Just for nice formatting of image naming hints -- otherwise we capitalize the 1st letter
OS_LIST = ("CentOS", "AlmaLinux", "Windows Server", "RHEL", "SLES", "openSUSE")
# Auxiliary mapping for `freq2secs` (note that values are rounded up a bit on purpose)
FREQ_TO_SEC = {
    "never": 0,
    "critical_bug": 0,
    "yearly": 365 * 24 * 3600,
    "quarterly": 92 * 24 * 3600,
    "monthly": 31 * 24 * 3600,
    "weekly": 7 * 25 * 3600,
    "daily": 25 * 3600,
}
STRICT_FORMATS = ("%Y-%m-%dT%H:%M:%SZ", )
DATE_FORMATS = STRICT_FORMATS + ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
MARKER_DATE_FORMATS = ("%Y-%m-%d", "%Y%m%d")
OUTDATED_MARKERS = ("old", "prev")
KIB, MIB, GIB = (1024 ** n for n in (1, 2, 3))


def recommended_name(nm, os_list=OS_LIST):
    """Return capitalized name"""
    for osnm in os_list:
        osln = len(osnm)
        if nm[:osln].casefold() == osnm.casefold():
            return osnm + nm[osln:]
    return nm[0].upper() + nm[1:]


def is_url(stg):
    """Is string stg a URL?"""
    idx = stg.find("://")
    return idx >= 0 and stg[:idx] in ("http", "https", "ftp", "ftps")


def parse_date(stg, formats=DATE_FORMATS):
    """
    Return time in Unix seconds or 0 if stg is not a valid date.
    We recognize: %Y-%m-%dT%H:%M:%SZ, %Y-%m-%d %H:%M[:%S], and %Y-%m-%d
    """
    bdate = 0
    for fmt in formats:
        try:
            tmdate = time.strptime(stg, fmt)
            bdate = calendar.timegm(tmdate)
            break
        except ValueError:  # as exc:
            # print(f'date {stg} does not match {fmt}\n{exc}', file=sys.stderr)
            pass
    return bdate


def freq2secs(stg):
    """Convert frequency to seconds (round up a bit), return 0 if not applicable"""
    secs = FREQ_TO_SEC.get(stg)
    if secs is None:
        print(f'ERROR: replace frequency {stg}?', file=sys.stderr)
        secs = 0
    return secs


def is_outdated(img, now=time.time()):
    """return 1 if img (with build/regdate bdate) is outdated,
       2 if it's not hidden or marked, 3 if error"""
    bdate = parse_date(img.properties.get('image_build_date', ''))
    if not bdate:
        bdate = parse_date(img.created_at, formats=STRICT_FORMATS)
    replace_frequency = img.properties.get('replace_frequency', 'never')
    if replace_frequency in ('never', 'critical_bug'):
        return 0
    secs = FREQ_TO_SEC.get(replace_frequency)
    if secs is None:
        # NOTE this error is already handled by testcase scs-0102-prop-replace_frequency
        logger.warning(f'invalid replace frequency {replace_frequency}')
        return 0
    if now <= bdate + 1.1 * secs:
        return 0
    # So we found an outdated image that should have been updated
    # (5a1) Check whether we are past the provided_until date
    until_str = img.properties["provided_until"]
    if until_str in ("none", "notice"):
        return 0
    until = parse_date(until_str)
    if not until:
        return 3
    if now > until:
        return 0
    if img.is_hidden:
        return 1
    parts = img.name.rsplit(" ", 1)
    if len(parts) < 2:
        return 2
    marker = parts[1]
    if marker in OUTDATED_MARKERS or parse_date(marker, formats=MARKER_DATE_FORMATS):
        return 1
    return 2


def _log_error(cause, offenders, channel=logging.ERROR):
    if not offenders:
        return
    names = [img.name for img in offenders]
    logger.log(channel, f"{cause} for image(s): {', '.join(names)}")


def compute_scs_0102_prop_architecture(images, architectures=ARCHITECTURES):
    """This test ensures that each image has a proper value for the property `architecture`."""
    offenders = [img for img in images if img.architecture not in architectures]
    _log_error('property architecture not correct', offenders)
    return not offenders


# NOTE I think this is a recommendation
def compute_scs_0102_prop_hash_algo(images):
    """This test ensures that each image has a proper value for the property `hash_algo`."""
    offenders = [img for img in images if img.hash_algo not in ('sha256', 'sha512')]
    _log_error('property hash_algo invalid', offenders)
    return not offenders


def compute_scs_0102_prop_min_disk(images):
    """This test ensures that each image has a proper value for the property `min_disk`."""
    offenders1 = [img for img in images if not img.min_disk]
    _log_error('property min_disk not set', offenders1)
    offenders2 = [img for img in images if img.min_disk and img.min_disk * GIB < img.size]
    _log_error('property min_disk smaller than size', offenders2)
    return not offenders1 and not offenders2


def compute_scs_0102_prop_min_ram(images):
    """This test ensures that each image has a proper value for the property `min_ram`."""
    offenders1 = [img for img in images if not img.min_ram]
    _log_error('property min_ram not set', offenders1)
    # emit a warning im RAM really low
    # NOTE this will probably only get noticed if an error occurs as well
    offenders2 = [img for img in images if img.min_ram and img.min_ram < 64]
    _log_error('property min_ram < 64 MiB', offenders2, channel=logging.WARNING)
    return not offenders1


def compute_scs_0102_prop_os_version(images):
    """This test ensures that each image has a proper value for the property `os_version`."""
    # NOTE currently we are content when the property is not empty, but we could be more strict,
    # because the standard was recently edited to refer to the OpenStack docs, which prescribe
    # certain values for common operating systems.
    offenders = [img for img in images if not img.os_version]
    _log_error('property os_version not set', offenders)
    return not offenders


def compute_scs_0102_prop_os_distro(images):
    """This test ensures that each image has a proper value for the property `os_distro`."""
    # NOTE see note in `compute_scs_0102_prop_os_version`
    offenders = [img for img in images if not img.os_distro]
    _log_error('property os_distro not set', offenders)
    return not offenders


def compute_scs_0102_prop_hw_disk_bus(images, hw_disk_buses=HW_DISK_BUSES):
    """This test ensures that each image has a proper value for the property `hw_disk_bus`."""
    offenders = [img for img in images if img.hw_disk_bus not in hw_disk_buses]
    _log_error('property hw_disk_bus not correct', offenders)
    return not offenders


def compute_scs_0102_prop_hypervisor_type(images, hypervisor_types=HYPERVISOR_TYPES):
    """This test ensures that each image has a proper value for the property `hypervisor_type`."""
    offenders = [img for img in images if img.hypervisor_type not in hypervisor_types]
    _log_error('property hypervisor_type not correct', offenders)
    return not offenders


def compute_scs_0102_prop_hw_rng_model(images, hw_rng_models=HW_RNG_MODELS):
    """This test ensures that each image has a proper value for the property `hw_rng_model`."""
    offenders = [img for img in images if img.hw_rng_model not in hw_rng_models]
    _log_error('property hw_rng_model not correct', offenders)
    return not offenders


def compute_scs_0102_prop_image_build_date(images, now=time.time()):
    """This test ensures that each image has a proper value for the property `image_build_date`."""
    errors = 0
    for img in images:
        rdate = parse_date(img.created_at, formats=STRICT_FORMATS)
        bdate_str = img.properties.get('image_build_date', '')
        bdate = parse_date(bdate_str)
        if not bdate:
            logger.error(f'Image "{img.name}": image_build_date "{bdate_str}" INVALID')
            errors += 1
        elif bdate > rdate:
            logger.error(f'Image "{img.name}": image_build_date {bdate_str} AFTER registration date {img.created_at}')
            errors += 1
        if (bdate or rdate) > now:
            logger.error(f'Image "{img.name}" has build time in the future: {bdate}')
            errors += 1
    return not errors


# FIXME this is completely optional
# def compute_scs_0102_prop_patchlevel(image):
#     return True


def compute_scs_0102_prop_image_original_user(images):
    """This test ensures that each image has a proper value for the property `image_original_user`."""
    offenders = [img for img in images if not img.properties.get('image_original_user')]
    _log_error('property image_original_user not set', offenders)
    return not offenders


def compute_scs_0102_prop_image_source(images):
    """This test ensures that each image has a proper value for the property `image_source`."""
    offenders = [
        img
        for img in images
        if img.properties.get('image_source') != 'private'
        if not is_url(img.properties.get('image_source'))
    ]
    _log_error('property image_source INVALID (url or "private")', offenders)
    return not offenders


def compute_scs_0102_prop_image_description(images):
    """This test ensures that each image has a proper value for the property `image_description`."""
    offenders = [img for img in images if not img.properties.get('image_description')]
    _log_error('property image_description not set', offenders)
    return not offenders


def compute_scs_0102_prop_replace_frequency(images, replace_frequencies=FREQ_TO_SEC):
    """This test ensures that each image has a proper value for the property `replace_frequency`."""
    offenders = [img for img in images if img.properties.get('replace_frequency') not in replace_frequencies]
    _log_error('property replace_frequency not correct', offenders)
    return not offenders


def compute_scs_0102_prop_provided_until(images):
    """This test ensures that each image has a proper value for the property `provided_until`."""
    offenders = [img for img in images if not img.properties.get('provided_until')]
    _log_error('property provided_until not set', offenders)
    return not offenders


def compute_scs_0102_prop_uuid_validity(images):
    """This test ensures that each image has a proper value for the property `uuid_validity`."""
    errors = 0
    for img in images:
        img_uuid_val = img.properties.get("uuid_validity")
        if img_uuid_val in (None, "none", "notice", "forever"):
            pass
        elif img_uuid_val[:5] == "last-" and img_uuid_val[5:].isdecimal():
            pass
        elif parse_date(img_uuid_val):
            pass
        else:
            logger.error(f'Image "{img.name}": property uuid_validity INVALID: {img_uuid_val}')
            errors += 1
    return not errors


def compute_scs_0102_prop_hotfix_hours(images):
    """This test ensures that each image has a proper value for the property `hotfix_hours`."""
    errors = 0
    for img in images:
        hotfix_hours = img.properties.get("hotfix_hours", '')
        if not hotfix_hours or hotfix_hours.isdecimal():
            continue
        logger.error(f'Image "{img.name}": property hotfix_hours INVALID: {hotfix_hours}')
        errors += 1
    return not errors


def _find_replacement_image(by_name, img_name):
    shortnm = img_name.rsplit(" ", 1)[0].rstrip()
    if shortnm == img_name:
        return None
    replacement = by_name.get(shortnm)
    if replacement is None or is_outdated(replacement):
        return None
    return replacement


def compute_scs_0102_image_recency(images):
    """
    This test ensures that each image is as recent as claimed by `replace_frequency`.

    If an image is outdated, it is not deemed critical in the following two cases:

    1. If the image is past its `provided_until` date, since no guarantees are given for these.
    2. If a recent variant of the image is found.

    However, a warning is issued if an outdated image is not hidden.
    """
    by_name = {img.name: img for img in images}
    if len(by_name) != len(images):
        counter = Counter([img.name for img in images])
        duplicates = [name for name, count in counter.items() if count > 1]
        logger.warning(f'duplicate names detected: {", ".join(duplicates)}')
    errors = 0
    for img in images:
        #  This is a bit tricky: We need to disregard images that have been rotated out
        #  - os_hidden = True is a safe sign for this
        #  - A name with a date stamp or old or prev (and a newer exists)
        outd = is_outdated(img)
        if not outd:
            continue  # fine
        if outd == 3:
            logger.error(f'Image "{img.name}" does not provide a valid provided until date')
            errors += 1
            continue  # hopeless
        # in case that outd in (1, 2) try to find a non-outdated version
        if outd == 2:
            logger.warning(f'Image "{img.name}" seems outdated (acc. to its repl freq) but is not hidden or otherwise marked')
            # warnings += 1
        replacement = _find_replacement_image(by_name, img.name)
        if replacement is None:
            logger.error(f'Image "{img.name}" outdated without replacement')
            errors += 1
        else:
            logger.info(f'Image "{replacement.name}" is a valid replacement for outdated "{img.name}"')
    return not errors
