#!/usr/bin/env python3
"""Check flavor names in the YAML files used for scs-0103-v1 with respect to scs-0100-vX.

For reference, see

  - </Standards/scs-0100-v3-flavor-naming.md>
  - </Standards/scs-0103-v1-standard-flavors.md>

Also check that the flavor properties encoded in the YAML match those encoded in the name.
"""

import sys
from pathlib import Path

import yaml

from flavor_names import parser_v2, flavorname_to_dict


REQUIRED_FIELDS = ['scs:name-v1', 'scs:name-v2', 'name', 'cpus', 'ram', 'scs:cpu-type']
DEFAULTS = {'scs:disk0-type': 'network'}


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
        name_v2 = flavor_spec['scs:name-v2']
        try:
            flavorname = parser_v2(name_v2)
        except Exception:
            flavorname = None
        if not flavorname:
            self.emit(f"flavor {name}: name-v2 '{name_v2}' could not be parsed")
            return
        undefined = Undefined()
        expected = flavorname_to_dict(flavorname)
        # add explicit undefined so the final for-loop catches spurious entries
        for key in flavor_spec:
            if key == 'name':
                continue
            expected.setdefault(key, undefined)
        for key, exp_val in expected.items():
            val = flavor_spec.get(key, DEFAULTS.get(key, undefined))
            if val != exp_val:
                self.emit(
                    f"flavor '{name}': field '{key}' contradicting name-v2 '{name_v2}'; "
                    f"found {val!r}, expected {exp_val!r}"
                )


def check(yaml_dir_path):
    if not isinstance(yaml_dir_path, Path):
        raise ValueError("yaml_dir_path must be a pathlib.Path")
    yaml_paths = sorted(yaml_dir_path.glob("scs-0103-*.yaml"))
    main_checker = Checker()
    if not yaml_paths:
        main_checker.emit("no yaml files found!")
    for yaml_path in yaml_paths:
        with open(yaml_path, mode="rb") as fileobj:
            flavor_spec_data = yaml.safe_load(fileobj)
        if 'flavor_groups' not in flavor_spec_data:
            main_checker.emit(f"file '{yaml_path.name}': missing field 'flavor_groups'")
            continue
        checker = Checker()
        for group in flavor_spec_data['flavor_groups']:
            for flavor_spec in group['list']:
                checker.check_spec(flavor_spec)
        if checker.errors:
            main_checker.emit(f"file '{yaml_path.name}': found {checker.errors} errors")
    return main_checker.errors


def validate_args(argv):
    if len(sys.argv) != 2:
        raise RuntimeError("must specify exactly one argument, PATH to the yaml directory")
    yaml_path = Path(argv[1])
    if not yaml_path.is_dir():
        raise RuntimeError(f"not a directory: {yaml_path}")
    return yaml_path


if __name__ == "__main__":
    try:
        sys.exit(check(validate_args(sys.argv)))
    except Exception as e:
        print(f"CRITICAL: {e!s}", file=sys.stderr)
        sys.exit(1)
