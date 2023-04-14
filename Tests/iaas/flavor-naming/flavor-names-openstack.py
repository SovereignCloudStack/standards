#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:

"""Flavor naming checker
https://github.com/SovereignCloudStack/Docs/Design-Docs/tools

Uses the flavor-name-check.py tool
Assumes a connection to an OpenStack tenant,
retrieves the list of flavors from there and validates them.
Something similar could be achieved by:
flavor-name-check.py -c $(openstack flavor list -f value -c Name)
In addition we check consistency by looking at the information
provided by openstack, such as the number of vCPUs and memory.

(c) Kurt Garloff <garloff@osb-alliance.com>, 12/2022
SPDX-License-Identifier: CC-BY-SA 4.0
"""

import os
import sys
import getopt
import importlib
import yaml
import openstack
fnmck = importlib.import_module("flavor-name-check")


def usage(rcode=1):
    "help output"
    print("Usage: flavor-names-openstack.py [options]", file=sys.stderr)
    print("Options: [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)", file=sys.stderr)
    print(" [-C/--mand mand.yaml] overrides the list of mandatory flavor names", file=sys.stderr)
    print(" [-1/--v1prefer] prefer v1 flavor names (but still tolerates v2", file=sys.stderr)
    print(" [-o/--accept-old-mandatory] prefer v2 flavor names, but v1 ones can fulfill mand list", file=sys.stderr)
    print(" [-2/--v2plus] only accepts v2 flavor names, old ones result in errors", file=sys.stderr)
    print(" [-v/--verbose] [-q/--quiet] control verbosity of output", file=sys.stderr)
    print("This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD", file=sys.stderr)
    print(" and checks for the presence of the mandatory SCS flavors (read from mand.yaml)", file=sys.stderr)
    print(" and reports inconsistencies, errors etc. It returns 0 on success.", file=sys.stderr)
    sys.exit(rcode)


