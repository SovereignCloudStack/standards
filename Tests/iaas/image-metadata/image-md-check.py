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
conn = None
if "OS_CLOUD" in os.environ:
    cloud = os.environ["OS_CLOUD"]
else:
    cloud = None

# Image list
mand_images = ["Ubuntu 22.04", "Ubuntu 20.04", "Debian 11"]
rec1_images = ["CentOS 8", "Rocky 8", "AlmaLinux 8", "Debian 10", "Fedora 36"]
rec2_images = ["SLES 15SP4", "RHEL 9", "RHEL 8", "Windows Server 2022", "Windows Server 2019"]
sugg_images = ["openSUSE Leap 15.4", "Cirros 0.5.2", "Alpine", "Arch"]


def get_imagelist(priv):
    "Retrieve list of public images (optionally also private images)"
    if priv:
        imgs = conn.image.images()
    else:
        imgs = conn.image.images(visibility='public')
    return list(map(lambda x: x.name, imgs))


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
                    print(f'Error: Image "{warn}": value "{props[self.name]}" for property '
                          f'"{self.name}" not allowed', file=sys.stderr)
                return False
            else:
                if not props[self.name] and not self.values:
                    err = "Error"
                    ret = False
                else:
                    err = "Warning"
                    ret = True
                if not props[self.name] and (verbose or not self.values) and warn:
                    print(f'{err}: Image "{warn}": empty value for property "{self.name}" not recommended',
                          file=sys.stderr)
                return ret
        elif self.ismand:
            if warn:
                print(f'Error: Image "{warn}": Mandatory property "{self.name}" is missing',
                      file=sys.stderr)
            return False
        elif warn and verbose:
            print(f'Info: Image "{warn}": Optional property "{self.name}" is missing')  # , file=sys.stderr)
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
    "Is string stg an URL?"
    idx = stg.find("://")
    if idx < 0:
        return False
    if stg[:idx] in ("http", "https", "ftp", "ftps"):
        return True
    return False


def validate_imageMD(imgnm):
    "Retrieve image properties and test for compliance with spec"
    try:
        img = conn.image.find_image(imgnm)
    except openstack.exceptions.DuplicateResource as exc:
        print(f'Error with duplicate name "{imgnm}": {str(exc)}', file=sys.stderr)
        return 1
    if not img:
        print(f'Image "{imgnm}" not found' % imgnm, file=sys.stderr)
        return 1
    # Now the hard work: Look at properties ....
    errors = 0
    # (1) recommended os_* and hw_*
    for prop in (*os_props, *arch_props, *hw_props):
        if not prop.is_ok(img, imgnm):
            errors += 1
    constr_name = f"{img.os_distro} {img.os_version}"
    # (3) os_hash
    if img.hash_algo not in ('sha256', 'sha512'):
        print(f'Error: Image "{imgnm}": no valid hash algorithm {img.hash_algo}', file=sys.stderr)
        errors += 1

    # (4) image_build_date, image_original_user, image_source (opt image_description)
    # (5) maintained_until, provided_until, uuid_validity, update_frequency
    for prop in (*build_props, *maint_props):
        if not prop.is_ok(img.properties, imgnm):
            errors += 1
    # TODO: Some more sanity checks:
    #  - Dateformat for image_build_date
    bdate = time.strptime(img.created_at, "%Y-%m-%dT%H:%M:%SZ")
    if "image_build_date" in img.properties:
        try:
            bdate = time.strptime(img.properties["image_build_date"][:10], "%Y-%m-%d")
            # This never evals to True, but makes bdate used for flake8
            if verbose and False:
                print(f'Info: Image "{imgnm}" with build date {bdate}')
        except Exception:
            print(f'Error: Image "{imgnm}": no valid image_build_date '
                  f'{img.properties["image_build_date"]}', file=sys.stderr)
            errors += 1
    # - image_source should be an URL
    if "image_source" in img.properties:
        if not is_url(img.properties["image_source"]):
            print(f'Error: Image "{imgnm}": image_source should be an URL', file=sys.stderr)
    #  - uuid_validity has a distinct set of options (none, last-X, DATE, notice, forever)
    #  - hotfix hours (if set!) should be numeric
    # (5a) Sanity: Are we actually in violation of update_frquency?
    #  This is a bit tricky: We need to disregard images that have been rotated out
    #  - os_hidden = True is a safe sign for this
    #  - A name with a date stamp or old or prev (and a newer exists)
    # (2) sanity min_ram (>=64), min_disk (>= size)
    # (6) tags os:*, managed_by_*
    #
    # (7) Recommended naming
    if verbose and imgnm[:len(constr_name)].casefold() != constr_name.casefold():
        print(f'Warning: Image "{imgnm}" does not start with recommended name "{constr_name}"',
              file=sys.stderr)

    if not errors and verbose:
        print(f'Image "{imgnm}": All good')
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


def main(argv):
    "Main entry point"
    # Option parsing
    global verbose, private, skip
    global cloud, conn
    try:
        opts, args = getopt.gnu_getopt(argv[1:], "phvc:s",
                                       ("private", "help", "os-cloud=", "verbose", "skip-completeness"))
    except getopt.GetoptError:  # as exc:
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
        print("ERROR: Need to specify --os-cloud or set OS_CLOUD environment.", file=sys.stderr)
        usage(1)
    conn = openstack.connect(cloud=cloud, timeout=24)
    # Do work
    if not images:
        images = get_imagelist(private)
    err = 0
    # Analyse image metadata
    for image in images:
        err += validate_imageMD(image)
    if not skip:
        err += report_stdimage_coverage(images)
    return err


if __name__ == "__main__":
    sys.exit(main(sys.argv))
