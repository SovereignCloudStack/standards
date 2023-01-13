#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-compliance-check.py
#
# (c) Eduard Itrich <eduard@itrich.net>
# (c) Kurt Garloff <kurt@garloff.de>
# SPDX-License-Identifier: Apache-2.0

"""Master SCS compliance checker
reads SCS certification requirements from e.g. scs-compatible.yaml
and performs all the checks for the specified level and outputs a
verdict from all tests (which is reflected in the exit code)
"""

# import os
import sys
# import getopt
# import time
import datetime
import subprocess
import yaml


def usage():
    "Output usage information"
    print("Usage: scs-compliance-check.py [options] compliance-spec.yaml layer [layer [layer]]")
    # TODO: options: debug, quiet, verbose
    #  single-layer
    #  specversion (default: current, other options vX or upcoming or date, etc.)


def is_valid_standard(now, stable, replace):
    "Check if now is after stable and not after replace"
    if not stable:
        return False
    if now < stable:
        return False
    if replace and now > replace:
        return False
    return True


def run_check_tool(executable, verbose=False, quiet=False):
    "Run executable and return exit code"
    compl = subprocess.run([executable, ], capture_output=True, text=True, check=False)
    if verbose:
        print(compl.stdout)
    if not quiet:
        print(compl.stderr, file=sys.stderr)
    return compl.returncode


def errcode_to_text(err):
    "translate error code to text"
    if err == 0:
        return "PASSED"
    return f"{err} ERRORS"

def dictval(dct, key):
    "Helper: Return dct[key] if it exists, None otherwise"
    if key in dct:
        return dct[key]
    return None

def search_version(layerdict, checkdate, forceversion=None):
    "Return dict with latest matching version, None if not found"
    bestdays = datetime.timedelta(999999999)    # Infinity
    bestversion = None
    for versdict in layerdict["versions"]:
        # print(f'Version {versdict["version"]}')
        if forceversion and forceversion == versdict["version"]:
            return versdict
        stabilized = dictval(versdict, "stabilized_at")
        if is_valid_standard(checkdate, stabilized, dictval(versdict, "replaced_at")):
            diffdays = checkdate - stabilized
            if diffdays < bestdays:
                bestdays = diffdays
                bestversion = versdict
    # print(f"Identified best version {bestversion}")
    return bestversion

def main(argv):
    """Entry point for the checker"""
    quiet = False
    versionoverride = None
    if len(argv) < 2:
        usage()
        return 1
    specfn = argv[0]
    with open(specfn, "r", encoding="UTF-8") as specfile:
        specdict = yaml.load(specfile, Loader=yaml.SafeLoader)
    checkdate = datetime.date.today()
    allerrors = 0
    for layer in argv[1:]:
        bestversion = search_version(specdict[layer], checkdate, versionoverride)
        if not bestversion:
            print(f"No valid standard found for {checkdate}", file=sys.stderr)
            return 2
        errors = 0
        for standard in bestversion["standards"]:
            if not quiet:
                print(f"Testing standard {standard['name']} ...")
            error = run_check_tool(standard["check_tool"])
            errors += error
            if not quiet:
                print(f"... returned {error}")
        print(f"Verdict for layer {layer}, version {bestversion['version']}: "
              f"{errcode_to_text(errors)}")
        allerrors += errors
    return allerrors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
