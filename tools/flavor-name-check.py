#!/usr/bin/env python3
#
# Flavor naming checker
# https://github.com/SovereignCloudStack/Operational-Docs/
# 
# Return codes:
# 0: Matching
# 1: No SCS flavor
# 10-19: Error in CPU spec
# 20-29: Error in Ram spec
# 30-39: Error in Disk spec
# 40-49: Error in optional specific CPU description
# 50-59: Error in optional GPU spec
# 60-69: Unknown extension
# 
# (c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
# License: CC-BY-SA 4.0


import os, sys, re

# globals
verbose = False

# search strings
scsPre = re.compile(r'^SCS\-')

# help
def usage():
    print("Usage: flavor-name-check.py [-v] NAME [NAME [...]]")
    print("Flavor name checker returns 0 if no error, 1 for non SCS flavors and 10+ for wrong flavor names")
    sys.exit(2)

def is_scs(nm):
    return scsPre.match(nm) != None


def main(argv):
    global verbose
    if len(argv) < 1:
        usage()
    if (argv[0]) == "-v":
        verbose = True
        argv = argv[1:]

    error = 0
    for name in argv:
        if not is_scs(name):
            error = 1
            if verbose:
                print("WARNING: %s: Not an SCS flavor" % name)
            continue
    return error

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
