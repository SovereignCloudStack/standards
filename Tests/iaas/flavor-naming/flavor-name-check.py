#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""Flavor naming checker
https://github.com/SovereignCloudStack/standards/Test/iaas/flavor-naming/

(c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 1/2024
License: CC-BY-SA 4.0
"""

import sys

from flavor_name_check import CompatLayer, inputflavor
from flavor_name_describe import prettyname


def usage():
    "help"
    print("Usage: flavor-name-check.py [-d] [-v] [-2] [-1] [-o] [-c] [-C mand.yaml] [-i | NAME [NAME [...]]]")
    print("Flavor name checker returns 0 if no error, otherwise check stderr for details")
    print("-d enables debug mode, -v outputs a verbose description, -i enters interactive input mode")
    print("-2 disallows old v1 flavor naming, -1 checks old names for completeness, -o accepts them still")
    print("-c checks the SCS names AND checks the list for completeness w.r.t. SCS mandatory flavors.")
    print("-C mand.yaml reads the mandatory flavor list from mand.yaml instead of SCS-Spec.MandatoryFlavors.yaml")
    print("Example: flavor-name-check.py -c $(openstack flavor list -f value -c Name)")
    sys.exit(2)


def main(argv):
    """Entry point when used as selfstanding tool"""
    _fnmck = CompatLayer()
    completecheck = False
    accept_old_mand = False
    # Number of good SCS flavors
    scs = 0
    # Number of non-SCS flavors
    nonscs = 0
    # Number of errors
    error = 0

    # TODO: Use getopt for proper option parsing
    if len(argv) < 1 or argv[0] == "-h":
        usage()
    if argv[0] == "-d":
        _fnmck.debug = True
        argv = argv[1:]
    if argv[0] == "-v":
        _fnmck.verbose = True
        argv = argv[1:]
    if argv[0] == "-2":
        _fnmck.disallow_old = True
        argv = argv[1:]
    if argv[0] == "-1":
        _fnmck.prefer_old = True
        argv = argv[1:]
    if argv[0] == "-3":
        v3_flv = True
        argv = argv[1:]
    if argv[0] == "-o":
        accept_old_mand = True
        argv = argv[1:]
    if argv[0] == "-c":
        completecheck = True
        scsMandatory, scsRecommended = _fnmck.readflavors(_fnmck.mandFlavorFile, v3_flv)
        scsMandNum = len(scsMandatory)
        scsRecNum = len(scsRecommended)
        if _fnmck.debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[1:]
    if argv[0] == "-C":
        completecheck = True
        scsMandatory, scsRecommended = _fnmck.readflavors(argv[1], v3_flv)
        scsMandNum = len(scsMandatory)
        scsRecNum = len(scsRecommended)
        if _fnmck.debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[2:]

    # Interactive input of flavor
    if argv and argv[0] == "-i":
        ret = inputflavor()
        print()
        nm1 = _fnmck.outname(ret)
        print(nm1)
        ret2 = _fnmck.parsename(nm1)
        nm2 = _fnmck.outname(ret2)
        if nm1 != nm2:
            print(f"WARNING: {nm1} != {nm2}")
        argv = argv[1:]
        scs = 1

    flavorlist = argv

    for name in flavorlist:
        if not name:
            continue
        try:
            ret = _fnmck.parsename(name)
        except Exception as e:
            error += 1
            print(f"ERROR parsing {name}: {e}")
            continue
        if not ret:
            nonscs += 1
            continue
        scs += 1
        namecheck = _fnmck.outname(ret)
        if completecheck:
            if name in scsMandatory:
                scsMandatory.remove(name)
            elif name in scsRecommended:
                scsRecommended.remove(name)
            elif accept_old_mand:
                newnm = _fnmck.old_to_new(name)
                if newnm in scsMandatory:
                    scsMandatory.remove(newnm)
                elif newnm in scsRecommended:
                    scsRecommended.remove(newnm)
        if _fnmck.debug:
            print(f"In {name}, Out {namecheck}")
        if _fnmck.verbose:
            print(f'Pretty description: {prettyname(ret, "")}')

        if _fnmck.prefer_old:
            namecheck = _fnmck.new_to_old(namecheck)
        if namecheck != name:
            print(f"WARNING: {name} != {namecheck}")

    if completecheck:
        print(f"Found {scs} SCS flavors ({scsMandNum} mandatory, {scsRecNum} recommended), {nonscs} non-SCS flavors")
        if scsMandatory:
            print(f"Missing {len(scsMandatory)} mandatory flavors: {scsMandatory}")
            error += len(scsMandatory)
        if scsRecommended:
            print(f"Missing {len(scsRecommended)} recommended flavors: {scsRecommended}")
        return error
    return nonscs + error


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