def main(argv):
    "Entry point -- main loop going over flavors"
    cloud = None
    verbose = False
    quiet = False
    scsMandFile = fnmck.mandFlavorFile

    try:
        cloud = os.environ["OS_CLOUD"]
    except KeyError:
        pass
    try:
        opts, args = getopt.gnu_getopt(argv, "c:C:vhq21o",
                                       ("os-cloud=", "mand=", "verbose", "help", "quiet", "v2plus",
                                        "v1prefer", "accept-old-mandatory"))
    except getopt.GetoptError as exc:
        print(f"{exc}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        elif opt[0] == "-C" or opt[0] == "--mand":
            scsMandFile = opt[1]
        elif opt[0] == "-2" or opt[0] == "--v2plus":
            fnmck.disallow_old = True
        elif opt[0] == "-1" or opt[0] == "--v1prefer":
            fnmck.prefer_old = True
        elif opt[0] == "-o" or opt[0] == "--accept-old-mandatory":
            fnmck.accept_old_mand = True
        elif opt[0] == "-v" or opt[0] == "--verbose":
            verbose = True
            # fnmck.verbose = True
        elif opt[0] == "-q" or opt[0] == "--quiet":
            quiet = True
        else:
            usage(2)
    if len(args) > 0:
        print(f"Extra arguments {str(args)}", file=sys.stderr)
        usage(1)

    scsMandatory = fnmck.readmandflavors(scsMandFile)

    if not cloud:
        print("ERROR: You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
    conn = openstack.connect(cloud=cloud, timeout=32)
    flavors = conn.compute.flavors()

    # Lists of flavors: mandatory, good-SCS, bad-SCS, non-SCS, with-warnings
    MSCSFlv = []
    SCSFlv = []
    wrongFlv = []
    nonSCSFlv = []
    warnFlv = []
    errors = 0
    for flv in flavors:
        # Skip non-SCS flavors
        if flv.name and flv.name[:4] != "SCS-":  # and flv.name[:4] != "SCSx"
            nonSCSFlv.append(flv.name)
            continue
        try:
            ret = fnmck.parsename(flv.name)
            assert ret
            # We have a successfully parsed SCS- name now
            # See if the OpenStack provided data fulfills what we
            # expect from the flavor based on its name
            err = 0
            warn = 0
            # Split list for readability
            cpuram = ret[0]
            disk = ret[1]
            # next qwould be hype, hwvirt, cpubrand, gpu, ib
            # see flavor-name-check.py: parsename()
            # vCPUS
            if flv.vcpus < cpuram.cpus:
                print(f"ERROR: Flavor {flv.name} has only {flv.vcpus} vCPUs, "
                      f"should have >= {cpuram.cpus}", file=sys.stderr)
                err += 1
            elif flv.vcpus > cpuram.cpus:
                print(f"WARNING: Flavor {flv.name} has {flv.vcpus} vCPUs, "
                      f"only needs {cpuram.cpus}", file=sys.stderr)
                warn += 1
            # RAM
            flvram = int((flv.ram + 51) / 102.4) / 10
            # Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
            if flvram >= 10 and flvram != int(flvram) or flvram * 2 != int(flvram * 2):
                print(f"WARNING: Flavor {flv.name} uses discouraged uneven size "
                      f"of memory {flvram:%.1f} GiB", file=sys.stderr)
            if flvram < cpuram.ram:
                print(f"ERROR: Flavor {flv.name} has only {flvram:.1f} GiB RAM, "
                      f"should have >= {cpuram.ram:.1f} GiB", file=sys.stderr)
                err += 1
            elif flvram > cpuram.ram:
                print(f"WARNING: Flavor {flv.name} has {flvram:.1f} GiB RAM, "
                      f"only needs {cpuram.ram:.1f} GiB", file=sys.stderr)
                warn += 1
            # DISK
            accdisk = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
            # Disk could have been omitted
            if not disk.parsed:
                disk.disksize = 0
            # We have a recommendation for disk size steps
            if disk.disksize not in accdisk:
                print(f"WARNING: Flavor {flv.name} advertizes disk size {disk.disksize}, "
                      f"should have (5, 10, 20, 50, 100, 200, ...)", file=sys.stderr)
                warn += 1
            if flv.disk < disk.disksize:
                print(f"ERROR: Flavor {flv.name} has only {flv.disk} GB root disk, "
                      f"should have >= {disk.disksize} GB", file=sys.stderr)
                err += 1
            elif flv.disk > disk.disksize:
                print(f"WARNING: Flavor {flv.name} has {flv.disk} GB root disk, "
                      f"only needs {disk.disksize} GB", file=sys.stderr)
                warn += 1
            # Ev'thing checked, react to errors by putting the bad flavors in the bad bucket
            if err:
                wrongFlv.append(flv.name)
                errors += 1
            else:
                if flv.name in scsMandatory:
                    scsMandatory.remove(flv.name)
                    MSCSFlv.append(flv.name)
                elif fnmck.accept_old_mand and fnmck.old_to_new(flv.name) in scsMandatory:
                    scsMandatory.remove(fnmck.old_to_new(flv.name))
                    MSCSFlv.append(flv.name)   # fnmck.old_to_new(flv.name)
                else:
                    SCSFlv.append(flv.name)
                if warn:
                    warnFlv.append(flv.name)
        # Parser error
        except NameError as exc:
            errors += 1
            wrongFlv.append(flv.name)
            print(f"Wrong flavor \"{flv.name}\": {exc}", file=sys.stderr)
    # This makes the output more readable
    MSCSFlv.sort()
    SCSFlv.sort()
    nonSCSFlv.sort()
    wrongFlv.sort()
    warnFlv.sort()
    # We have counted errors on the fly, add missing flavors to the final result
    if scsMandatory:
        errors += len(scsMandatory)
    # Produce dicts for YAML reporting
    flvSCSList = {
        "MandatoryFlavorsPresent": MSCSFlv,
        "MandatoryFlavorsMissing": scsMandatory,
        "OptionalFlavorsValid": SCSFlv,
        "OptionalFlavorsWrong": wrongFlv,
        "FlavorsWithWarnings": warnFlv,
    }
    flvOthList = {
        "OtherFlavors": nonSCSFlv
    }
    flvSCSRep = {
        "TotalAmount": len(MSCSFlv) + len(SCSFlv) + len(wrongFlv),
        "MandatoryFlavorsPresent": len(MSCSFlv),
        "MandatoryFlavorsMissing": len(scsMandatory),
        "OptionalFlavorsValid": len(SCSFlv),
        "OptionalFlavorsWrong": len(wrongFlv),
        "FlavorsWithWarnings": len(warnFlv)
    }
    flvOthRep = {
        "TotalAmount": len(nonSCSFlv)
    }
    totSummary = {
        "Errors": errors,
        "Warnings": len(warnFlv)
    }
    Report = {cloud: {"TotalSummary": totSummary}}
    if not quiet:
        Report[cloud]["SCSFlavorSummary"] = flvSCSRep
        Report[cloud]["OtherFlavorSummary"] = flvOthRep
    if verbose:
        Report[cloud]["SCSFlavorReport"] = flvSCSList
        Report[cloud]["OtherFlavorReport"] = flvOthList
    print(f"{yaml.dump(Report, default_flow_style=False)}")
    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
