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

# import os
import sys
import re
# import traceback
# TODO: Replace cgi by urllib, cgi is deprecated
import cgi


class TestForm:
    "Class for testing via cmd line"
    def __init__(self, fnm):
        self.value = fnm


def parse_form(form):
    "output pretty description from SCS flavor name"
    import importlib
    fnmd = importlib.import_module("flavor-name-describe")
    fnm = ""
    try:
        fnm = form["flavor"].value
    except KeyError:
        pass
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print(f'\t  Flavor name: <INPUT TYPE="text" NAME="flavor" SIZE=24 VALUE="{fnm}"/>')
    print('\t  <INPUT TYPE="submit" VALUE="Submit"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('\t</FORM>')
    if fnm:
        print("\t<br/><b>Flavor</b>")
        try:
            fnmd.main((fnm,))
        except (TypeError, NameError, KeyError) as exc:
            print(f"\tERROR<br/>\n\t{exc}")


def parse_generate(form):
    "input details to generate SCS flavor name"
    print("\tNot implemented yet as webform, use")
    print('\t<tt><a href="https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/flavor-naming/flavor-name-check.py">flavor-name-check.py</a> -i</tt>')


def main(argv):
    "Entry point for cgi flavor parsing"
    print("Content-Type: text/html\n")
    form = cgi.FieldStorage()
    # For testing
    if len(argv) > 0:
        form = {"flavor": TestForm(argv[0])}
    find_parse    = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: PARSE\-\->[ \t]*$')
    find_generate = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: GENERATE\-\->[ \t]*$')
    with open("page/index.html", "r", encoding='utf-8') as infile:
        for line in infile:
            print(line, end='')
            if find_parse.match(line):
                parse_form(form)
            elif find_generate.match(line):
                parse_generate(form)


if __name__ == "__main__":
    main(sys.argv[1:])
