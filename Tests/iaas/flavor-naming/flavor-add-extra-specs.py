#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
"""
flavor-add-extra-specs.py

Cycles through all SCS- openstack flavors and adds metadata specified in
scs-0103-v1 <https://docs.scs.community/standards/scs-0103-v1-standard-flavors>.

Usage: flavor-add-extra-specs.py [options] [FLAVORS]
Options:
    -h|--help:  Print usage information
    -d|--debug: Output verbose debugging info
    -t|--disk0-type TYPE:   Assumes disk TYPE for flavors w/ unspec disk0-type
    -c|--os-cloud CLOUD:    Cloud to work on (default: OS_CLOUD env)
By default, all SCS- flavors are processed; by passing flavor names FLAVORS as
arguments, only those are processed.
(Currently, only SCS- flavors are supported; this may be lifted in the future.)

On most clouds, to add properties (extra_specs) to flavors, you need to have
admin power; this program will otherwise report the failed settings. This can
be used for testing, best in conjunction with -d|--debug.

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import os
import sys
import getopt
import openstack

from flavor_names import parser_v2, parser_v1, SyntaxV1, SyntaxV2, CPUTYPE_KEY, DISKTYPE_KEY
# outname, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname,
# Inputter, lookup_user_input, prettyname, CompatLayer

# globals
DEBUG = False


def usage(out):
    "Output usage information (help)"
    print(__doc__, file=sys.stderr)
    sys.exit(out)


def min_max_check(real, claim, valnm, flvnm):
    """Check whether property valnm real is at least claim.
       Prints ERROR is lower and returns False
       Prints WARNING if higher (and returns True)
       Returns True if no problem detected.
       For floats, we allow for 1% tolerance in both directions.
       """
    # 1% tolerance for floats (RAM)
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


def check_name_extra(flavor, ver, match):
    """Check for existence and consistency of scs names in extra specs
    This assumes that a v1 or v2 name is used as main flavor name and should
    match. If match is not set an v1->v2 or v2->v1 translation is neeed.
    ver needs to be set to 'v1' or 'v2'.
    """
    spec = f"scs:name-{ver}"
    errs = 0
    need_name_set = True
    if spec in flavor.extra_specs:
        name = flavor.extra_specs[spec]
        if match and name != flavor.name:
            print(f"WARNING: {spec} {name} != flavor name {flavor.name}",
                  file=sys.stderr)
        # Existing names must be parseable SCS names, check
        try:
            if ver == "v2":
                parser_v2(name)
            else:
                parser_v1(name)
            need_name_set = False
        except ValueError as exc:
            print(f"ERROR parsing {spec} {name}: {exc!r}",
                  file=sys.stderr)
        # To Do: Check consistency
    if need_name_set:
        errs += 1
        if match:
            flavor.extra_specs[spec] = flavor.name
        else:
            if ver == "v2":
                flavor.extra_specs[spec] = SyntaxV2.from_v1(flavor.name)
            else:
                flavor.extra_specs[spec] = SyntaxV1.from_v2(flavor.name)
        # flavor.update_extra_specs_property(spec, flavor.extra_specs[spec])
        if DEBUG:
            print(f"DEBUG: Update extra_spec {spec} to {flavor.extra_specs[spec]}")
    return errs


def revert_dict(value, dct, extra=""):
    "Return key that matches val, None if no match"
    for key, val in dct.items():
        if val == value:
            return key
    print(f"ERROR: {extra} {value} should be in {dct.items()}",
          file=sys.stderr)
    return None


def update_flavor_extra(compute, flavor, prop):
    """Update flavor extra_spec property prop with the value in the
    dict flavor.extra_specs[prop]. Delete the property if it is None.
    Return 1 if there was an error."""
    try:
        if prop in flavor.extra_specs and flavor.extra_specs[prop]:
            flavor.update_extra_specs_property(compute, prop,
                                               flavor.extra_specs[prop])
        else:
            flavor.delete_extra_specs_property(compute, prop)
            if prop in flavor.extra_specs:
                del flavor.extra_specs[prop]
        return 0
    except openstack.exceptions.ForbiddenException as exc:
        print(f"ERROR: Could not set {prop} for {flavor.name}: {exc!r}",
              file=sys.stderr)
        return 1


def check_extra_type(flavor, prop, val, dct):
    """Check extra_specs['scs:prop'] for flavor
    It should be set and consistent with val, translated with dct.
    Returns 1 is the extra_spec needs to change"""
    spec = f"scs:{prop}"
    if val:
        expected = dct[val]
    else:
        expected = None
    if spec in flavor.extra_specs:
        setting = flavor.extra_specs[spec]
        if setting != expected:
            print(f"ERROR: flavor {flavor.name} has {spec} set to {setting}, expect {expected}",
                  file=sys.stderr)
        else:
            return 0
    elif not expected:
        return 0
    flavor.extra_specs[spec] = expected
    if DEBUG:
        print(f"DEBUG: Update extra_spec {spec} to {flavor.extra_specs[spec]}")
    return 1


def main(argv):
    "Entry point"
    global DEBUG
    errors = 0
    cloud = None
    disk0_type = None

    if "OS_CLOUD" in os.environ:
        cloud = os.environ["OS_CLOUD"]
    try:
        opts, flvs = getopt.gnu_getopt(argv, "hdt:c:",
                                       ("help", "debug", "disk0-type=", "os-cloud="))
    except getopt.GetoptError as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        if opt[0] == "-d" or opt[0] == "--debug":
            DEBUG = True
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-t" or opt[0] == "--disk0-type":
            disk0_type = opt[1]
            if disk0_type not in DISKTYPE_KEY:
                disk0_type = revert_dict(disk0_type, DISKTYPE_KEY)
                if not disk0_type:
                    return 2

    if not cloud:
        print("ERROR: Need to pass -c|--os-cloud|OS_CLOUD env", file=sys.stderr)
        usage(3)

    conn = openstack.connect(cloud)
    conn.authorize()
    compute = conn.compute

    flavors = compute.flavors()
    for flavor in flavors:
        is_v1 = False
        if flvs and flavor not in flvs:
            continue
        if flavor.name[0:4] != "SCS-":
            continue
        if DEBUG:
            print(f"DEBUG: Inspecting flavor {flavor.name} ...")
        try:
            flvnm = parser_v2(flavor.name)
        except ValueError as exc:
            try:
                flvnm = parser_v1(flavor.name)
                is_v1 = True
            except ValueError:
                print(f"ERROR with flavor {flavor.name}: {exc!r}, skipping ...",
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

        # Parse and Generate name-v1 and name-v2
        upd = check_name_extra(flavor, "v2", not is_v1)
        if upd:
            errors += update_flavor_extra(compute, flavor, "scs:name-v2")
        upd = check_name_extra(flavor, "v1", is_v1)
        if upd:
            errors += update_flavor_extra(compute, flavor, "scs:name-v1")
        # Parse and Generate cpu-type and disk0-type
        upd = check_extra_type(flavor, "cpu-type", flvnm.cpuram.cputype, CPUTYPE_KEY)
        if upd:
            errors += update_flavor_extra(compute, flavor, "scs:cpu-type")

        # We may not have a disk (or the type is unknown)
        if flvnm.disk:
            dtp = flvnm.disk.disktype
            if not dtp:
                dtp = disk0_type
        else:
            dtp = None
        upd = check_extra_type(flavor, "disk0-type", dtp, DISKTYPE_KEY)
        if upd:
            errors += update_flavor_extra(compute, flavor, "scs:disk0-type")

    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
