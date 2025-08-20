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
    compute_scs_flavors, compute_scs_0100_syntax_check, compute_scs_0100_semantics_check, compute_flavor_name_check
from scs_0101_entropy.entropy_check import \
    compute_scs_0101_image_property, compute_scs_0101_flavor_property, compute_canonical_image, \
    compute_collected_vm_output, compute_scs_0101_entropy_avail, compute_scs_0101_rngd, \
    compute_scs_0101_fips_test, compute_scs_0101_entropy_check


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
    # scs_0100_flavor_naming
    c.add_function('conn', lambda _: openstack.connect(cloud=cloud, timeout=32))
    c.add_function('flavors', lambda c: list(c.conn.list_flavors(get_extra=True)))
    c.add_function('images', lambda c: [img for img in c.conn.list_images() if img.visibility in ('public', 'community')])
    c.add_function('scs_flavors', lambda c: compute_scs_flavors(c.flavors))
    c.add_function('scs_0100_syntax_check', lambda c: compute_scs_0100_syntax_check(c.scs_flavors))
    c.add_function('scs_0100_semantics_check', lambda c: compute_scs_0100_semantics_check(c.scs_flavors))
    c.add_function('flavor_name_check', lambda c: compute_flavor_name_check(c.scs_0100_syntax_check, c.scs_0100_semantics_check))
    c.add_function('scs_0101_image_property', lambda c: compute_scs_0101_image_property(c.images))
    c.add_function('scs_0101_flavor_property', lambda c: compute_scs_0101_flavor_property(c.flavors))
    c.add_function('canonical_image', lambda c: compute_canonical_image(c.images))
    c.add_function('collected_vm_output', lambda c: compute_collected_vm_output(c.conn, c.flavors, c.canonical_image))
    c.add_function('scs_0101_entropy_avail', lambda c: compute_scs_0101_entropy_avail(c.collected_vm_output, c.canonical_image.name))
    c.add_function('scs_0101_rngd', lambda c: compute_scs_0101_rngd(c.collected_vm_output, c.canonical_image.name))
    c.add_function('scs_0101_fips_test', lambda c: compute_scs_0101_fips_test(c.collected_vm_output, c.canonical_image.name))
    c.add_function('entropy_check', lambda c: compute_scs_0101_entropy_check(c.scs_0101_entropy_avail, c.scs_0101_fips_test))
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

    testcases = [t for t in args if t.endswith('-check') or t.startswith('scs-')]
    if len(testcases) != len(args):
        unknown = [a for a in args if a not in testcases]
        logger.warning(f"ignoring unknown testcases: {','.join(unknown)}")

    if not cloud:
        print("CRITICAL: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        sys.exit(1)

    c = make_container(cloud)
    for testcase in testcases:
        harness(testcase, lambda: getattr(c, testcase.replace('-', '_')))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        sys.exit(1)
