#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# SCS/Docs/tools/image-md-check.py

"""
Retrieve metadata from (public) images and check for compliance
with SCS specifications.

(c) Kurt Garloff <kurt@garloff.de>, 09/2022
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import os
import sys
import time
import calendar
import getopt
import openstack


def usage(ret):
    "Usage information"
    print("Usage: image-md-check.py [options] [images]")
    print("image-md-check.py will create a report on public images by retrieving")
    print(" the image metadata (properties) and comparing this against the image")
    print(" metadata spec from SCS.")
    print("Options: --os-cloud CLOUDNAME: Use this cloud config, default is $OS_CLOUD")
    print(" -p/--private : Also consider private images")
    print(" -v/--verbose : Be more verbose")
    print(" -s/--skip-completeness: Don't check whether we have all mandatory images")
    print(" -h/--help    : Print this usage information")
    print("If you pass images, only these will be validated, otherwise all (public unless")
    print(" -p is specified) images from the catalog will be processed.")
    sys.exit(ret)


# global options
verbose = False
private = False
skip = False

# Image list
mand_images = ["Ubuntu 22.04", "Ubuntu 20.04", "Debian 11"]
rec1_images = ["CentOS 8", "Rocky 8", "AlmaLinux 8", "Debian 10", "Fedora 36"]
rec2_images = ["SLES 15SP4", "RHEL 9", "RHEL 8", "Windows Server 2022", "Windows Server 2019"]
sugg_images = ["openSUSE Leap 15.4", "Cirros 0.5.2", "Alpine", "Arch"]

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


def recommended_name(nm, os_list=OS_LIST):
    """Return capitalized name"""
    for osnm in os_list:
        osln = len(osnm)
        if nm[:osln].casefold() == osnm.casefold():
            return osnm + nm[osln:]
    return nm[0].upper() + nm[1:]


class Property:
    "Class to specify properties, allowed values, ..."
    def __init__(self, name, mand, values, desc = ""):
        self.name = name
        self.ismand = mand
        self.values = values
        if desc:
            self.desc = desc
        else:
            self.desc = name

    def is_ok(self, props, warn = ""):
        "Check validity of properties"
        if self.name in props:
            if self.values and not props[self.name] in self.values:
                if warn:
                    print(f'ERROR: Image "{warn}": value "{props[self.name]}" for property '
                          f'"{self.name}" not allowed', file=sys.stderr)
                return False
            if not props[self.name] and not self.values:
                err = "ERROR"
                ret = False
            else:
                err = "WARNING"
                ret = True
            if not props[self.name] and (verbose or not self.values) and warn:
                print(f'{err}: Image "{warn}": empty value for property "{self.name}" not recommended',
                      file=sys.stderr)
            return ret
        if self.ismand:
            if warn:
                print(f'ERROR: Image "{warn}": Mandatory property "{self.name}" is missing',
                      file=sys.stderr)
            return False
        if warn and verbose:
            print(f'INFO: Image "{warn}": Optional property "{self.name}" is missing')  # , file=sys.stderr)
        return True


# From the image metadata specification
# https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Image-Properties-Spec.md
os_props = (Property("os_distro", True, ()),
            Property("os_version", True, ()))
arch_props = (Property("architecture", True, ("x86_64", "aarch64", "risc-v"), "CPU architecture"),
              Property("hypervisor_type", True, ("qemu", "kvm", "xen", "hyper-v", "esxi", None)))
hw_props = (Property("hw_rng_model", False, ("virtio", None), "Random Number Generator"),
            Property("hw_disk_bus", True, ("virtio", "scsi", None), "Disk bus: vda or sda"))
build_props = (Property("image_build_date", True, ()),
               Property("patchlevel", False, (),),
               Property("image_original_user", True, (), "Default ssh username"),
               Property("image_source", True, ()),
               Property("image_description", True, ()))
maint_props = (Property("replace_frequency", True, ("yearly", "quarterly", "monthly", "weekly",
                                                    "daily", "critical_bug", "never")),
               Property("provided_until", True, ()),
               Property("uuid_validity", True, ()),
               Property("hotfix_hours", False, ()))


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


OUTDATED_IMAGES = []


def is_outdated(img, bdate):
    """return 1 if img (with build/regdate bdate) is outdated,
       2 if it's not hidden or marked, 3 if error"""
    max_age = 0
    if "replace_frequency" in img.properties:
        max_age = 1.1 * (freq2secs(img.properties["replace_frequency"]))
    if not max_age or time.time() <= max_age + bdate:
        return 0
    # So we found an outdated image that should have been updated
    # (5a1) Check whether we are past the provided_until date
    until_str = img.properties["provided_until"]
    until = parse_date(img.properties["provided_until"])
    if not until and not until_str == "none" and not until_str == "notice":
        print(f'ERROR: Image "{img.name}" does not provide a valid provided until date',
              file=sys.stderr)
        return 3
    if time.time() > until:
        return 0
    if img.is_hidden or img.name[-3:] == "old" or img.name[-4:] == "prev" or img.name[-8:].isdecimal():
        return 1
    if parse_date(img.name[-10:]):
        return 1
    print(f'WARNING: Image "{img.name}" seems outdated (acc. to its repl freq) but is not hidden or otherwise marked',
          file=sys.stderr)
    return 2


