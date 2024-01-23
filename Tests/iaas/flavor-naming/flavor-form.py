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

from flavor_name_check import CompatLayer, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname
from flavor_name_describe import prettyname

fnmck = CompatLayer()

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
        ERROR = f"\tERROR:\n\t{exc}"
        return ()
    ERROR = ""
    return FLAVOR_SPEC


def output_parse():
    "output pretty description from SCS flavor name"
    print('\tInput an SCS flavor name such as e.g. SCS-2V-8 ...')
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print('\t  <label for="flavor">Flavor name:</label>')
    print(f'\t  <INPUT TYPE="text" ID="flavor" NAME="flavor" SIZE=24 VALUE="{html.escape(FLAVOR_NAME, quote=True)}"/>')
    print('\t  <INPUT TYPE="submit" VALUE="Parse"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('\t</FORM><br/>')
    if FLAVOR_NAME:
        print(f"\t<br/><font size=+1 color=blue><b>Flavor <tt>{html.escape(FLAVOR_NAME, quote=True)}</tt>:</b></font>")
        if FLAVOR_SPEC:
            print(f"\t<font color=green>{html.escape(prettyname(FLAVOR_SPEC), quote=True)}</font>")
        else:
            print("\t<font color=brown>Not an SCS flavor</font>")
            if ERROR:
                print(f"\t<br/><font color=red>{html.escape(ERROR, quote=True)}</font>")


def find_spec(lst, key):
    "Find index of class name key in lst, -1 means not found"
    for i, val in enumerate(lst):
        if type(val).type == key:
            return i
    return -1


def find_attr(cls, key):
    "Find index of attribute in object cls, -1 means not found"
    for i, val in enumerate(cls.pattrs):
        if val == key:
            return i
    return -1


def generate_name(form):
    "Parse submitted form with flavor properties"
    global ERROR, FLAVOR_SPEC, FLAVOR_NAME
    ERROR = ""
    FLAVOR_NAME = ""
    FLAVOR_SPEC = Flavorname()
    for key, val in form.items():
        val = val[0]
        print(f'{key}={val}', file=sys.stderr)
        keypair = key.split(':')
        idx = find_spec(FLAVOR_SPEC, keypair[0])
        if idx < 0:
            ERROR = f"ERROR: Unknown key {keypair[0]}"
            return None
        spec = FLAVOR_SPEC[idx]
        idx2 = find_attr(spec, keypair[1])
        if idx2 < 0:
            ERROR = f"ERROR: Can not find attribute {keypair[1]} in {keypair[1]}"
            return None
        fdesc = spec.pnames[idx2]
        if val == "NN":
            val = ""
        if val and val != "" and val != "0" and not (val == "1" and fdesc[0:2] == "#:"):
            spec.parsed += 1
        # Now parse fdesc to get the right value
        if fdesc[0:2] == '##':
            setattr(spec, keypair[1], float(val))
        elif fdesc[0] == '#':
            if fdesc[1] != '.' and int(val) <= 0:
                ERROR = f"ERROR: {key} must be > 0, found {val}"
                return None
            if fdesc[1] == ':' and not int(val):
                val = '1'
            setattr(spec, keypair[1], int(val))
        elif fdesc[0] == '?':
            setattr(spec, keypair[1], bool(val))
        elif hasattr(spec, f"tbl_{keypair[1]}"):
            tbl = getattr(spec, f"tbl_{keypair[1]}")
            # print(f'tbl_{keypair[1]}: {tbl}: Search for {val}', file=sys.stderr)
            if val not in tbl and (val or fdesc[0] != '.'):
                ERROR = f'ERROR: Invalid key {val} for tbl_{keypair[1]}'
                return None
            setattr(spec, keypair[1], val)
            spec.create_dep_tbl(idx2, val)
            # if idx2 < len(spec.pattrs)-1 and hasattr(spec, f"tbl_{spec.pattrs[idx2+1]}"):
            #     print(f"Dynamically set tbl_{spec.pattrs[idx2+1]} to tbl_{spec.pattrs[idx2]}_{val}_{spec.pattrs[idx2+1]}", file=sys.stderr)
        else:
            setattr(FLAVOR_SPEC[idx], keypair[1], val)
    # Eliminate empty features
    for spec in FLAVOR_SPEC:
        if spec.pnames[0][0] == '.' and not getattr(spec, spec.pattrs[0]):
            spec.parsed = 0
            if "perf" in spec.pattrs:
                setattr(spec, "perf", "")
            if "gen" in spec.pattrs:
                setattr(spec, "gen", "")
        elif "gen" in spec.pattrs and not hasattr(spec, "gen"):
            setattr(spec, "gen", "")
            print(f'{spec.type}:gen=""', file=sys.stderr)
        elif "cpugen" in spec.pattrs and not hasattr(spec, "cpugen"):
            setattr(spec, "cpugen", 0)
            print(f'{spec.type}:cpugen=0', file=sys.stderr)

    # Debugging
    print(*FLAVOR_SPEC, file=sys.stderr, sep='\n')
    try:
        FLAVOR_NAME = fnmck.outname(*FLAVOR_SPEC)
    except (TypeError, NameError, KeyError) as exc:
        ERROR = f"\tERROR:\n\t{exc}"
        # return None
    return FLAVOR_SPEC


def is_checked(flag):
    "Checked attribute string"
    return flag and "checked" or ""


def keystr(key):
    "Empty string gets converted to NN"
    if key is None or key == "":
        return "NN"
    return key


def make_component_form(spec, component):
    """This mirrors flavor-name-check.py input(), but instead generates a web form.
       Defaults come from attr, the form is constructed from the attr's class
       attributes (like the mentioned input function). tblopt indicates whether
       chosing a value in a table is optional."""
    if component is not None and not isinstance(component, spec):
        print(f"WARNING: {component} not of {targetcls}", file=sys.stderr)
    # pct = min(20, int(100/len(spec.pnames)))
    pct = 20
    if ERROR:
        print(f'\tERROR: {html.escape(ERROR, quote=True)}<br/>')
    print(f'\t <fieldset><legend>{spec.type}</legend><br/>')
    print('\t <div style="position: relative; overflow: hidden;">')
    # any consecutive Boolean fields shall be put into the same div
    check_group = False
    for attr in Attr.collect(spec):
        tbl = attr.get_tbl(component)
        fname = attr.attr
        fdesc = attr.name
        check_box = fdesc[0] == "?"
        if check_group:
            if check_box:
                print('\t  <br/>')
            else:
                print('\t  </div>')
        else:
            print(f'\t  <div id="column" style="position: relative; width: {pct}%; float: left;">')
        check_group = check_box
        value = getattr(component, attr.attr, '')
        # Table => READIO
        if tbl:
            tblopt = fdesc[0] == '.'
            if tblopt:
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc}:</label><br/>')
            value_set = False
            for key in tbl:
                ischk = value == key or (not key and not value)
                value_set = value_set or ischk
                print(f'\t   <input type="radio" id="{fname}:{key}" name="{spec.type}:{fname}" value="{keystr(key)}" {is_checked(ischk)}/>')
                print(f'\t   <label for="{fname}:{key}">{tbl[key]} (<tt>{key}</tt>)</label><br/>')
            if tblopt:
                print(f'\t   <input type="radio" id="{fname}:NN" name="{spec.type}:{fname}" value="NN" {is_checked(not value_set)}/>')
                print(f'\t   <label for="{fname}:NN">NN ()</label><br/>')
        elif fdesc[0:2] == "##":
            # Float number => NUMBER
            print(f'\t  <label for="{fname}">{fdesc[2:]}:</label><br/>')
            print(f'\t  <input type="number" name="{spec.type}:{fname}" id="{fname}" min=0 value="{value}" size=5/>')
        elif fdesc[0] == "#":
            # Float number => NUMBER
            # Handle : and .
            if fdesc[1] == ":":
                if not value:
                    value = 1
                fdesc = fdesc[1:]
            elif fdesc[1] == '.':
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc[1:]}:</label><br/>')
            print(f'\t  <input type="number" name="{spec.type}:{fname}" id="{fname}" min=0 step=1 value="{value}" size=4/>')
        elif fdesc[0] == "?":
            # Bool => Checkbox
            letter = attr.letter
            print(f'\t  <input type="checkbox" name="{spec.type}:{fname}" id="{fname}" {is_checked(value)}/>')
            print(f'\t  <label for="{fname}">{fdesc[1:]} (<tt>{letter}</tt>)</label>')
        else:
            if fdesc[0] == '.':
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc}:</label><br/>')
            print(f'\t  <input type="text" name="{spec.type}:{fname}" id="{fname}" value="{value}" size=4/>')
        if not check_group:
            print('\t  </div>')
    if check_group:
        print('\t  </div>')

    print('\t </div>')
    print('\t </fieldset>')


