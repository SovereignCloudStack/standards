#!/usr/bin/env python3
"""
Generate flavor specification file for osism's flavor manager,
cf. https://github.com/osism/openstack-flavor-manager .

The spec file is output to stdout.
"""
import logging
import sys

import yaml

from scs_0100_flavor_naming.flavor_names import compute_flavor_spec
from scs_0103_standard_flavors.standard_flavors import \
    SCS_0103_V1_MANDATORY, SCS_0103_V1_RECOMMENDED

logger = logging.getLogger(__name__)


def convert_flavor_spec(canonical_name, spec):
    """convert `spec` into format for openstack-flavor-manager"""
    converted = {
        'name': canonical_name,
        'cpus': spec['cpus'],
        'ram': int(1024 * spec['ram']),
    }
    if 'disk' in spec:
        converted['disk'] = spec['disk']
    for k, v in spec.items():
        if not k.startswith('scs:'):
            continue
        converted[k] = v
    return converted


def compute_spec_list(canonical_names):
    return [
        convert_flavor_spec(
            canonical_name,
            compute_flavor_spec(canonical_name),
        )
        for canonical_name in canonical_names
    ]


def main(argv):
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    # boilerplate / scaffolding
    result = yaml.safe_load("""
reference:
  - field: name
    mandatory_prefix: SCS-
  - field: public
    default: true
  - field: disabled
    default: false
  - field: cpus
  - field: ram
  - field: disk
mandatory: []
recommended: []
""")

    result['mandatory'] = compute_spec_list(SCS_0103_V1_MANDATORY)
    result['recommended'] = compute_spec_list(SCS_0103_V1_RECOMMENDED)

    print(yaml.dump(result, sort_keys=False))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