def validate_imageMD(img):
    """Retrieve image properties and test for compliance with spec"""
    # global OUTDATED_IMAGES
    imgnm = img.name
    # Now the hard work: Look at properties ....
    errors = 0
    warnings = 0
    # (1) recommended os_* and hw_*
    for prop in (*os_props, *arch_props, *hw_props):
        if not prop.is_ok(img, imgnm):
            errors += 1
    constr_name = f"{img.os_distro} {img.os_version}"
    # (3) os_hash
    if img.hash_algo not in ('sha256', 'sha512'):
        print(f'WARNING: Image "{imgnm}": no valid hash algorithm {img.hash_algo}', file=sys.stderr)
        # errors += 1
        warnings += 1

    # (4) image_build_date, image_original_user, image_source (opt image_description)
    # (5) maintained_until, provided_until, uuid_validity, replace_frequency
    for prop in (*build_props, *maint_props):
        if not prop.is_ok(img.properties, imgnm):
            errors += 1
    # Some more sanity checks:
    #  - Dateformat for image_build_date
    rdate = parse_date(img.created_at, formats=STRICT_FORMATS)
    bdate = rdate
    if "image_build_date" in img.properties:
        bdate = parse_date(img.properties["image_build_date"])
        if bdate > rdate:
            print(f'ERROR: Image "{imgnm}" with build date {img.properties["image_build_date"]} after registration date {img.created_at}',
                  file=sys.stderr)
            errors += 1
        if not bdate:
            print(f'ERROR: Image "{imgnm}": no valid image_build_date '
                  f'{img.properties["image_build_date"]}', file=sys.stderr)
            errors += 1
            bdate = rdate
    if bdate > time.time():
        print(f'ERROR: Image "{imgnm}" has build time in the future: {bdate}')
        errors += 1
    # - image_source should be a URL
    if "image_source" not in img.properties:
        pass  # we have already noted this as error, no need to do it again
    elif img.properties["image_source"] == "private":
        if verbose:
            print(f'INFO: Image {imgnm} has image_source set to private', file=sys.stderr)
    elif not is_url(img.properties["image_source"]):
        print(f'ERROR: Image "{imgnm}": image_source should be a URL or "private"', file=sys.stderr)
        errors += 1
    #  - uuid_validity has a distinct set of options (none, last-X, DATE, notice, forever)
    if "uuid_validity" in img.properties:
        img_uuid_val = img.properties["uuid_validity"]
        if img_uuid_val in ("none", "notice", "forever"):
            pass
        elif img_uuid_val[:5] == "last-" and img_uuid_val[5:].isdecimal():
            pass
        elif parse_date(img_uuid_val):
            pass
        else:
            print(f'ERROR: Image "{imgnm}": invalid uuid_validity {img_uuid_val}', file=sys.stderr)
            errors += 1
    #  - hotfix hours (if set!) should be numeric
    if "hotfix_hours" in img.properties:
        if not img.properties["hotfix_hours"].isdecimal():
            print(f'ERROR: Image "{imgnm}" has non-numeric hotfix_hours set', file=sys.stderr)
            errors += 1
    # (5a) Sanity: Are we actually in violation of replace_frequency?
    #  This is a bit tricky: We need to disregard images that have been rotated out
    #  - os_hidden = True is a safe sign for this
    #  - A name with a date stamp or old or prev (and a newer exists)
    outd = is_outdated(img, bdate)
    if outd == 3:
        errors += 1
    elif outd:
        OUTDATED_IMAGES.append(imgnm)
        warnings += (outd-1)
    # (2) sanity min_ram (>=64), min_disk (>= size)
    if img.min_ram < 64:
        print(f'WARNING: Image "{imgnm}": min_ram == {img.min_ram} MB', file=sys.stderr)
        warnings += 1
        # errors += 1
    if img.min_disk < img.size/1073741824:
        print(f'WARNING: Image "{imgnm}" has img size of {img.size/1048576}MiB, but min_disk {img.min_disk*1024}MiB',
              file=sys.stderr)
        warnings += 1
        # errors += 1
    # (6) tags os:*, managed_by_*
    # Nothing to do here ... we could do a warning if those are missing ...

    # (7) Recommended naming
    if imgnm[:len(constr_name)].casefold() != constr_name.casefold():  # and verbose
        rec_name = recommended_name(constr_name)
        print(f'WARNING: Image "{imgnm}" does not start with recommended name "{rec_name}"',
              file=sys.stderr)
        warnings += 1

    if not errors and verbose:
        print(f'Image "{imgnm}": All good ({warnings} warnings)')
    return errors


