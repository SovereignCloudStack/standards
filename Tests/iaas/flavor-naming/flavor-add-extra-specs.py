#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
"""
flavor-add-extra-specs.py

Cycles through all openstack flavors and adds metadata specified in
scs-0104-v1 <https://docs.scs.community/standards/scs-0104-v1-standard-images>.

Usage: flavor-add-extra-specs.py [-d|--debug] [-a|--all] [-c|--os-cloud CLOUD] [FLAVORS]
CLOUD defaults to env["OS_CLOUD"], FLAVORS default to all found SCS- flavors.
-t|--disk-type0= allows to set the disk type (default = networked aka n.

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import os
import sys
import getopt
import openstack

from flavor_names import parser_v2, parser_v1, outname, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname, \
    Inputter, lookup_user_input, prettyname, CompatLayer


def usage(out):
    "Output usage information (help)"
    print(__doc__, file=sys.stderr)
    sys.exit(out)


def min_max_check(real, claim, valnm, flvnm):
    """Check whether property valnm real is at least claim.
       Prints ERROR is lower and returns False
       Prints WARNING if higher (and returns True)
       Returns True if no problem detected."""
    # 1% tolerance for floats
    if claim is float:
        chkval = real*1.01
        chkval2 = real*0.99
    else:
        chkval = real
        chkval2 = real
    if chkval < claim:
        print(f"ERROR: Flavor {flvnm} claims {claim} {valnm}, but only has {real}. Skipping ...",
              file=sys.stderr)
        return False
    if chkval2 > claim:
        print(f"WARNING: Flavor {flvnm} claims {claim} {valnm}, but overdelivers with {real}.",
              file=sys.stderr)
    return True


def main(argv):
    "Entry point"
    errors = 0
    cloud = None
    debug = False
    disk_type0 = None

    if "OS_CLOUD" in os.environ:
        cloud = os.environ["OS_CLOUD"]
    try:
        opts, flvs = getopt.gnu_getopt(argv, "dt:c:",
                                       ("debug", "disk-type0=", "os-cloud="))
    except getopt.GetoptError as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-d" or opt[0] == "--debug":
            debug = True
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-t" or opt[0] == "--disk-typo0":
            disk_type0 = opt[1]

    if not cloud:
        print("ERROR: Need to pass -c|--os-cloud|OS_CLOUD env", file=sys.stderr)
        usage(2)

    conn = openstack.connect(cloud)
    conn.authorize()
    compute = conn.compute

    flavors = compute.flavors()
    for flavor in flavors:
        if flvs and flavor not in flvs:
            continue
        if flavor.name[0:4] != "SCS-":
            continue
        if debug:
            print(f"DEBUG: Inspecting flavor {flavor.name} ...")
        try:
            flvnm = parser_v2(flavor.name)
        except ValueError as exc:
            try:
                flvnm = parser_v1(flavor.name)
            except ValueError:
                print(f"ERROR with flavor {flavor.name}: {str(exc)}, skipping ...",
                      file=sys.stderr)
                errors += 1
                continue
        # Now do sanity checks (std properties)
        #  vcpus
        if not min_max_check(flavor.vcpus, flvnm.cpuram.cpus, "CPUs", flavor.name):
            errors += 1
            continue
        #  ram
        if not min_max_check(flavor.ram, flvnm.cpuram.ram*1024, "MiB RAM", flavor.name):
            errors += 1
            continue
        #  disk
        disksz = 0
        if flvnm.disk:
            disksz = flvnm.disk.disksize
        if not min_max_check(flavor.disk, disksz, "GiB Disk", flavor.name):
            errors += 1
            continue

        # Generate namev1 and namev2
        # Generate CPU and disk types


if __name__ == "__main__":
    main(sys.argv[1:])
