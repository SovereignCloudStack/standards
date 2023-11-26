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
# import traceback
import cgi


def main(argv):
    "Entry point for cgi flavor parsing"
    import importlib
    fnmd = importlib.import_module("flavor-name-describe")
    print("Content-Type: text/html\n")
    form = cgi.FieldStorage()
    try:
        fnm = form["flavor"].value
        print(f"<h1>SCS flavor name {fnm}</h1>")
        fnmd.main((fnm,))
    except (TypeError, NameError, KeyError) as exc:
        print("ERROR<br/>")
        print(exc)
    print('<br/><br/><FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print(f' New Flavor name: <INPUT TYPE="text" NAME="flavor" SIZE=20 VALUE="{fnm}"/>')
    print('  <INPUT TYPE="submit" VALUE="Submit"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('</FORM>')
    print("\n<br/><br/><a href=\"/\">Back to main page</a>")


if __name__ == "__main__":
    main(sys.argv[1:])
