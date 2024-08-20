#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
"""
flavor-add-extra-specs.py

Cycles through all SCS- openstack flavors and adds properties specified in
scs-0103-v1 <https://docs.scs.community/standards/scs-0103-v1-standard-flavors>.

Usage: flavor-add-extra-specs.py [options] [FLAVORS]
Options:
    -h|--help:   Print usage information
    -d|--debug:  Output verbose debugging info
    -q|--quiet:  Only output warnings and errors
    -A|--all-names:         Overwrite scs:name-vN with systematic names
                            (name-v1 and -v2 will be overwritten,
                             often also -v3 and -v4)
    -t|--disk0-type TYPE:   Assumes disk TYPE for flavors w/ unspec disk0-type
    -p|--cpu-type TYPE:     Assumes CPU TYPE for flavors w/o SCS name
    -c|--os-cloud CLOUD:    Cloud to work on (default: OS_CLOUD env)
    -a|--action ACTION:     What action to perform:
        report:  only report what changes would be performed
        ask:     (default) report, then ask whether to perform
        apply:   perform changes without asking

By default, all SCS- flavors are processed; by passing flavor names FLAVORS as
arguments, only those are processed.
You can pass non-SCS FLAVORS and specify --cpu-type to generate SCS names and
set the SCS extra_specs.

On most clouds, to add properties (extra_specs) to flavors, you need to have
admin power; this program will otherwise report the failed settings.
Add -d|--debug for more verbose output.

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2024
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 8/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import getopt
import logging
import os
import sys

import openstack

from flavor_names import parser_vN, CPUTYPE_KEY, DISKTYPE_KEY, Flavorname, Main, Disk, flavorname_to_dict, \
    SCS_NAME_PATTERN


logger = logging.getLogger(__name__)
DEFAULTS = {'scs:disk0-type': 'network'}


def usage(file=sys.stderr):
    "Output usage information (help)"
    print(__doc__.strip(), file=file)


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
        logger.error(f"Flavor {flvnm} claims {claim} {valnm}{extra}, but only has {real}. Needs fixing.")
        return False
    if chkval2 > claim:
        logger.warning(f"Flavor {flvnm} claims {claim} {valnm}{extra}, but overdelivers with {real}.")
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
    logger.error(f"ERROR: {extra} {value} should be in {dct.items()}")


def _extract_core_items(flavorname: Flavorname):
    cputype = flavorname.cpuram.cputype
    disktype = None if flavorname.disk is None else flavorname.disk.disktype
    return cputype, disktype


def _extract_core(flavorname: Flavorname):
    cputype, disktype = _extract_core_items(flavorname)
    return f"cputype={cputype}, disktype={disktype}"


class ActionReport:
    @staticmethod
    def set_extra_spec(flavor, key, value):
        print(f'Flavor {flavor.name}: SET {key}={value}')

    @staticmethod
    def del_extra_spec(flavor, key):
        print(f'Flavor {flavor.name}: DELETE {key}')


class ActionApply:
    def __init__(self, compute):
        self.compute = compute

    def set_extra_spec(self, flavor, key, value):
        logger.info(f'Flavor {flavor.name}: SET {key}={value}')
        try:
            flavor.update_extra_specs_property(self.compute, key, value)
        except openstack.exceptions.SDKException as exc:
            logger.error(f"{exc!r} while setting {key}={value} for {flavor.name}")

    def del_extra_spec(self, flavor, key):
        logger.info(f'Flavor {flavor.name}: DELETE {key}')
        try:
            flavor.delete_extra_specs_property(self.compute, key)
        except openstack.exceptions.SDKException as exc:
            logger.error(f"{exc!r} while deleting {key} for {flavor.name}")


class SetCommand:
    def __init__(self, flavor, key, value):
        self.flavor = flavor
        self.key = key
        self.value = value

    def apply(self, action):
        action.set_extra_spec(self.flavor, self.key, self.value)


class DelCommand:
    def __init__(self, flavor, key):
        self.flavor = flavor
        self.key = key

    def apply(self, action):
        action.del_extra_spec(self.flavor, self.key)


def handle_commands(action, compute, commands):
    if not commands:
        return
    if action in ('ask', 'report'):
        action_report = ActionReport()
        print(f'Proposing the following {len(commands)} changes to extra_specs:')
        for command in commands:
            command.apply(action_report)
    if action == 'ask':
        print('Do you want to apply these changes? y/n')
        if input() == 'y':
            action = 'apply'
        else:
            print('No changes will be applied.')
    if action == 'apply':
        action_apply = ActionApply(compute)
        for command in commands:
            command.apply(action_apply)


def main(argv):
    action = "ask"  # or "report" or "apply"

    errors = 0
    disk0_type = None
    cpu_type = None
    gen_all_names = False

    cloud = os.environ.get("OS_CLOUD")
    try:
        opts, flvs = getopt.gnu_getopt(argv, "hdqAt:p:c:a:",
                                       ("help", "debug", "quiet", "all-names",
                                        "disk0-type=", "cpu-type=", "os-cloud=", "action="))
    except getopt.GetoptError as exc:
        logger.critical(repr(exc))
        usage()
        return 1
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(file=sys.stdout)
            return 0
        if opt[0] == "-q" or opt[0] == "--quiet":
            logging.getLogger().setLevel(logging.WARNING)
        if opt[0] == "-d" or opt[0] == "--debug":
            logging.getLogger().setLevel(logging.DEBUG)
        if opt[0] == "-A" or opt[0] == "--all-names":
            gen_all_names = True
        if opt[0] == "-a" or opt[0] == "--action":
            action = opt[1].strip().lower()
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

    if action not in ('ask', 'report', 'apply'):
        logger.error("action needs to be one of ask, report, apply")
        usage()
        return 4

    if not cloud:
        logger.error("Need to pass -c|--os-cloud|OS_CLOUD env")
        usage()
        return 3

    conn = openstack.connect(cloud)
    conn.authorize()

    # select relevant flavors: either given via name, or all SCS flavors
    predicate = (lambda fn: fn in flvs) if flvs else (lambda fn: fn.startswith('SCS-'))
    flavors = [flavor for flavor in conn.compute.flavors() if predicate(flavor.name)]
    # This is likely a user error, so make them aware
    if len(flavors) < len(flvs):
        missing = set(flvs) - set(flavor.name for flavor in flavors)
        logger.warning("Flavors not found: " + ", ".join(missing))

    commands = []
    for flavor in flavors:
        extra_names_to_check = [
            (key, value)
            for key, value in flavor.extra_specs.items()
            if SCS_NAME_PATTERN.match(key)
        ]
        names_to_check = [('name', flavor.name)] if flavor.name.startswith('SCS-') else []
        names_to_check.extend(extra_names_to_check)

        # syntax check: compute flavorname instances
        # Also select best match
        bestln = 0
        reference_key = None
        flavornames = {}
        for key, name_str in names_to_check:
            try:
                flavornames[key] = parser_vN(name_str)
                # Longest name is the most specific
                if len(name_str) >= bestln:
                    bestln = len(name_str)
                    reference_key = key
            except ValueError as exc:
                logger.error(f"could not parse {key}={name_str}: {exc!r}")
                errors += 1

        # select a reference flavorname, check flavornames
        if flavornames:
            reference = flavornames[reference_key]
            reference_core = _extract_core(reference)
            for key, flavorname in flavornames.items():
                # sanity check: claims must be true wrt actual flavor
                errors += check_std_props(flavor, flavorname, " by name")
                # sanity check: claims must coincide (check remaining flavornames)
                if key == reference_key:
                    continue
                core = _extract_core(flavorname)
                if core != reference_core:
                    # for all we know, it might just be a case of one name understating something...
                    # (as long as we don't check things like CPU vendor)
                    # issue a warning nonetheless, because this case shouldn't be too common
                    logger.warning(f"Inconsistent {key} vs. {reference_key}: {core} vs. {reference_core}")
        else:
            # we need cputype and disktype from user
            if not cpu_type:
                logger.warning(f"Need to specify cpu-type for generating name for {flavor.name}, skipping")
                continue
            if flavor.disk and not disk0_type:
                logger.warning(f"Need to specify disk0-type for generating name for {flavor.name}, skipping")
                continue
            reference = generate_flavorname(flavor, cpu_type, disk0_type)

        expected = flavorname_to_dict(reference)
        # determine invalid keys (within scs namespace)
        # scs:name-vN is always permissible
        removals = [
            key
            for key in flavor.extra_specs
            if key.startswith('scs:') and not SCS_NAME_PATTERN.match(key)
            if expected.get(key, DEFAULTS.get(key)) is None
        ]
        logger.debug(f"Flavor {flavor.name}: expected={expected}, removals={removals}")

        for key in removals:
            commands.append(DelCommand(flavor, key))

        # generate or rectify extra_specs
        for key, value in expected.items():
            if not key.startswith("scs:"):
                continue
            if not gen_all_names and key.startswith("scs:name-v") and extra_names_to_check:
                continue  # do not generate names if names are present
            current = flavor.extra_specs.get(key)
            if current == value:
                continue
            if current is None and DEFAULTS.get(key) == value:
                continue
            if current is not None:
                logger.warning(f"{flavor.name}: resetting {key} because {current} != expected {value}")
            commands.append(SetCommand(flavor, key, value))

    handle_commands(action, conn.compute, commands)
    logger.info(f"Processed {len(flavors)} flavors, {len(commands)} changes")
    return errors


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    sys.exit(min(127, main(sys.argv[1:])))  # cap at 127 due to OS restrictions
