#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""Flavor manager spec generator
https://github.com/SovereignCloudStack/standards/Tests/iaas/flavor-naming

We have a list of mandatory flavors.
The flavor-manager however does not have the capability to parse the names
and derive the properties from them. So we generate a yaml file that has
this information desired by it.

(c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
License: CC-BY-SA 4.0
"""

import sys
# import os
import getopt
import importlib
import yaml

fnmck = importlib.import_module("flavor-name-check")


def usage(rcode=1):
    "help output"
    print("Usage: flavor-manager-input.py [options]")
    print("Options: -l use list of flavors from the command line instead of reading them")
    print("-C flavor-list.yaml: Use this file instead of SCS-Spec.MandatoryFlavors.yaml")
    print("-1: Use v1 flavor names instead of v2")
    print("-o outfile: write yaml file to outfile instead of stdout")
    sys.exit(rcode)


class SpecSyntax:
    "Abstraction for the output flavor-manager spec file"
    vocabulary = {"name": "name", "cpus": "0.cpus", "ram": "0.ram*1024", "disk": "1.disksize"}

    def spec_dict():
        "return dict with syntax specification"
        ref = [{"field": "name", "mandatory_prefix": "SCS-"},
               {"field": "public", "default": "true"},
               {"field": "disabled", "default": "false"}]
        for key in SpecSyntax.vocabulary:
            ref.append({"field": key})
        return {"reference": ref}

    def mand_dict(name, flv):
        "return a dict for a single flavor, input is the name and the list of properties"
        dct = {}
        for key in SpecSyntax.vocabulary:
            valsel = SpecSyntax.vocabulary[key]
            if valsel == "name":
                val = name
            else:
                fno, attrcalc = valsel.split('.')
                attrnm = attrcalc.split("*")[0]
                try:
                    val = flv[int(fno)].__getattribute__(attrnm)
                    if "*" in attrcalc:
                        val = int(val*int(attrcalc.split("*")[1]))
                except AttributeError:
                    val = 0
            dct[key] = val
        return dct


def main(argv):
    "main entry point"
    list_mode = False
    outfile = sys.stdout
    scs_mand_file = fnmck.mandFlavorFile
    errors = 0

    try:
        opts, args = getopt.gnu_getopt(argv, "hlC:1o:",
                                       ("help", "list", "mand=", "v1prefer", "outfile="))
    except getopt.GetoptError as exc:
        print(f"{exc}", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-l" or opt[0] == "--list":
            list_mode = True
        elif opt[0] == "-C" or opt[0] == "--mand":
            scs_mand_file = opt[1]
        elif opt[0] == "-1" or opt[0] == "--v1prefer":
            fnmck.prefer_old = True
            pass
        elif opt[0] == "-o" or opt[0] == "--outfile":
            outfile = open(opt[1], "w", encoding="UTF-8")
        else:
            usage(2)
    if len(args) > 0 and not list_mode:
        usage(3)

    outspec = SpecSyntax.spec_dict()
    if list_mode:
        scs_mand_flavors = args
        flavor_type = "optional"
    else:
        scs_mand_flavors = fnmck.readmandflavors(scs_mand_file)
        flavor_type = "mandatory"

    olist = []
    for name in scs_mand_flavors:
        try:
            ret = fnmck.parsename(name)
            assert ret
            olist.append(SpecSyntax.mand_dict(name, ret))
        except NameError as exc:
            print(f"{exc}", file=sys.stderr)
            errors += 1
    outspec[flavor_type] = olist
    # print(outspec, file=outfile)
    print(yaml.dump(outspec, default_flow_style=False, sort_keys=False), file=outfile)
    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
