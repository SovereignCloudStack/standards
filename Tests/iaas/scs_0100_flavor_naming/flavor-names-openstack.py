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

from flavor_names_check import \
    compute_scs_flavors,  compute_scs_0100_syntax_check, compute_scs_0100_semantics_check, compute_flavor_name_check


logger = logging.getLogger(__name__)


def usage(rcode=1):
    """help output"""
    print("Usage: flavor-names-openstack.py [options]", file=sys.stderr)
    print("Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)", file=sys.stderr)
    print("This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD", file=sys.stderr)
    print(" and reports inconsistencies, errors etc. It returns 0 on success.", file=sys.stderr)
    sys.exit(rcode)


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

    with openstack.connect(cloud=cloud, timeout=32) as conn:
        scs_flavors = compute_scs_flavors(conn.compute.flavors())
    result = compute_flavor_name_check(
        compute_scs_0100_syntax_check(scs_flavors),
        compute_scs_0100_semantics_check(scs_flavors),
    )
    print("flavor-name-check: " + ('FAIL', 'PASS')[min(1, result)])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        sys.exit(1)
