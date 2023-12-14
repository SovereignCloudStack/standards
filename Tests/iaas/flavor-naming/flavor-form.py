#!/usr/bin/env python3
# Little wrapper to output flavor pretty description
# from a CGI form with flavor
#
# (c) Kurt Garloff <kurt@garloff.de>, 11/2023
# SPDX-License-Identifier: CC-BY-SA-4.0
"""
flavor-form.py
CGI script to get passed flavor from a html form (GET)
and parses it according to SCS flavor naming.
It returns an error (sometimes with a useful error message)
or a human-readable description of the flavor.
"""

import os
import sys
import re
import urllib.parse
import html
import importlib
fnmck = importlib.import_module("flavor-name-check")

# Global variables
FLAVOR_NAME = ""
FLAVOR_SPEC = ()
ERROR = ""


def parse_name(fnm):
    "return tuple with flavor description"
    global FLAVOR_SPEC, FLAVOR_NAME, ERROR
    FLAVOR_NAME = fnm
    try:
        FLAVOR_SPEC = fnmck.parsename(fnm)
    except (TypeError, NameError, KeyError) as exc:
        ERROR = f"\tERROR<br/>\n\t{exc}"
        return ()
    ERROR = ""
    return FLAVOR_SPEC


def output_parse():
    "output pretty description from SCS flavor name"
    fnmd = importlib.import_module("flavor-name-describe")
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print(f'\t  Flavor name: <INPUT TYPE="text" NAME="flavor" SIZE=24 VALUE="{html.escape(FLAVOR_NAME, quote=True)}"/>')
    print('\t  <INPUT TYPE="submit" VALUE="Submit"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('\t</FORM>')
    if FLAVOR_NAME:
        print(f"\t<br/><b>Flavor {html.escape(FLAVOR_NAME, quote=True)}:</b>")
        if FLAVOR_SPEC:
            print(f"\t{html.escape(fnmd.prettyname(FLAVOR_SPEC), quote=True)}")
        else:
            print("\tNot an SCS flavor")
            if ERROR:
                print(f"\t<br/>{html.escape(ERROR, quote=True)})")


def output_generate():
    "input details to generate SCS flavor name"
    print("\tNot implemented yet as webform, use")
    print('\t<tt><a href="https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/flavor-naming/flavor-name-check.py">flavor-name-check.py</a> -i</tt>')


def main(argv):
    "Entry point for cgi flavor parsing"
    print("Content-Type: text/html\n")
    form = {"flavor": [""]}
    if 'QUERY_STRING' in os.environ:
        form = urllib.parse.parse_qs(os.environ['QUERY_STRING'])
    # For testing
    if len(argv) > 0:
        form = {"flavor": [argv[0],]}
    find_parse    = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: PARSE\-\->[ \t]*$')
    find_generate = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: GENERATE\-\->[ \t]*$')
    if "flavor" in form:
        parse_name(form["flavor"][0])
    with open("page/index.html", "r", encoding='utf-8') as infile:
        for line in infile:
            print(line, end='')
            if find_parse.match(line):
                output_parse()
            elif find_generate.match(line):
                output_generate()


if __name__ == "__main__":
    main(sys.argv[1:])
