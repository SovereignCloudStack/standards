#!/usr/bin/env python3
"""Check flavor names in the YAML files used for scs-0103-v1 with respect to scs-0100-vX.

For reference, see

  - </Standards/scs-0100-v3-flavor-naming.md>
  - </Standards/scs-0103-v1-standard-flavors.md>

Also check that the flavor properties encoded in the YAML match those encoded in the name.
"""
import importlib
import os
import os.path
import sys

import yaml

flavor_name_check = importlib.import_module("flavor-name-check")
flavor_name_check.disallow_old = True


REQUIRED_FIELDS = ['name-v1', 'name-v2', 'name', 'cpus', 'ram', 'cpu-type']
DEFAULTS = {'disk0-type': 'network'}
CPUTYPE_KEY = {'L': 'crowded-core', 'V': 'shared-core', 'T': 'dedicated-thread', 'C': 'dedicated-core'}
DISKTYPE_KEY = {'n': 'network', 'h': 'hdd', 's': 'ssd', 'p': 'nvme'}


class Undefined:
    def __repr__(self):
        return 'undefined'


class Checker:
    """
    Auxiliary class that contains the logic for checking a single flavor spec
    as well as emitting error messages to stderr.

    Once this program grows (significantly), this class should actually be split
    in two in order to follow the single-responsibility principle.
    """
    def __init__(self):
        self.errors = 0

    def emit(self, s):
        print(f"ERROR: {s}", file=sys.stderr)
        self.errors += 1

    def check_spec(self, flavor_spec):
        missing = [key for key in REQUIRED_FIELDS if key not in flavor_spec]
        if missing:
            self.emit(f"flavor spec missing keys {', '.join(missing)}: {flavor_spec}")
            return
        name = flavor_spec['name']
        name_v2 = flavor_spec['name-v2']
        parsed = flavor_name_check.parsename(name_v2)
        if not parsed:
            self.emit(f"flavor {name}: name-v2 '{name_v2}' could not be parsed")
            return
        cpu, disk, hype, hvirt, cpubrand, gpu, ibd = parsed
        undefined = Undefined()
        expected = {
            'cpus': cpu.cpus,
            'cpu-type': CPUTYPE_KEY[cpu.cputype],
            'ram': cpu.ram,
            'name-v1': flavor_name_check.new_to_old(name_v2),
            'disk': undefined,
        }
        if disk.parsed:
            if disk.nrdisks != 1:
                self.emit(f"flavor '{name}': name-v2 using multiple disks")
            expected['disk'] = disk.disksize
            expected['disk0-type'] = DISKTYPE_KEY[disk.disktype or 'n']
        for key, exp_val in expected.items():
            val = flavor_spec.get(key, DEFAULTS.get(key, undefined))
            if val != exp_val:
                self.emit(
                    f"flavor '{name}': field '{key}' contradicting name-v2 '{name_v2}'; "
                    f"found {val!r}, expected {exp_val!r}"
                )


def main(argv):
    if len(argv) != 2:
        raise RuntimeError("must specify exactly one argument, PATH to the yaml directory")
    yaml_path = argv[1]
    yaml_files = sorted([
        filename
        for filename in os.listdir(yaml_path)
        if filename.startswith("scs-0103-") and filename.endswith(".yaml")
    ])
    main_checker = Checker()
    if not yaml_files:
        main_checker.emit("no yaml files found!")
    for filename in yaml_files:
        with open(os.path.join(yaml_path, filename), "rb") as fileobj:
            flavor_spec_data = yaml.safe_load(fileobj)
        if 'flavor_groups' not in flavor_spec_data:
            main_checker.emit(f"file '{filename}': missing field 'flavor_groups'")
            continue
        checker = Checker()
        for group in flavor_spec_data['flavor_groups']:
            for flavor_spec in group['list']:
                checker.check_spec(flavor_spec)
        if checker.errors:
            main_checker.emit(f"file '{filename}': found {checker.errors} errors")
    return main_checker.errors


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"CRITICAL: {e!s}", file=sys.stderr)
        sys.exit(1)
