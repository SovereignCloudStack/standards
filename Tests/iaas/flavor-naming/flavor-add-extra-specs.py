#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
"""
flavor-add-extra-specs.py

Cycles through all SCS- openstack flavors and adds properties specified in
scs-0103-v1 <https://docs.scs.community/standards/scs-0103-v1-standard-flavors>.

Usage: flavor-add-extra-specs.py [options] [FLAVORS]
Options:
    -h|--help:  Print usage information
    -d|--debug: Output verbose debugging info
    -q|--quiet: Don't output notes on changes performed
    -t|--disk0-type TYPE:   Assumes disk TYPE for flavors w/ unspec disk0-type
    -p|--cpu-type TYPE:     Assumes CPU TYPE for flavors w/o SCS name
    -c|--os-cloud CLOUD:    Cloud to work on (default: OS_CLOUD env)
    -n|--no-changes:        Do not perform any change
By default, all SCS- flavors are processed; by passing flavor names FLAVORS as
arguments, only those are processed.
You can pass non-SCS FLAVORS and specify --cpu-type to generate SCS names and
set the SCS extra_specs.

On most clouds, to add properties (extra_specs) to flavors, you need to have
admin power; this program will otherwise report the failed settings.
You can can use this for testing, better use =n|--no-change.
Add -d|--debug for more verbose output.

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import os
import sys
import getopt
import openstack

from flavor_names import parser_v2, parser_v1, SyntaxV1, SyntaxV2, CPUTYPE_KEY, DISKTYPE_KEY
from flavor_names import Flavorname, Main, Disk, outname

# globals
DEBUG = False
QUIET = False
NOCHANGE = False


def usage(out):
    "Output usage information (help)"
    print(__doc__, file=sys.stderr)
    sys.exit(out)


def min_max_check(real, claim, valnm, flvnm, extra):
    """Check whether property valnm real is at least claim.
       Prints ERROR is lower and returns False
       Prints WARNING if higher (and returns True)
       Returns True if no problem detected.
       For floats, we allow for 1% tolerance in both directions.
       """
    # 1% tolerance for floats (RAM)
    if isinstance(claim, float):
        chkval = real*1.01
        chkval2 = real*0.99
    else:
        chkval = real
        chkval2 = real
    if chkval < claim:
        print(f"ERROR: Flavor {flvnm} claims {claim} {valnm}{extra}, but only has {real}. Needs fixing.",
              file=sys.stderr)
        return False
    if chkval2 > claim:
        print(f"WARNING: Flavor {flvnm} claims {claim} {valnm}{extra}, but overdelivers with {real}.",
              file=sys.stderr)
    return True


def check_std_props(flavor, flvnm, extra=""):
    """Check consistency of openstack props with parsed SCS name specs
    Return no of errors found."""
    errors = 0
    #  vcpus
    if not min_max_check(flavor.vcpus, flvnm.cpuram.cpus, "CPUs", flavor.name, extra):
        errors += 1
    #  ram
    if not min_max_check(flavor.ram, flvnm.cpuram.ram*1024, "MiB RAM", flavor.name, extra):
        errors += 1
    #  disk
    disksz = 0
    if flvnm.disk:
        disksz = flvnm.disk.disksize
    if not min_max_check(flavor.disk, disksz, "GiB Disk", flavor.name, extra):
        errors += 1
    return errors


def generate_name_v2(flavor, cpu_type, disk0_type):
    """Generate an SCS- v2 name for flavor,
    using cpu_type (and disk0_type if needed).
    Returns string."""
    cpuram = Main()
    cpuram.cpus = flavor.vcpus
    cpuram.cputype = cpu_type
    cpuram.ram = int((flavor.ram+12)/512)/2.0
    if flavor.disk:
        disk = Disk()
        disk.disksize = flavor.disk
        disk.disktype = disk0_type
        flv = Flavorname(cpuram, disk)
    else:
        flv = Flavorname(cpuram)
    return outname(flv)


def check_name_extra(flavor, ver, match, flname):
    """Check for existence and consistency of scs names in extra specs
    This assumes that a v1 or v2 name is used as main flavor name and should
    match. If match is not set an v1->v2 or v2->v1 translation is needed.
    ver needs to be set to 'v1' or 'v2'/'v3'/'v4'
    flname is the SCS flavor name (may have been generated)
    Returns non-zero if we need to perform an API call to perform a change.
    """
    spec = f"scs:name-{ver}"
    errs = 0
    need_name_set = True
    if spec in flavor.extra_specs:
        # Get name from scs:name-vN property
        name = flavor.extra_specs[spec]
        # If match=True has been passed, we expect it to match flname
        # produces a warning on mismatch
        if match and name != flname:
            print(f"WARNING: {spec} {name} != flavor name {flname}",
                  file=sys.stderr)
        # Existing names must be parseable SCS names, check
        # If we can parse the name AND there is no inconsistency
        # we don't need to update the name.
        try:
            parsed = parser_v2(name)
        except ValueError as exc:
            try:
                parsed = parser_v1(name)
            except ValueError as exc2:
                print(f"ERROR parsing {spec} {name}: {exc!r} {exc2!r}",
                      file=sys.stderr)
                need_name_set = False
        # Check consistency
        if need_name_set and not check_std_props(flavor, parsed, f" by {spec}"):
            need_name_set = False

    # FIXME: name might contain more details than the flname, use them
    # TODO: determine whether we want to generate additional names in that case
    # e.g.: scs:name-v1 -> detailed v1 name, -v2: detailed v2 name,
    #               -v3 -> shortened v1 name (if different), -v4 shortened v2 name (if ...)
    if need_name_set:
        errs += 1
        if match:
            flavor.extra_specs[spec] = flname
        else:
            if ver == "v1":
                flavor.extra_specs[spec] = SyntaxV1.from_v2(flname)
            else:
                flavor.extra_specs[spec] = SyntaxV2.from_v1(flname)
        # flavor.update_extra_specs_property(spec, flavor.extra_specs[spec])
        if not QUIET:
            print(f"INFO  {flavor.name}: Update extra_spec {spec} to {flavor.extra_specs[spec]}")

    # FIXME: Spec 0103 has changed, no point in creating additional literal copies
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
    if NOCHANGE:
        if DEBUG:
            if prop in flavor.extra_specs and flavor.extra_specs[prop]:
                print(f"DEBUG {flavor.name}: Would set property {prop} to {flavor.extra_specs[prop]}",
                      file=sys.stderr)
            else:
                print(f"DEBUG {flavor.name}: Would delete property {prop}",
                      file=sys.stderr)
        return 0
    try:
        if prop in flavor.extra_specs and flavor.extra_specs[prop]:
            flavor.update_extra_specs_property(compute, prop,
                                               flavor.extra_specs[prop])
        else:
            flavor.delete_extra_specs_property(compute, prop)
            if prop in flavor.extra_specs:
                del flavor.extra_specs[prop]
        return 0
    except openstack.exceptions.SDKException as exc:
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
    if not QUIET:
        print(f"INFO  {flavor.name}: Update extra_spec {spec} to {flavor.extra_specs[spec]}")
    return 1


def main(argv):
    "Entry point"
    global DEBUG, QUIET, NOCHANGE
    errors = 0
    disk0_type = None
    cpu_type = None

    cloud = os.environ.get("OS_CLOUD")
    try:
        opts, flvs = getopt.gnu_getopt(argv, "hdqt:p:c:n",
                                       ("help", "debug", "quiet", "disk0-type=",
                                        "cpu-type=", "os-cloud=", "no-change"))
    except getopt.GetoptError as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        if opt[0] == "-d" or opt[0] == "--debug":
            DEBUG = True
        if opt[0] == "-q" or opt[0] == "--quiet":
            QUIET = True
        if opt[0] == "-n" or opt[0] == "--no-change":
            NOCHANGE = True
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-t" or opt[0] == "--disk0-type":
            disk0_type = opt[1]
            if disk0_type not in DISKTYPE_KEY:
                disk0_type = revert_dict(disk0_type, DISKTYPE_KEY)
                if not disk0_type:
                    return 2
        if opt[0] == "-p" or opt[0] == "--cpu-type":
            cpu_type = opt[1]
            if cpu_type not in CPUTYPE_KEY:
                cpu_type = revert_dict(cpu_type, CPUTYPE_KEY)
                if not cpu_type:
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
        if flvs and flavor.name not in flvs:
            continue
        flname = flavor.name
        if flname[0:4] != "SCS-":
            if not flvs:
                continue
            # Set flname by looking at extra_spec scs:name-v2
            if "scs:name-v2" in flavor.extra_specs:
                flname = flavor.extra_specs["scs:name-v2"]
            else:
                # In generation case, we'd need a cpu-type spec
                if not cpu_type:
                    print(f"WARNING: Need to specify cpu-type for generating name for {flname}, skipping",
                          file=sys.stderr)
                    continue
                flname = generate_name_v2(flavor, cpu_type, disk0_type)
        if DEBUG:
            print(f"DEBUG: Inspecting flavor {flavor.name}/{flname} ...")
        try:
            flvnm = parser_v2(flname)
        except ValueError as exc:
            try:
                flvnm = parser_v1(flname)
                is_v1 = True
            except ValueError:
                print(f"ERROR with flavor {flavor.name}: {exc!r}, skipping ...",
                      file=sys.stderr)
                errors += 1
                continue

        # Now do sanity checks (std properties)
        stderrs = check_std_props(flavor, flvnm, " by name")
        errors += stderrs
        if stderrs:
            continue

        # Parse and Generate name-v1 and name-v2
        upd = check_name_extra(flavor, "v2", not is_v1, flname)
        if upd:
            errors += update_flavor_extra(compute, flavor, "scs:name-v2")
        upd = check_name_extra(flavor, "v1", is_v1, flname)
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
