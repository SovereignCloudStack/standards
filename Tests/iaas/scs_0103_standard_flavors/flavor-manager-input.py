#!/usr/bin/env python3
"""
Convert yaml format from the one expected by flavors-openstack.py to the one expected
by osism's flavor manager, cf. https://github.com/osism/openstack-flavor-manager .

The conversion is performed from stdin to stdout.
"""
import logging
import sys

import yaml


logger = logging.getLogger(__name__)


def main(argv):
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    # load the yaml, checking for sanity
    try:
        flavor_spec_data = yaml.safe_load(sys.stdin)
    except Exception as e:
        logger.critical(f"Unable to load: {e!r}")
        logger.debug("Exception info", exc_info=True)
        return 1

    if 'meta' not in flavor_spec_data or 'name_key' not in flavor_spec_data['meta']:
        logger.critical("Flavor definition missing 'meta' field or field incomplete")
        return 1

    if 'flavor_groups' not in flavor_spec_data:
        logger.critical("Flavor definition missing 'flavor_groups' field")

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

    # transfer the info into the result yaml, again checking for sanity
    for flavor_group in flavor_spec_data['flavor_groups']:
        group_info = dict(flavor_group)
        group_info.pop('list')
        missing = {'status'} - set(group_info)
        if missing:
            logging.critical(f"Flavor group missing attributes: {', '.join(missing)}")
            return 1
        group_info.pop('status')
        result_list = result[flavor_group['status']]
        for flavor_spec in flavor_group['list']:
            missing = {'name', 'cpus', 'ram'} - set(flavor_spec)
            if missing:
                logging.critical(f"Flavor spec missing attributes: {', '.join(missing)}")
                return 1
            flavor_spec = {**group_info, **flavor_spec}
            flavor_spec['ram'] = flavor_spec['ram'] * 1024
            extra_specs = {
                f"scs:{key}": value
                for key, value in flavor_spec.items()
                if key not in ('name', 'cpus', 'ram', 'disk')
            }
            flavor_spec = {
                key: value
                for key, value in flavor_spec.items()
                if key in ('name', 'cpus', 'ram', 'disk')
            }
            result_list.append({**flavor_spec, **extra_specs})

    print(yaml.dump(result, sort_keys=False))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
