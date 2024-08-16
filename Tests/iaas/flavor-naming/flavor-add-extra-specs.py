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

import getopt
import logging
import os
import re
import sys

from flavor_names import parser_vN, CPUTYPE_KEY, DISKTYPE_KEY, Flavorname, Main, Disk, flavorname_to_dict

import openstack


logger = logging.getLogger(__name__)
scs_name_pattern = re.compile(r"scs:name-v\d+\Z")
DEFAULTS = {'scs:disk0-type': 'network'}

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


def generate_flavorname(flavor, cpu_type, disk0_type):
    """Generate an SCS- v2 name for flavor,
    using cpu_type (and disk0_type if needed).
    Returns string."""
    cpuram = Main()
    cpuram.cpus = flavor.vcpus
    cpuram.cputype = cpu_type
    cpuram.ram = int((flavor.ram+12)/512)/2.0
    flavorname = Flavorname(main)
    if flavor.disk:
        disk = Disk()
        disk.disksize = flavor.disk
        disk.disktype = disk0_type
        flavorname.disk = disk
    return flavorname


def revert_dict(value, dct, extra=""):
    "Return key that matches val, None if no match"
    for key, val in dct.items():
        if val == value:
            return key
    print(f"ERROR: {extra} {value} should be in {dct.items()}",
          file=sys.stderr)
    return None


def _extract_core_items(flavorname: Flavorname):
    cputype = flavorname.cpuram.cputype
    disktype = None if flavorname.disk is None else flavorname.disk.disktype
    return cputype, disktype


def _extract_core(flavorname: Flavorname):
    cputype, disktype = _extract_core_items(flavorname)
    return f"cputype={cputype}, disktype={disktype}"


def main(argv):
    "Entry point"
    global DEBUG, QUIET, NOCHANGE
    errors = 0
    chg = 0
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
            logging.getLogger().setLevel(logging.DEBUG)
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

    # select relevant flavors: either given via name, or all SCS flavors
    predicate = (lambda fn: fn in flvs) if flvs else (lambda fn: fn.startswith('SCS-'))
    flavors = [flavor for flavor in compute.flavors() if predicate(flavor.name)]
    # This is likely a user error, so make them aware
    if len(flavors) < len(flvs):
        missing = set(flvs) - set(flavor.name for flavor in flavors)
        logger.warning("Flavors not found: " + ", ".join(missing))

    for flavor in flavors:
        extra_names_to_check = [
            (key, value)
            for key, value in flavor.extra_specs.items()
            if scs_name_pattern.match(key)
        ]
        names_to_check = [('name', flavor.name)] if flavor.name.startswith('SCS-') else []
        names_to_check.extend(extra_names_to_check)

        # syntax check: compute flavorname instances
        flavornames = {}
        for key, name_str in names_to_check:
            try:
                flavornames[key] = parser_vN(name_str)
            except ValueError as exc:
                logger.error(f"could not parse {key}={name_str}: {exc!r}")
                errors += 1

        # select a reference flavorname, check flavornames
        if flavornames:
            flavorname_items = iter(flavornames.items())
            reference_key, reference = next(flavorname_items)
            reference_core = _extract_core(reference)
            # sanity check: claims must be true wrt actual flavor
            errors += check_std_props(flavor, reference, " by name")
            # sanity check: claims must coincide (check remaining flavornames)
            for key, flavorname in flavorname_items:
                errors += check_std_props(flavor, flavorname, " by name")
                core = _extract_core(flavorname)
                if core != reference_core:
                    logger.error(f"Inconsistent {key} vs. {reference_key}: {core} vs. {reference_core}")
        else:
            # we need cputype and disktype from user
            if not cpu_type:
                logger.warning(f"Need to specify cpu-type for generating name for {flavor.name}, skipping")
                continue
            if flavor.disk and not disk0_type:
                logger.warning(f"Need to specify disk0-type for generating name for {flavor.name}, skipping")
                continue
            reference_key = None
            reference = generate_flavorname(flavor, cpu_type, disk0_type)

        expected = flavorname_to_dict(reference)
        # set value for any unexpected, but present key to default value
        # this will help us find necessary removals
        for key in flavor.extra_specs:
            expected.setdefault(key, DEFAULTS.get(key))

        # generate default name-vN (ONLY if none present)
        if not extra_names_to_check:
            for key, value in expected.items():
                if not key.startswith("scs:name-v"):
                    continue
                # TODO do the API call
                logger.debug(f"{flavor.name}: SET {key}={value}")
                chg += 1

        # generate or rectify other extra_specs
        for key, value in expected.items():
            if key.startswith("scs:name-v") or not key.startswith("scs:"):
                continue
            current = flavor.extra_specs.get(key, DEFAULTS.get(key))
            if current == value:
                continue
            if current is not None:
                logger.warning(f"resetting {key} because {current} != expected {value}")
            if value is None:
                # TODO do the API call
                logger.debug(f"{flavor.name}: DELETE {key}")
            else:
                # TODO do the API call
                logger.debug(f"{flavor.name}: SET {key}={value}")
            chg += 1

    if (DEBUG):
        print(f"DEBUG: Processed {len(flavors)} flavors, {chg} changes")
    return errors


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    sys.exit(main(sys.argv[1:]))
