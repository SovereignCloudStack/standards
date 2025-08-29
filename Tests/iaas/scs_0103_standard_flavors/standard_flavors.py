import logging


logger = logging.getLogger(__name__)


NAME_KEY = "scs:name-v2"
SCS_0103_CANONICAL_NAMES = (
    "SCS-1V-4",
    "SCS-2V-8",
    "SCS-4V-16",
    "SCS-8V-32",
    "SCS-1V-2",
    "SCS-2V-4",
    "SCS-4V-8",
    "SCS-8V-16",
    "SCS-16V-32",
    "SCS-1V-8",
    "SCS-2V-16",
    "SCS-4V-32",
    "SCS-1L-1",
    "SCS-2V-4-20s",
    "SCS-4V-16-100s",
    "SCS-1V-4-10",
    "SCS-2V-8-20",
    "SCS-4V-16-50",
    "SCS-8V-32-100",
    "SCS-1V-2-5",
    "SCS-2V-4-10",
    "SCS-4V-8-20",
    "SCS-8V-16-50",
    "SCS-16V-32-100",
    "SCS-1V-8-20",
    "SCS-2V-16-50",
    "SCS-4V-32-100",
    "SCS-1L-1-5",
)


def compute_flavor_lookup(flavors, name_key=NAME_KEY):
    # look up via extra_spec given by name_key
    by_name = {
        flavor.extra_specs[name_key]: flavor
        for flavor in flavors
        if name_key in flavor.extra_specs
    }
    # as a fallback, also allow flavor to be found by its actual name
    for flavor in flavors:
        if not flavor.name.startswith('SCS-'):
            continue
        by_name.setdefault(flavor.name, flavor)
    return by_name


def compute_scs_0103_flavor(flavor_lookup, flavor_spec):
    """
    This test ensures that the flavor given via `flavor_spec` is present.

    The primary way to arrive at a flavor spec is to parse an SCS flavor name and
    convert it to a dictionary. This can be done using the module `flavor_names.py`
    in the `iaas/scs_0100_flavor_naming` directory. See `iaas/openstack_test.py`
    for details.
    """
    canonical_name = flavor_spec[NAME_KEY]
    flavor = flavor_lookup.get(canonical_name)
    if flavor is None:
        logger.error(f'standard flavor missing: {canonical_name}')
        return False
    # check that flavor matches flavor_spec
    # cpu, ram, and disk should match, and they should match precisely for discoverability
    # also check extra_specs (ours are prefixed with 'scs:')
    comparison = [
        ('vcpus', flavor.vcpus, flavor_spec['cpus']),
        ('ram', flavor.ram, 1024 * flavor_spec['ram']),
        ('disk', flavor.disk, flavor_spec.get('disk', 0)),
    ] + [
        (key, value, flavor.extra_specs.get(key))
        for key, value in flavor_spec.items()
        if key.startswith("scs:")
    ]
    report = [
        f'{key}: {a_val!r} should be {b_val!r}'
        for key, a_val, b_val in comparison
        if a_val != b_val
    ]
    if report:
        logger.error(f"Flavor '{flavor.name}' violating constraints: {'; '.join(report)}")
    return not report
