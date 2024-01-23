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

from flavor_name_check import CompatLayer, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname
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


class Inputter:
    """
    Auxiliary class for interactive input of flavor names.
    """
    def to_bool(self, s):
        """interpret string input as bool"""
        s = s.upper()
        if s == "" or s == "0" or s[0] == "N" or s[0] == "F":
            return False
        if s == "1" or s[0] == "Y" or s[0] == "T":
            return True
        raise ValueError

    def input_component(self, targetcls):
        parsed = 0
        target = targetcls()
        print(targetcls.type)
        attrs = [att for att in targetcls.__dict__.values() if isinstance(att, Attr)]
        for i, attr in enumerate(attrs):
            fdesc = attr.name
            tbl = attr.get_tbl(target)
            if tbl:
                print(f" {fdesc} Options:")
                for key, v in tbl.items():
                    print(f"  {key}: {v}")
            while True:
                print(f" {fdesc}: ", end="")
                val = input()
                try:
                    if fdesc[0] == "." and not val and i == 0:
                        return
                    if fdesc[0] == "?":
                        val = self.to_bool(val)
                        if not val:
                            break
                    elif fdesc[0:2] == "##":
                        val = float(val)
                    elif fdesc[0] == "#":
                        if fdesc[1] == ":" and not val:     # change?
                            val = 1
                            break
                        if fdesc[1] == "." and not val:
                            val = None
                            break
                        oval = val
                        val = int(val)
                        if str(val) != oval:
                            print(" INVALID!")
                            continue
                    elif tbl:
                        if fdesc[0] == "." and not val:
                            break
                        if val in tbl:
                            pass
                        elif val.upper() in tbl:
                            val = val.upper()
                        elif val.lower() in tbl:
                            val = val.lower()
                        if val in tbl:
                            parsed += 1
                            break
                        print(" INVALID!")
                        continue
                except BaseException as exc:
                    print(exc)
                    print(" INVALID!")
                    continue
                parsed += 1
                break
            attr.__set__(target, val)
        return parsed and target or None

    def __call__(self):
        flavorname = Flavorname()
        flavorname.cpuram = self.input_component(Main)
        flavorname.disk = self.input_component(Disk)
        if flavorname.disk and not (flavorname.disk.nrdisks and flavorname.disk.disksize):
            # special case...
            flavorname.disk = None
        flavorname.hype = self.input_component(Hype)
        flavorname.hvirt = self.input_component(HWVirt)
        flavorname.cpubrand = self.input_component(CPUBrand)
        flavorname.gpu = self.input_component(GPU)
        flavorname.ibd = self.input_component(IB)
        return flavorname


inputter = Inputter()


def inputflavor():
    """Interactively input a flavor"""
    return inputter()


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
        ret = _fnmck.parsename(name)
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
