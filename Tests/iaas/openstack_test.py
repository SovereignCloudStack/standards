#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:

"""Openstack testcase runner

(c) Matthias Büchse <matthias.buechse@alasca.cloud>, 8/2025
SPDX-License-Identifier: CC-BY-SA 4.0
"""

import getopt
import logging
import os
import sys

import openstack

from scs_0100_flavor_naming.flavor_names_check import \
    compute_scs_flavors, compute_scs_0100_syntax_check, compute_scs_0100_semantics_check, \
    compute_flavor_spec
from scs_0101_entropy.entropy_check import \
    compute_scs_0101_image_property, compute_scs_0101_flavor_property, compute_canonical_image, \
    compute_collected_vm_output, compute_scs_0101_entropy_avail, compute_scs_0101_rngd, \
    compute_scs_0101_fips_test
from scs_0102_image_metadata.image_metadata import \
    compute_scs_0102_prop_architecture, compute_scs_0102_prop_hash_algo, compute_scs_0102_prop_min_disk, \
    compute_scs_0102_prop_min_ram, compute_scs_0102_prop_os_version, compute_scs_0102_prop_os_distro, \
    compute_scs_0102_prop_os_purpose, \
    compute_scs_0102_prop_hw_disk_bus, compute_scs_0102_prop_hypervisor_type, compute_scs_0102_prop_hw_rng_model, \
    compute_scs_0102_prop_image_build_date, compute_scs_0102_prop_image_original_user, \
    compute_scs_0102_prop_image_source, compute_scs_0102_prop_image_description, \
    compute_scs_0102_prop_replace_frequency, compute_scs_0102_prop_provided_until, \
    compute_scs_0102_prop_uuid_validity, compute_scs_0102_prop_hotfix_hours, \
    compute_scs_0102_image_recency
from scs_0103_standard_flavors.standard_flavors import \
    SCS_0103_CANONICAL_NAMES, compute_flavor_lookup, compute_scs_0103_flavor
from scs_0104_standard_images.standard_images import \
    SCS_0104_IMAGE_SPECS, compute_scs_0104_source, compute_scs_0104_image
from scs_0114_volume_types.volume_types import \
    compute_volume_type_lookup, compute_scs_0114_syntax_check, compute_scs_0114_aspect_type
from scs_0115_security_groups.security_groups import \
    compute_scs_0115_default_rules
from scs_0116_key_manager.key_manager import \
    compute_services_lookup, compute_scs_0116_presence, compute_scs_0116_permissions
from scs_0117_volume_backup.volume_backup import \
    compute_scs_0117_test_backup
from scs_0123_mandatory_services.mandatory_services import \
    compute_scs_0123_service_presence, compute_scs_0123_swift_s3


logger = logging.getLogger(__name__)


def usage(rcode=1, file=sys.stderr):
    """help output"""
    print("Usage: openstack_test.py [options] testcase-id1 ... testcase-idN", file=file)
    print("Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)", file=file)
    print("Runs specified testcases against the OpenStack cloud OS_CLOUD", file=file)
    print("and reports inconsistencies, errors etc. It returns 0 on success.", file=file)
    sys.exit(rcode)


