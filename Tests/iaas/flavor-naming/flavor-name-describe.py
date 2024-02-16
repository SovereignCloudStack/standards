#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""Flavor naming describer
https://github.com/SovereignCloudStack/Standards/

Output a human readable flavor description from the SCS names

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2023
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 1/2024
License: CC-BY-SA 4.0
"""
import sys

from flavor_name_check import CompatLayer, prettyname


def main(argv):
    """Entry point for testing"""
    fnmck = CompatLayer()
    for nm in argv:
        ret = fnmck.parsename(nm)
        if ret:
            print(f'{nm}: {prettyname(ret)}')
        else:
            print(f'{nm}: Not an SCS flavor')


if __name__ == "__main__":
    main(sys.argv[1:])
