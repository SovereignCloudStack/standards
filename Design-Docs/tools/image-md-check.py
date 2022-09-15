#!/usr/bin/python3
#
# SCS/Docs/tools/image-md-check.py
#
# Retrieve metadata from (public) images and check for compliance
# with SCS specifications.
#
# (c) Kurt Garloff <kurt@garloff.de>, 09/2022
# SPDX-License-Identifier: CC-BY-SA-4.0

import os, sys, getopt
import openstack

def usage(rc):
    print("Usage: image-md-check.py [options] [images]")
    print("image-md-check.py will create a report on public images by retrieving")
    print(" the image metadata (properties) and comparing this against the image")
    print(" metadata spec from SCS.")
    print("Options: --os-cloud CLOUDNAME: Use this cloud config, default is $OS_CLOUD")
    print(" -p/--private : Also consider private images")
    print(" -v/--verbose : Be more verbose")
    print(" -s/--skip-completeness: Don't check whether we have all mandatory images")
    print(" -h/--help    : Print this usage information")
    print("If you pass images, only these will be validated, otherwise all images")
    print(" catalog will be processed.")
    sys.exit(rc)

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
rec1_images = ["CentOS 8", "Rocky 8", "Alma Linux 8", "Debian 10", "Fedora 36"]
rec2_images = ["SLES 15SP4", "RHEL 9", "RHEL 8", "Windows Server 2022", "Windows Server 2019"]
sugg_images = ["openSUSE Leap 15.4", "Cirros 0.5.2", "Alpine", "Arch"]

def get_imagelist(priv):
    if priv:
        imgs = conn.image.images()
    else:
        imgs = conn.image.images(visibility='public')
    return list(map(lambda x: x.name, imgs))

class property:
    def __init__(self, name, mand, values, desc):
        self.name = name
        self.ismand = mand
        self.values = values
        self.desc = desc
    def is_ok(self, props, warn = ""):
        if self.name in props:
            if self.values and not props[self.name] in self.values:
                if warn:
                    print("Error: Image \"%s\": value \"%s\" for property \"%s\" not in list" % \
                            (warn, props[self.name], self.name))
                return False
            else:
                return True
        elif self.ismand:
            if warn:
                print("Error: Image \"%s\": Mandatory property \"%s\" is missing" % \
                        (warn, self.name))
            return False
        elif warn:
            print("Info: Image \"%s\": Recommended property \"%s\" is missing" % \
                    (warn, self.name))
        return True

os_props = (property("os_distro", True, (), "Operating System"),
            property("os_version", True, (), "OS Versions"))
arch_props = (property("architecture", True, ("x86_64", "aarch64", "risc-v"), "CPU architecture"),
              property("hypervisor_type", True, ("kvm", "xen", "hyper-v", "esxi"), "Hypervisor"))
hw_props = (property("hw_rng_model", False, ("virtio",), "Random Number Generator"),
            property("hw_disk_bus", True, ("virtio", "scsi"), "Disk bus: vda or sda"))


def validate_imageMD(imgnm):
    try:
        img = conn.image.find_image(imgnm)
    except openstack.exceptions.DuplicateResource as exc:
        print("Error with duplicate name \"%s\": %s" % (imgnm, str(exc)), file=sys.stderr)
        return 1
    # Now the hard work: Look at properties ....
    errors = 0
    for prop in (*os_props, *arch_props, *hw_props):
        if not prop.is_ok(img, imgnm):
            errors += 1

    #(1) recommended os_* and hw_*
    #(2) sanity architecture, min_ram, min_disk (vs size)
    #(3) os_hash
    #(4) image_build_date, image_original_user, image_source (opt image_description)
    #(5) maintained_until, provided_until, uuid_validity, update_frequency
    #(5a) Sanity: Are we actually in violation of update_frquency?
    #(6) tags os:*, managed_by_*
    if not errors and verbose:
        print("Image \"%s\": All good" % imgnm)
    return errors

def report_stdimage_coverage(imgs):
    err = 0
    for inm in mand_images:
        if inm not in imgs:
            err += 1
            print("WARNING: Mandatory image \"%s\" is missing" % inm)
    for inm in (*rec1_images, *rec2_images):
        if inm not in imgs:
            print("INFO: Recommended image \"%s\" is missing" % inm)
    # Ignore sugg_images for now
    return err

def main(argv):
    # Option parsing
    global verbose, private, skip
    global cloud, conn
    try:
        opts, args = getopt.gnu_getopt(argv[1:], "phvc:s", \
           ("private", "help", "os-cloud=", "verbose", "skip-completeness"))
    except getopt.GetoptError as exc:
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
