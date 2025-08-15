#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:

"""Flavor naming checker

Uses the flavor_names.py module.
Assumes a connection to an OpenStack tenant,
retrieves the list of flavors from there and validates them.
Something similar could be achieved by:
flavor-name-check.py -c $(openstack flavor list -f value -c Name)
In addition we check consistency by looking at the information
provided by openstack, such as the number of vCPUs and memory.

(c) Kurt Garloff <garloff@osb-alliance.com>, 12/2022
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 1/2024
SPDX-License-Identifier: CC-BY-SA 4.0
"""

import logging
import os
import sys
import typing
import getopt
import openstack

import flavor_names


logger = logging.getLogger(__name__)


def usage(rcode=1):
    "help output"
    print("Usage: flavor-names-openstack.py [options]", file=sys.stderr)
    print("Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)", file=sys.stderr)
    print("This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD", file=sys.stderr)
    print(" and reports inconsistencies, errors etc. It returns 0 on success.", file=sys.stderr)
    sys.exit(rcode)


TESTCASES = ('scs-0100-syntax-check', 'scs-0100-semantics-check', 'flavor-name-check')
STRATEGY = flavor_names.ParsingStrategy(
    vstr='v3',
    parsers=(flavor_names.parser_v3, ),
    tolerated_parsers=(flavor_names.parser_v2, flavor_names.parser_v1),
)
ACC_DISK = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)


def compute_scs_flavors(flavors: typing.List[openstack.compute.v2.flavor.Flavor], parser=STRATEGY) -> list:
    result = []
    for flv in flavors:
        if not flv.name or flv.name[:4] != 'SCS-':
            continue  # not an SCS flavor; none of our business
        try:
            flavorname = parser(flv.name)
        except ValueError as exc:
            logger.info(f"error parsing {flv.name}: {exc}")
            flavorname = None
        result.append((flv, flavorname))
    return result


def compute_scs_0100_syntax_check(scs_flavors: list) -> bool:
    problems = [flv.name for flv, flavorname in scs_flavors if not flavorname]
    if problems:
        logger.error(f"scs-100-syntax-check: flavor(s) failed: {', '.join(sorted(problems))}")
    return not problems


def compute_scs_0100_semantics_check(scs_flavors: list) -> bool:
    problems = set()
    for flv, flavorname in scs_flavors:
        if not flavorname:
            continue  # this case is handled by syntax check
        cpuram = flavorname.cpuram
        if flv.vcpus < cpuram.cpus:
            logger.info(f"Flavor {flv.name} CPU overpromise: {flv.vcpus} < {cpuram.cpus}")
            problems.add(flv.name)
        elif flv.vcpus > cpuram.cpus:
            logger.info(f"Flavor {flv.name} CPU underpromise: {flv.vcpus} > {cpuram.cpus}")
        # RAM
        flvram = int((flv.ram + 51) / 102.4) / 10
        # Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
        if flvram >= 10 and flvram != int(flvram) or flvram * 2 != int(flvram * 2):
            logger.info(f"Flavor {flv.name} uses discouraged uneven size of memory {flvram:.1f} GiB")
        if flvram < cpuram.ram:
            logger.info(f"Flavor {flv.name} RAM overpromise {flvram:.1f} < {cpuram.ram:.1f}")
            problems.add(flv.name)
        elif flvram > cpuram.ram:
            logger.info(f"Flavor {flv.name} RAM underpromise {flvram:.1f} > {cpuram.ram:.1f}")
        # Disk could have been omitted
        disksize = flavorname.disk.disksize if flavorname.disk else 0
        # We have a recommendation for disk size steps
        if disksize not in ACC_DISK:
            logger.info(f"Flavor {flv.name} non-standard disk size {disksize}, should have (5, 10, 20, 50, 100, 200, ...)")
        if flv.disk < disksize:
            logger.info(f"Flavor {flv.name} disk overpromise {flv.disk} < {disksize}")
            problems.add(flv.name)
        elif flv.disk > disksize:
            logger.info(f"Flavor {flv.name} disk underpromise {flv.disk} > {disksize}")
    if problems:
        logger.error(f"scs-100-semantics-check: flavor(s) failed: {', '.join(sorted(problems))}")
    return not problems


def compute_flavor_name_check(syntax_check_result, semantics_check_result):
    return syntax_check_result and semantics_check_result


# TODO see comment in main function about moving to another module

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


# TODO see comment in main function about moving to another module

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
    """Entry point -- main loop going over flavors"""
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    openstack.enable_logging(debug=False)
    cloud = None

    try:
        cloud = os.environ["OS_CLOUD"]
    except KeyError:
        pass
    try:
        opts, args = getopt.gnu_getopt(argv, "c:C:vhq321o",
                                       ("os-cloud=", "mand=", "verbose", "help", "quiet", "v2plus",
                                        "v3", "v1prefer", "accept-old-mandatory"))
    except getopt.GetoptError as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        elif opt[0] == "-C" or opt[0] == "--mand":
            if opt[1].split('/')[-1] != 'scs-0100-v3-flavors.yaml':
                print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-3" or opt[0] == "--v3":
            # fnmck.disallow_old = True
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-2" or opt[0] == "--v2plus":
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-1" or opt[0] == "--v1prefer":
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-o" or opt[0] == "--accept-old-mandatory":
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-v" or opt[0] == "--verbose":
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        elif opt[0] == "-q" or opt[0] == "--quiet":
            print(f'ignoring obsolete argument: {opt[0]}', file=sys.stderr)
        else:
            usage(2)
    if len(args) > 0:
        print(f"CRITICAL: Extra arguments {str(args)}", file=sys.stderr)
        usage(1)

    if not cloud:
        print("CRITICAL: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        sys.exit(1)

    # TODO in the future, the remainder should be moved to a central module `scs_compatible_iaas.py`,
    # which would import the test logic (i.e., the functions called compute_XYZ) from here.
    # Then this module wouldn't need to know about containers, and the central module can handle
    # information sharing as well as running precisely the requested set of testcases.
    c = Container()
    c.add_function('conn', lambda _: openstack.connect(cloud=cloud, timeout=32))
    c.add_function('flavors', lambda c: list(c.conn.compute.flavors()))
    c.add_function('scs_flavors', lambda c: compute_scs_flavors(c.flavors))
    c.add_function('scs_0100_syntax_check', lambda c: compute_scs_0100_syntax_check(c.scs_flavors))
    c.add_function('scs_0100_semantics_check', lambda c: compute_scs_0100_semantics_check(c.scs_flavors))
    c.add_function('flavor_name_check', lambda c: compute_flavor_name_check(c.scs_0100_syntax_check, c.scs_0100_semantics_check))
    for testcase in TESTCASES:
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