def make_container(cloud):
    c = Container()
    # basic support attributes shared by multiple testcases
    c.add_function('conn', lambda _: openstack.connect(cloud=cloud, timeout=32))
    c.add_function('flavors', lambda c: list(c.conn.list_flavors(get_extra=True)))
    c.add_function('images', lambda c: [img for img in c.conn.list_images(show_all=True) if img.visibility in ('public', 'community')])
    c.add_function('image_lookup', lambda c: {img.name: img for img in c.images})
    # scs_0100_flavor_naming
    c.add_function('scs_flavors', lambda c: compute_scs_flavors(c.flavors))
    c.add_function('scs_0100_syntax_check', lambda c: compute_scs_0100_syntax_check(c.scs_flavors))
    c.add_function('scs_0100_semantics_check', lambda c: compute_scs_0100_semantics_check(c.scs_flavors))
    c.add_function('flavor_name_check', lambda c: all((
        c.scs_0100_syntax_check, c.scs_0100_semantics_check,
    )))
    # scs_0101_entropy
    c.add_function('canonical_image', lambda c: compute_canonical_image(c.images))
    c.add_function('collected_vm_output', lambda c: compute_collected_vm_output(c.conn, c.flavors, c.canonical_image))
    c.add_function('scs_0101_image_property', lambda c: compute_scs_0101_image_property(c.images))
    c.add_function('scs_0101_flavor_property', lambda c: compute_scs_0101_flavor_property(c.flavors))
    c.add_function('scs_0101_entropy_avail', lambda c: compute_scs_0101_entropy_avail(c.collected_vm_output, c.canonical_image.name))
    c.add_function('scs_0101_rngd', lambda c: compute_scs_0101_rngd(c.collected_vm_output, c.canonical_image.name))
    c.add_function('scs_0101_fips_test', lambda c: compute_scs_0101_fips_test(c.collected_vm_output, c.canonical_image.name))
    c.add_function('entropy_check', lambda c: all((
        c.scs_0101_entropy_avail, c.scs_0101_fips_test,
    )))
    # scs_0102_image_metadata
    c.add_function('scs_0102_prop_architecture', lambda c: compute_scs_0102_prop_architecture(c.images))
    c.add_function('scs_0102_prop_hash_algo', lambda c: compute_scs_0102_prop_hash_algo(c.images))
    c.add_function('scs_0102_prop_min_disk', lambda c: compute_scs_0102_prop_min_disk(c.images))
    c.add_function('scs_0102_prop_min_ram', lambda c: compute_scs_0102_prop_min_ram(c.images))
    c.add_function('scs_0102_prop_os_version', lambda c: compute_scs_0102_prop_os_version(c.images))
    c.add_function('scs_0102_prop_os_distro', lambda c: compute_scs_0102_prop_os_distro(c.images))
    c.add_function('scs_0102_prop_os_purpose', lambda c: compute_scs_0102_prop_os_purpose(c.images))
    c.add_function('scs_0102_prop_hw_disk_bus', lambda c: compute_scs_0102_prop_hw_disk_bus(c.images))
    c.add_function('scs_0102_prop_hypervisor_type', lambda c: compute_scs_0102_prop_hypervisor_type(c.images))
    c.add_function('scs_0102_prop_hw_rng_model', lambda c: compute_scs_0102_prop_hw_rng_model(c.images))
    c.add_function('scs_0102_prop_image_build_date', lambda c: compute_scs_0102_prop_image_build_date(c.images))
    c.add_function('scs_0102_prop_image_original_user', lambda c: compute_scs_0102_prop_image_original_user(c.images))
    c.add_function('scs_0102_prop_image_source', lambda c: compute_scs_0102_prop_image_source(c.images))
    c.add_function('scs_0102_prop_image_description', lambda c: compute_scs_0102_prop_image_description(c.images))
    c.add_function('scs_0102_prop_replace_frequency', lambda c: compute_scs_0102_prop_replace_frequency(c.images))
    c.add_function('scs_0102_prop_provided_until', lambda c: compute_scs_0102_prop_provided_until(c.images))
    c.add_function('scs_0102_prop_uuid_validity', lambda c: compute_scs_0102_prop_uuid_validity(c.images))
    c.add_function('scs_0102_prop_hotfix_hours', lambda c: compute_scs_0102_prop_hotfix_hours(c.images))
    c.add_function('scs_0102_image_recency', lambda c: compute_scs_0102_image_recency(c.images))
    c.add_function('image_metadata_check', lambda c: all((
        c.scs_0102_prop_architecture, c.scs_0102_prop_min_disk, c.scs_0102_prop_min_ram, c.scs_0102_prop_os_version,
        c.scs_0102_prop_os_distro, c.scs_0102_prop_hw_disk_bus, c.scs_0102_prop_image_build_date,
        c.scs_0102_prop_image_original_user, c.scs_0102_prop_image_source, c.scs_0102_prop_image_description,
        c.scs_0102_prop_replace_frequency, c.scs_0102_prop_provided_until, c.scs_0102_prop_uuid_validity,
        c.scs_0102_image_recency,
    )))
    # scs_0103_standard_flavors
    c.add_function('flavor_lookup', lambda c: compute_flavor_lookup(c.flavors))
    for canonical_name in SCS_0103_CANONICAL_NAMES:
        nm = canonical_name.removeprefix('SCS-').lower().replace('-', '_')
        # NOTE we need cn=canonical_name below because anon function only catches a variable's CELL, not its value
        # i.e., if we use canonical_name inside it, we will only get its final value after the loop is done
        c.add_function(
            f'scs_0103_flavor_{nm}',
            lambda c, cn=canonical_name: compute_scs_0103_flavor(c.flavor_lookup, compute_flavor_spec(cn))
        )
    c.add_function('standard_flavors_check', lambda c: all((
        c.scs_0103_flavor_1v_4, c.scs_0103_flavor_2v_8, c.scs_0103_flavor_4v_16, c.scs_0103_flavor_8v_32,
        c.scs_0103_flavor_1v_2, c.scs_0103_flavor_2v_4, c.scs_0103_flavor_4v_8, c.scs_0103_flavor_8v_16,
        c.scs_0103_flavor_16v_32, c.scs_0103_flavor_1v_8, c.scs_0103_flavor_2v_16, c.scs_0103_flavor_4v_32,
        c.scs_0103_flavor_1l_1, c.scs_0103_flavor_2v_4_20s, c.scs_0103_flavor_4v_16_100s,
    )))
    # scs_0104_standard_images
    c.add_function('scs_0104_source_capi_1', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['ubuntu-capi-image-1']))
    c.add_function('scs_0104_source_capi_2', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['ubuntu-capi-image-2']))
    c.add_function('scs_0104_source_ubuntu_2404', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 24.04']))
    c.add_function('scs_0104_source_ubuntu_2204', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 22.04']))
    c.add_function('scs_0104_source_ubuntu_2004', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 20.04']))
    c.add_function('scs_0104_source_debian_13', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 13']))
    c.add_function('scs_0104_source_debian_12', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 12']))
    c.add_function('scs_0104_source_debian_11', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 11']))
    c.add_function('scs_0104_source_debian_10', lambda c: compute_scs_0104_source(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 10']))
    c.add_function('scs_0104_image_capi_1', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['ubuntu-capi-image-1']))
    c.add_function('scs_0104_image_capi_2', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['ubuntu-capi-image-2']))
    c.add_function('scs_0104_image_ubuntu_2404', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 24.04']))
    c.add_function('scs_0104_image_ubuntu_2204', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 22.04']))
    c.add_function('scs_0104_image_ubuntu_2004', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Ubuntu 20.04']))
    c.add_function('scs_0104_image_debian_13', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 13']))
    c.add_function('scs_0104_image_debian_12', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 12']))
    c.add_function('scs_0104_image_debian_11', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 11']))
    c.add_function('scs_0104_image_debian_10', lambda c: compute_scs_0104_image(c.image_lookup, SCS_0104_IMAGE_SPECS['Debian 10']))
    # NOTE the following variant is correct for SCS-compatible IaaS v4 only
    c.add_function('standard_images_check_1', lambda c: all((
        c.scs_0104_image_ubuntu_2204,
        c.scs_0104_source_capi_1, c.scs_0104_source_capi_2,
        c.scs_0104_source_ubuntu_2404, c.scs_0104_source_ubuntu_2204, c.scs_0104_source_ubuntu_2004,
        c.scs_0104_source_debian_13, c.scs_0104_source_debian_12, c.scs_0104_source_debian_11, c.scs_0104_source_debian_10,
    )))
    # NOTE the following variant is correct for SCS-compatible IaaS v5.1 only
    c.add_function('standard_images_check_2', lambda c: all((
        c.scs_0104_image_ubuntu_2404,
        c.scs_0104_source_capi_1, c.scs_0104_source_capi_2,
        c.scs_0104_source_ubuntu_2404, c.scs_0104_source_ubuntu_2204, c.scs_0104_source_ubuntu_2004,
        c.scs_0104_source_debian_13, c.scs_0104_source_debian_12, c.scs_0104_source_debian_11, c.scs_0104_source_debian_10,
    )))
    # scs_0114_volume_types
    c.add_function('volume_types', lambda c: c.conn.list_volume_types())
    c.add_function('volume_type_lookup', lambda c: compute_volume_type_lookup(c.volume_types))
    c.add_function('scs_0114_syntax_check', lambda c: compute_scs_0114_syntax_check(c.volume_type_lookup))
    c.add_function('scs_0114_encrypted_type', lambda c: compute_scs_0114_aspect_type(c.volume_type_lookup, 'encrypted'))
    c.add_function('scs_0114_replicated_type', lambda c: compute_scs_0114_aspect_type(c.volume_type_lookup, 'replicated'))
    c.add_function('volume_types_check', lambda c: all((
        c.scs_0114_syntax_check,
        # the following is recommended only, but we treat this whole monolithic testcase as recommended
        c.scs_0114_encrypted_type, c.scs_0114_replicated_type,
    )))
    # scs_0115_security_groups
    c.add_function('scs_0115_default_rules', lambda c: compute_scs_0115_default_rules(c.conn))
    c.add_function('security_groups_default_rules_check', lambda c: c.scs_0115_default_rules)
    # scs_0116_key_manager
    c.add_function('services_lookup', lambda c: compute_services_lookup(c.conn))
    c.add_function('scs_0116_presence', lambda c: compute_scs_0116_presence(c.services_lookup))
    c.add_function('scs_0116_permissions', lambda c: compute_scs_0116_permissions(c.conn, c.services_lookup))
    c.add_function('key_manager_check', lambda c: all((
        # recommended only: c.scs_0116_presence,
        c.scs_0116_permissions,
    )))
    # scs_0117_volume_backup
    c.add_function('scs_0117_test_backup', lambda c: compute_scs_0117_test_backup(c.conn))
    c.add_function('volume_backup_check', lambda c: all((
        c.scs_0117_test_backup,
    )))
    # scs_0123_mandatory_services
    c.add_function('scs_0123_service_compute', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'compute'))
    c.add_function('scs_0123_service_identity', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'identity'))
    c.add_function('scs_0123_service_image', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'image'))
    c.add_function('scs_0123_service_network', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'network'))
    c.add_function('scs_0123_service_load_balancer', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'load-balancer'))
    c.add_function('scs_0123_service_placement', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'placement'))
    c.add_function('scs_0123_service_object_store', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'object-store'))
    c.add_function('scs_0123_storage_apis', lambda c: compute_scs_0123_service_presence(c.services_lookup, 'volume', 'volumev3', 'block-storage'))
    c.add_function('scs_0123_swift_s3', lambda c: compute_scs_0123_swift_s3(c.conn))
    c.add_function('service_apis_check', lambda c: all((
        c.scs_0123_service_compute, c.scs_0123_service_identity, c.scs_0123_service_image,
        c.scs_0123_service_network, c.scs_0123_service_load_balancer, c.scs_0123_service_placement,
        c.scs_0123_service_object_store, c.scs_0123_storage_apis, c.scs_0123_swift_s3,
    )))
    return c


class Container:
    """
    This class does lazy evaluation and memoization. You register any potential value either
    by giving the value directly, using `add_value`, or
    by specifying how it is computed using `add_function`,
    which expects a function that takes a container (so other values may be referred to).
    In each case, you have to give the value a name.

    The value will be available as a normal member variable under this name.
    If given via a function, this function will only be evaluated when the value is accessed,
    and the value will be memoized, so the function won't be called twice.
    If the function raises an exception, then this will be memoized just as well.

    For instance,

    >>>> container = Container()
    >>>> container.add_function('pi', lambda _: 22/7)
    >>>> container.add_function('pi_squared', lambda c: c.pi * c.pi)
    >>>> assert container.pi_squared == 22/7 * 22/7
    """
    def __init__(self):
        self._values = {}
        self._functions = {}

    def __getattr__(self, key):
        val = self._values.get(key)
        if val is None:
            logger.debug(f'... {key}')
            try:
                ret = self._functions[key](self)
            except BaseException as e:
                val = (True, e)
            else:
                val = (False, ret)
            self._values[key] = val
        error, ret = val
        if error:
            raise ret
        return ret

    def add_function(self, name, fn):
        if name in self._functions:
            raise RuntimeError(f"fn {name} already registered")
        self._functions[name] = fn

    def add_value(self, name, value):
        if name in self._values:
            raise RuntimeError(f"value {name} already registered")
        self._values[name] = value


def harness(name, *check_fns):
    """Harness for evaluating testcase `name`.

    Logs beginning of computation.
    Calls each fn in `check_fns`.
    Prints (to stdout) 'name: RESULT', where RESULT is one of

    - 'ABORT' if an exception occurs during the function calls
    - 'FAIL' if one of the functions has a falsy result
    - 'PASS' otherwise
    """
    logger.debug(f'** {name}')
    try:
        result = all(check_fn() for check_fn in check_fns)
    except BaseException:
        logger.debug('exception during check', exc_info=True)
        result = 'ABORT'
    else:
        result = ['FAIL', 'PASS'][min(1, result)]
    # this is quite redundant
    # logger.debug(f'** computation end for {name}')
    print(f"{name}: {result}")


def main(argv):
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    openstack.enable_logging(debug=False)
    cloud = None

    try:
        cloud = os.environ["OS_CLOUD"]
    except KeyError:
        pass
    try:
        opts, args = getopt.gnu_getopt(argv, "c:C:", ("os-cloud=", ))
    except getopt.GetoptError as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        else:
            usage(2)

    # NOTE For historic reasons, there is precisely one testcase id, namely standard-images-check,
    # whose meaning depends on the version of the certificate scope in question. We are in the process
    # of transitioning away from this anti-feature. For the time being, however, we use the following
    # hack to support it: One testcase may be implemented in multiple variants, denoted by suffixing
    # a number, as in standard-images-check/1, standard-images-check/2.
    # NOTE Also, the historic testcases have terrible naming. We will transition towards names
    # that encode the corresponding standard, such as scs-0104-image-ubuntu-2404.
    testcases = [t for t in args if t.rsplit('/', 1)[0].endswith('-check') or t.startswith('scs-')]
    if len(testcases) != len(args):
        unknown = [a for a in args if a not in testcases]
        logger.warning(f"ignoring unknown testcases: {','.join(unknown)}")

    if not cloud:
        print("CRITICAL: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        sys.exit(1)

    c = make_container(cloud)
    for testcase in testcases:
        testcase_name = testcase.rsplit('/', 1)[0]  # see the note above
        harness(testcase_name, lambda: getattr(c, testcase.replace('-', '_').replace('/', '_')))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        sys.exit(1)
