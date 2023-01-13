#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# Flavor naming checker
# https://github.com/SovereignCloudStack/Docs/Design-Docs/tools
#
# Uses the flavor-name-check.py tool
# Assumes a connection to an OpenStack tenant,
# retrieves the list of flavors from there and validates them.
# Something similar could be achieved by:
# flavor-name-check.py -c $(openstack flavor list -f value -c Name)
# In addition we check consistency by looking at the information
# provided by openstack, such as the number of vCPUs and memory.
#
# (c) Kurt Garloff <garloff@osb-alliance.com>, 12/2022
# SPDX-License-Identifier: CC-BY-SA 4.0

import os
import sys
import openstack
import importlib
import yaml
fnmck = importlib.import_module("flavor-name-check")


def usage():
    print("Usage: flavor-names-openstack.py [--os-cloud OS_CLOUD]", file=sys.stderr)
    sys.exit(1)


def main(argv):
    verbose = False
    cloud = None
    try:
        cloud = os.environ["OS_CLOUD"]
    except KeyError:
        pass
    # Note: Convert this to gnu_getopt if we get more params supported
    if len(argv):
        if argv[0] == "-v" or argv[0] == "--verbose":
            verbose = True
            argv = argv[1:]
    if len(argv):
        if argv[0][:10] == "--os-cloud":
            if len(argv[0]) > 10 and argv[0][10] == "=":
                cloud = argv[0][11:]
            elif argv[0] == "--os-cloud" and len(argv) == 2:
                cloud = argv[1]
            else:
                usage()
        else:
            usage()
    if not cloud:
        print("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
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
        if flv.name and flv.name[:4] != "SCS-":
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
            if (flv.vcpus < cpuram.cpus):
                print(f"ERROR: Flavor {flv.name} has only {flv.vcpus} vCPUs, should have >= {cpuram.cpus}", file=sys.stderr)
                err += 1
            elif (flv.vcpus > cpuram.cpus):
                print(f"WARNING: Flavor {flv.name} has {flv.vcpus} vCPUs, only needs {cpuram.cpus}", file=sys.stderr)
                warn += 1
            # RAM
            flvram = int((flv.ram + 51) / 102.4) / 10
            # Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
            if (flvram >= 10 and flvram != int(flvram) or flvram * 2 != int(flvram * 2)):
                print("WARNING: Flavor %s uses discouraged uneven size of memory %.1f GiB" % (flv.name, flvram), file=sys.stderr)
            if (flvram < cpuram.ram):
                print("ERROR: Flavor %s has only %.1f GiB RAM, should have >= %.1f GiB" % (flv.name, flvram, cpuram.ram), file=sys.stderr)
                err += 1
            elif (flvram > cpuram.ram):
                print("WARNING: Flavor %s has %.1f GiB RAM, only needs %.1f GiB" % (flv.name, flvram, cpuram.ram), file=sys.stderr)
                warn += 1
            # DISK
            accdisk = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
            # Disk could have been omitted
            if not disk.parsed:
                disk.disksize = 0
            # We have a recommendation for disk size steps
            if disk.disksize not in accdisk:
                print("WARNING: Flavor {flv.name} advertizes disk size {disk.disksize}, should have (5, 10, 20, 50, 100, 200, ...)", file=sys.stderr)
                warn += 1
            if (flv.disk < disk.disksize):
                print(f"ERROR: Flavor {flv.name} has only {flv.disk} GB root disk, should have >= {disk.disksize} GB", file=sys.stderr)
                err += 1
            elif (flv.disk > disk.disksize):
                print("WARNING: Flavor {flv.name} has {flv.disk} GB root disk, only needs {disk.disksize} GB", file=sys.stderr)
                warn += 1
            # Ev'thing checked, react to errors by putting the bad flavors in the bad bucket
            if err:
                wrongFlv.append(flv.name)
                errors += 1
            else:
                if flv.name in fnmck.scsMandatory:
                    fnmck.scsMandatory.remove(flv.name)
                    MSCSFlv.append(flv.name)
                else:
                    SCSFlv.append(flv.name)
                if warn:
                    warnFlv.append(flv.name)
        # Parser error
        except NameError as e:
            errors += 1
            wrongFlv.append(flv.name)
            print("Wrong flavor \"%s\": %s" % (flv.name, e), file=sys.stderr)
    # This makes the output more readable
    MSCSFlv.sort()
    SCSFlv.sort()
    nonSCSFlv.sort()
    wrongFlv.sort()
    warnFlv.sort()
    # We have counted errors on the fly, add missing flavors to the final result
    if (fnmck.scsMandatory):
        errors += len(fnmck.scsMandatory)
    # Produce dict for YAML reporting
    flvSCSList = {
        "MandatoryFlavorsPresent": MSCSFlv,
        "MandatoryFlavorsMissing": fnmck.scsMandatory,
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
        "MandatoryFlavorsMissing": len(fnmck.scsMandatory),
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
    Report = {cloud: {"SCSFlavorSummary": flvSCSRep, "OtherFlavorSummary": flvOthRep,
                      "TotalSummary": totSummary}}
    if verbose:
        Report[cloud]["SCSFlavorReport"] = flvSCSList
        Report[cloud]["OtherFlavorReport"] = flvOthList
    print("%s" % yaml.dump(Report, default_flow_style=False))
    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