def output_generate():
    "input details to generate SCS flavor name"
    global FLAVOR_SPEC
    if not FLAVOR_SPEC:
        print(f'\tERROR: {html.escape(ERROR, quote=True)}')
        print('\t<br/>Starting with empty template ...')
        # return
        FLAVOR_SPEC = Flavorname()
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    make_component_form(Main, FLAVOR_SPEC.cpuram)
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t<br/>The following settings are all optional and (except for disk) meant for highly specialized / differentiated offerings.<br/>')
    print('\t<font size=-1>')
    make_component_form(Disk, FLAVOR_SPEC.disk)
    make_component_form(Hype, FLAVOR_SPEC.hype)
    make_component_form(HWVirt, FLAVOR_SPEC.hwvirt)
    make_component_form(CPUBrand, FLAVOR_SPEC.cpubrand)
    make_component_form(GPU, FLAVOR_SPEC.gpu)
    make_component_form(IB, FLAVOR_SPEC.ib)
    print('\t</font><br/>')
    print('\tRemember that you are allowed to understate performance.<br/>')
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t</FORM>')
    if FLAVOR_NAME:
        print(f"\t<br/><font size=+1 color=blue><b>SCS flavor name: <tt>{html.escape(FLAVOR_NAME, quote=True)}</tt></b>")
        altname = fnmck.outname(Flavorname(cpuram=FLAVOR_SPEC.cpuram, disk=FLAVOR_SPEC.disk, gpu=FLAVOR_SPEC.gpu, ib=FLAVOR_SPEC.ib))
        print(f"\t<br/><b>Short SCS flavor name: <tt>{html.escape(altname, quote=True)}</tt></b></font>")
    else:
        print(f'\t<font color=red>ERROR: {html.escape(ERROR, quote=True)}</font>')


def main(argv):
    "Entry point for cgi flavor parsing"
    print("Content-Type: text/html\n")
    form = {"flavor": [""]}
    if 'QUERY_STRING' in os.environ:
        form = urllib.parse.parse_qs(os.environ['QUERY_STRING'])
        print(f'QUERY_STRING: {os.environ["QUERY_STRING"]}', file=sys.stderr)
    # For testing
    if len(argv) > 0:
        form = {"flavor": [argv[0], ]}
    find_parse    = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: PARSE\-\->[ \t]*$')
    find_generate = re.compile(r'^[ \t]*<!\-\-FLAVOR\-FORM: GENERATE\-\->[ \t]*$')
    if "flavor" in form:
        parse_name(form["flavor"][0])
    if "CPU-RAM:cpus" in form:
        generate_name(form)
    with open("page/index.html", "r", encoding='utf-8') as infile:
        for line in infile:
            print(line, end='')
            if find_parse.match(line):
                output_parse()
            elif find_generate.match(line):
                output_generate()


if __name__ == "__main__":
    main(sys.argv[1:])
