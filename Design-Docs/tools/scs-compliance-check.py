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
The tests require the OpenStack SDK (and in the future probably
also k8s python bindings) to be installed and access to IaaS
(for the iaas layer tests) via configure clouds/secure.yaml
which are passed in OS_CLOUD (or --os-cloud cmdline param).
In the future als access to a cluster with KUBECONFIG pointing
to a working file.
The goal is to work without any special admin privileges.
(If we find things that can't be tested as normal user, we
would split these tests out.)
"""

import os
import sys
import getopt
# import time
import datetime
import subprocess
import yaml


def usage():
    "Output usage information"
    print("Usage: scs-compliance-check.py [options] compliance-spec.yaml layer [layer [layer]]")
    print("Options: -v/--verbose: More verbose output")
    print(" -q/-quiet: Don't output anythin but errors")
    print(" -s/--single-layer: Don't perform require checks for dependantr layers")
    print(" -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today")
    print(" -V/--version VERS: Force version VERS of the standard (instead of deriving from date)")
    print(" -c/--os-cloud CLOUD: Use specified cloud env (instead of OS_CLOUD env var)")


def is_valid_standard(now, stable, obsolete):
    "Check if now is after stable and not after obsolete"
    if not stable:
        return False
    if now < stable:
        return False
    if obsolete and now > obsolete:
        return False
    return True


def run_check_tool(executable, args, verbose=False, quiet=False):
    "Run executable and return exit code"
    exe = [executable, ]
    if args:
        exe.extend(args.split(" "))
    # print(f"{exe}")
    # compl = subprocess.run(exe, capture_output=True, text=True, check=False)
    compl = subprocess.run(exe, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding='UTF-8', check=False)
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
        if is_valid_standard(checkdate, stabilized, dictval(versdict, "obsoleted_at")):
            diffdays = checkdate - stabilized
            if diffdays < bestdays:
                bestdays = diffdays
                bestversion = versdict
    # print(f"Identified best version {bestversion}")
    if forceversion and bestversion and not bestversion["version"] == forceversion:
        print(f"Wanted version {forceversion} which was not found")
        sys.exit(3)
    return bestversion


def optparse(argv):
    "Parse options. Return (args, verbose, quiet, checkdate, version, singlelayer)."
    verbose = False
    quiet = False
    checkdate = datetime.date.today()
    version = None
    single_layer = False
    try:
        opts, args = getopt.gnu_getopt(argv, "hvqd:V:sc:",
                                       ("help", "verbose", "quiet", "date=", "version=",
                                        "single-layer", "os-cloud="))
    except getopt.GetoptError as exc:
        print(f"Option error: {exc}", file=sys.stderr)
        usage()
        sys.exit(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage()
            sys.exit(0)
        elif opt[0] == "-v" or opt[0] == "--verbose":
            verbose = True
        elif opt[0] == "-q" or opt[0] == "--quiet":
            quiet = True
        elif opt[0] == "-d" or opt[0] == "--date":
            checkdate = datetime.date.fromisoformat(opt[1])
        elif opt[0] == "-V" or opt[0] == "--version":
            version = opt[1]
        elif opt[0] == "-s" or opt[0] == "--single-layer":
            single_layer = True
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            os.environ["OS_CLOUD"] = opt[1]
        else:
            print(f"Error: Unknown argument {opt[0]}", file=sys.stderr)
    if len(args) < 2:
        usage()
        sys.exit(1)
    return (args, verbose, quiet, checkdate, version, single_layer)


def main(argv):
    """Entry point for the checker"""
    args, verbose, quiet, checkdate, version, single_layer = optparse(argv)
    with open(args[0], "r", encoding="UTF-8") as specfile:
        specdict = yaml.load(specfile, Loader=yaml.SafeLoader)
    allerrors = 0
    if "depends_on" in specdict and not single_layer:
        print("WARNING: depends_on not yet implemented!", file=sys.stderr)
    # Iterate over layers
    for layer in args[1:]:
        bestversion = search_version(specdict[layer], checkdate, version)
        if not bestversion:
            print(f"No valid standard found for {checkdate}", file=sys.stderr)
            return 2
        errors = 0
        if not quiet:
            print(f"Testing {layer} standard version {bestversion['version']}")
        if "standards" not in bestversion:
            print(f"WARNING: No standards defined yet for {layer} version {bestversion['version']}",
                  file=sys.stderr)
        for standard in bestversion["standards"]:
            optional = False
            optstr = ""
            if "condition" in standard and standard['condition'] == 'optional':
                optional = True
                optstr = "optional "
            # TODO: Check for misspelling of condition
            if not quiet:
                print("*******************************************************")
                print(f"Testing {optstr}standard {standard['name']} ...")
                print(f"Reference: {standard['url']} ...")
            if "check_tool" not in standard:
                print(f"WARNING: No compliance check tool implemented yet for {standard['name']}")
                error = 0
            else:
                args = dictval(standard, 'check_tool_args')
                error = run_check_tool(standard["check_tool"], args, verbose, quiet)
            if not optional:
                errors += error
            if not quiet and "check_tool" in standard:
                print(f"... returned {error}")
            for kwd in standard:
                if kwd not in ('check_tool', 'check_tool_args', 'url', 'name', 'condition'):
                    print(f"ERROR in spec: standard.{kwd} is an unknown keyword", file=sys.stderr)
        # TODO: Option to write output-report.yaml
        if not quiet:
            print("*******************************************************")
        print(f"Verdict for cloud {os.environ['OS_CLOUD']}, layer {layer}, "
              f"version {bestversion['version']}: {errcode_to_text(errors)}")
        allerrors += errors
    return allerrors


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