def report_stdimage_coverage(imgs):
    "Have we covered all standard images?"
    err = 0
    for inm in mand_images:
        if inm not in imgs:
            err += 1
            print(f'WARNING: Mandatory image "{inm}" is missing', file=sys.stderr)
    for inm in (*rec1_images, *rec2_images):
        if inm not in imgs:
            print(f'INFO: Recommended image "{inm}" is missing', file=sys.stderr)
    # Ignore sugg_images for now
    return err


def miss_replacement_images(by_name, outd_list):
    """Go over list of images to find replacement imgs for outd_list, return the ones that are left missing"""
    rem_list = []
    for outd in outd_list:
        img = None
        shortnm = outd.rsplit(" ", 1)[0]
        if shortnm != outd:
            img = by_name.get(shortnm)
        if img is not None:
            bdate = 0
            if "build_date" in img.properties:
                bdate = parse_date(img.properties["build_date"])
            if not bdate:
                bdate = parse_date(img.created_at, formats=STRICT_FORMATS)
            if is_outdated(img, bdate):
                img = None
        if img is None:
            rem_list.append(outd)
        elif verbose:
            print(f'INFO: Image "{img.name}" is a valid replacement for outdated "{outd}"', file=sys.stderr)
    return rem_list


def main(argv):
    "Main entry point"
    # Option parsing
    global verbose, private, skip
    cloud = os.environ.get("OS_CLOUD")
    err = 0
    try:
        opts, args = getopt.gnu_getopt(argv[1:], "phvc:s",
                                       ("private", "help", "os-cloud=", "verbose", "skip-completeness"))
    except getopt.GetoptError:  # as exc:
        print("CRITICAL: Command-line syntax error", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-p" or opt[0] == "--private":
            private = True
        elif opt[0] == "-v" or opt[0] == "--verbose":
            verbose = True
        elif opt[0] == "-s" or opt[0] == "--skip-completeness":
            skip = True
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
    images = args
    if not cloud:
        print("CRITICAL: Need to specify --os-cloud or set OS_CLOUD environment.", file=sys.stderr)
        usage(1)
    try:
        conn = openstack.connect(cloud=cloud, timeout=24)
        all_images = list(conn.image.images())
        by_name = {img.name: img for img in all_images}
        if len(by_name) != len(all_images):
            print(f'WARNING: duplicate names detected', file=sys.stderr)
        if not images:
            images = [img.name for img in all_images if private or img.visibility == 'public']
        # Analyse image metadata
        for imgnm in images:
            err += validate_imageMD(by_name[imgnm])
        if not skip:
            err += report_stdimage_coverage(images)
        if OUTDATED_IMAGES:
            if verbose:
                print(f'INFO: The following outdated images have been detected: {OUTDATED_IMAGES}',
                      file=sys.stderr)
            rem_list = miss_replacement_images(images, OUTDATED_IMAGES)
            if rem_list:
                print(f'ERROR: Outdated images without replacement: {rem_list}', file=sys.stderr)
                err += len(rem_list)
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}")
        return 1 + err
    return err


if __name__ == "__main__":
    sys.exit(main(sys.argv))
