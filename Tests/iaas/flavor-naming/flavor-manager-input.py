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
pp = importlib.import_module("flavor-name-describe")


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
    vocabulary = {"name": "name", "cpus": "0.cpus", "ram": "0.ram*1024", "disk": "1.disksize",
                  "description": "oldname"}

    def spec_dict():
        "return dict with syntax specification"
        ref = [{"field": "name", "mandatory_prefix": "SCS-"},
               {"field": "public", "default": "true"},
               {"field": "disabled", "default": "false"}]
        for key in SpecSyntax.vocabulary:
            if not fnmck.prefer_old:
                ref.append({"field": key})
        return {"reference": ref}

    def mand_dict(name, flv, prefix=""):
        "return a dict for a single flavor, input is the name and the list of properties"
        dct = {}
        for key in SpecSyntax.vocabulary:
            valsel = SpecSyntax.vocabulary[key]
            if valsel == "name":
                val = name
            elif valsel == "oldname":
                val = "alias=" + fnmck.new_to_old(name)
                val += " " + pp.prettyname(flv, prefix)
            else:
                fno, attrcalc = valsel.split('.')
                attrnm = attrcalc.split("*")[0]
                try:
                    val = flv[int(fno)].__getattribute__(attrnm)
                    if "*" in attrcalc:
                        val = int(val*int(attrcalc.split("*")[1]))
                except AttributeError:
                    val = 0
            if not fnmck.prefer_old or not valsel == "oldname":
                dct[key] = val
        return dct


def parsenames(flv_list, prefix):
    "Return list of SpecSyntax mand_dict flavors, parsing flvlist and no of errors"
    errors = 0
    fdict_list = []
    for name in flv_list:
        try:
            ret = fnmck.parsename(name)
            assert ret
            fdict_list.append(SpecSyntax.mand_dict(name, ret, prefix))
        except NameError as exc:
            print(f"{exc}", file=sys.stderr)
            errors += 1
    return fdict_list, errors


def main(argv):
    "main entry point"
    list_mode = False
    v3mode = False
    outfile = sys.stdout
    scs_mand_file = fnmck.mandFlavorFile
    errors = 0

    try:
        opts, args = getopt.gnu_getopt(argv, "hlC:1o:3",
                                       ("help", "list", "mand=", "v1prefer", "outfile=", "v3"))
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
        elif opt[0] == "-3" or opt[0] == "--v3":
            v3mode = True
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
        scs_mand_flavors = []
        scs_rec_flavors = args
    else:
        scs_mand_flavors, scs_rec_flavors = fnmck.readflavors(scs_mand_file,
                                                              v3mode, fnmck.prefer_old)

    mand_list, err = parsenames(scs_mand_flavors, "Mandatory ")
    errors += err
    rec_list, err = parsenames(scs_rec_flavors, "Recommended ")
    errors += err

    if scs_mand_flavors:
        outspec["mandatory"] = mand_list
    if scs_rec_flavors:
        outspec["recommended"] = rec_list
    # print(outspec, file=outfile)
    print(yaml.dump(outspec, default_flow_style=False, sort_keys=False), file=outfile)
    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
