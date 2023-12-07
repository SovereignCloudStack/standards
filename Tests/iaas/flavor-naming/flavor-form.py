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
    print('\t  <label for="flavor"?Flavor name:</label>')
    print(f'\t  <INPUT TYPE="text" ID="flavor" NAME="flavor" SIZE=24 VALUE="{html.escape(FLAVOR_NAME, quote=True)}"/>')
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


def collect_input(self):
    "This is just for reference"
    print(self.type)
    for i in range(0, len(self.pnames)):
        tbl = None
        fname = self.pattrs[i]
        fdesc = self.pnames[i]
        if hasattr(self, f"tbl_{fname}"):
            tbl = self.__getattribute__(f"tbl_{fname}")
        if tbl:
            print(f" {fdesc} Options:")
            for key in tbl.keys():
                print(f"  {key}: {tbl[key]}")
        while True:
            print(f" {fdesc}: ", end="")
            val = input()
            try:
                if fdesc[0] == "." and not val and i == 0:
                    return
                if fdesc[0] == "?":
                    val = fnmck.to_bool(val)
                    if not val:
                        break
                elif fdesc[0:2] == "##":
                    val = float(val)
                elif fdesc[0] == "#":
                    if fdesc[1] == ":" and not val:     # change?
                        val = 1
                        break
                    if fdesc[1] == "." and not val:
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
                        self.parsed += 1
                        self.create_dep_tbl(i, val)
                        break
                    print(" INVALID!")
                    continue
            except BaseException as exc:
                print(exc)
                print(" INVALID!")
                continue
            self.parsed += 1
            break
        self.__setattr__(fname, val)


def is_checked(flag):
    if flag:
        return "checked"
    else:
        return ""


def form_attr(attr, tblopt = True):
    "This mirrors flavor-name-check.py input()"
    spec = type(attr)
    # pct = min(20, int(100/len(spec.pnames)))
    pct = 20
    # print(attr, spec)
    print(f'\t <fieldset><legend>{spec.type}</legend><br/>')
    print('\t <div id="the-whole-thing" style="position: relative; overflow: hidden;">')
    for i in range(0, len(spec.pnames)):
        tbl = None
        fname = spec.pattrs[i]
        fdesc = spec.pnames[i]
        if fdesc[0] != "?" or i == 0 or spec.pnames[i-1][0] != "?":
            print(f'\t  <div id="column" style="position: relative; width: {pct}%; float: left;">')
        # print(fname, fdesc)
        value = None
        try:
            value = attr.__getattribute__(fname)
        except AttributeError:
            pass
        # FIXME: Handle leading . qualifier
        # Table => READIO
        if hasattr(spec, f"tbl_{fname}"):
            tbl = attr.__getattribute__(f"tbl_{fname}")
        if tbl:
            print(f'\t  <label for="{fname}">{fname[0].upper()+fname[1:]}:</label><br/>')
            value_set = False
            for key in tbl.keys():
                ischk = value == key
                value_set = value_set or ischk
                print(f'\t   <input type="radio" id="{key}" name="{fname}" value="{key}" {is_checked(ischk)}/>')
                print(f'\t   <label for="{key}">{tbl[key]}</label><br/>')
            if tblopt:
                print(f'\t   <input type="radio" id="{fname}_NN" name="{fname}" value="{fname}_NN" {is_checked(not value_set)}/>')
                print(f'\t   <label for="{fname}_NN">NN</label><br/>')
        elif fdesc[0:2] == "##":
            # Float number => NUMBER
            print(f'\t  <label for="{fname}">{fdesc[2:]}</label><br/>')
            print(f'\t  <input type="number" name="{fname}" id="{fname}" min=0 value={value} size=5/>')
        elif fdesc[0] == "#":
            # Float number => NUMBER
            # FIXME: Handle : and .
            print(f'\t  <label for="{fname}">{fdesc[1:]}</label><br/>')
            print(f'\t  <input type="number" name="{fname}" id="{fname}" min=0 step=1 value={value} size=4/>')
        elif fdesc[0] == "?":
            # Bool => Checkbox
            print(f'\t  <input type="checkbox" name="{fname}" id="{fname}" {is_checked(value)}/>')
            print(f'\t  <label for="{fname}">{fdesc[1:]}</label>')
        if fdesc[0] != "?" or i == len(spec.pnames)-1 or spec.pnames[i+1][0] != "?":
            print('\t  </div>')
        else:
            print('\t  <br/>')

    print('\t </div>')
    print('\t </fieldset>')


def output_generate():
    "input details to generate SCS flavor name"
    if FLAVOR_SPEC:
        cpu, disk, hype, hvirt, cpubrand, gpu, ibd = FLAVOR_SPEC
    else:
        return
    # print("\tNot implemented yet as webform, use")
    # print('\t<tt><a href="https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/flavor-naming/flavor-name-check.py">flavor-name-check.py</a> -i</tt>')
    print('\t<br/>\n\t<FORM ACTION=/cgi-bin/flavor-form.py" METHOD="GET">')
    form_attr(cpu, False)
    print('\t<br/>The following settings are all optional and meant for highly specialized / differentiated offerings.<br/>')
    print('\t<font size=-1>')
    form_attr(disk)
    form_attr(hype)
    form_attr(hvirt)
    form_attr(cpubrand)
    form_attr(gpu)
    form_attr(ibd)
    print('\t</font>')
    print('\t</FORM>')
    # TODO: Submission


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
