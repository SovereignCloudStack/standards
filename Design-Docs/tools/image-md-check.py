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
    print(" -h/--help    : Print this usage information")
    print("If you pass images, only these will be validated, otherwise all images")
    print(" catalog will be processed.")
    sys.exit(rc)

# global options
verbose = False
private = False

# Image list
mand_images = ["Ubuntu 22.04", "Ubuntu 20.04", "Debian 11"]
rec1_images = ["CentOS 8", "Rocky 8", "Alma Linux 8", "Debian 10", "Fedora 36"]
rec2_images = ["SLES 15SP4", "RHEL 9", "RHEL 8", "Windows Server 2022", "Windows Server 2019"]
sugg_images = ["openSUSE Leap 15.4", "Cirros", "Alpine", "Arch"]

def get_imagelist(priv):
    return []

def validate_imageMD(imgnm):
    return 0

def report_stdimage_coverage(imgs):
    pass

def main(argv):
    # Option parsing
    global verbose, private
    try:
        opts, args = getopt.gnu_getopt(argv[1:], "phc:", \
		("private", "help", "os-cloud="))
    except getopt.GetoptError as exc:
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-p" or opt[0] == "--private":
            private = True
        elif opt[0] == "-v" or opt[0] == "--verbose":
            verbose = True
    images = args
    # Do work
    if not images:
        images = get_imagelist(private)
    # Analyse image metadata
    for image in images:
        validate_imageMD(image)
    report_stdimage_coverage(images)

if __name__ == "__main__":
    main(sys.argv)
