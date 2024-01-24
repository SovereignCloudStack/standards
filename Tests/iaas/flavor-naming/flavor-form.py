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

from flavor_name_check import parser_v2, outname, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname
from flavor_name_describe import prettyname


def output_parse(namestr: str, flavorname: Flavorname, error: str):
    "output pretty description from SCS flavor name"
    print('\tInput an SCS flavor name such as e.g. SCS-2V-8 ...')
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print('\t  <label for="flavor">Flavor name:</label>')
    print(f'\t  <INPUT TYPE="text" ID="flavor" NAME="flavor" SIZE=24 VALUE="{html.escape(namestr, quote=True)}"/>')
    print('\t  <INPUT TYPE="submit" VALUE="Parse"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('\t</FORM><br/>')
    if namestr:
        print(f"\t<br/><font size=+1 color=blue><b>Flavor <tt>{html.escape(namestr, quote=True)}</tt>:</b></font>")
    if error:
        print(f"\t<br/><font color=red>{html.escape(error, quote=True)}</font>")
        return
    if flavorname:
        print(f"\t<font color=green>{html.escape(prettyname(flavorname), quote=True)}</font>")
    else:
        print("\t<font color=brown>Not an SCS flavor</font>")


def generate_name(form):
    "Parse submitted form with flavor properties"
    flavorname = Flavorname(
        cpuram=Main(), disk=Disk(), hype=Hype(), hwvirt=HWVirt(), cpubrand=CPUBrand(), gpu=GPU(), ib=IB(),
    )
    for key, values in form.items():
        val = values[0]
        print(f'{key}={val}', file=sys.stderr)
        component_key, attr_key = key.split('.')
        component = getattr(flavorname, component_key, None)
        if component is None:
            raise RuntimeError(f"Unknown key {component_key}")
        attr = getattr(component, attr_key, None)
        if attr is None:
            raise RuntimeError(f"ERROR: Can not find attribute {attr_key} in {component_key}")
        fdesc = attr.name
        if val == "NN":
            val = ""
        # Now parse fdesc to get the right value
        if fdesc[0:2] == '##':
            val = float(val)
        elif fdesc[0] == '#':
            if fdesc[1] == '.' and not val:
                val = attr.default
            else:
                val = int(val)
        elif fdesc[0] == '?':
            val = bool(val)
        setattr(component, attr_key, val)
    # Eliminate empty components
    for member_name, component in flavorname.__dict__.items():
        if not hasattr(component, "type"):
            continue
        if isinstance(component, Main):
            continue
        if isinstance(component, Disk):
            if not component.nrdisks or not component.disksize:
                setattr(flavorname, member_name, None)
            continue
        if Attr.collect(component.__class__)[0].__get__(component) is None:
            setattr(flavorname, member_name, None)
    return flavorname


def is_checked(flag):
    "Checked attribute string"
    return flag and "checked" or ""


def keystr(key):
    "Empty string gets converted to NN"
    if key is None or key == "":
        return "NN"
    return key


def make_component_form(spec, component, basepath):
    """This mirrors flavor-name-check.py input(), but instead generates a web form.

    Defaults come from component, the form is constructed from the component's class attributes.
    """
    if component is not None and not isinstance(component, spec):
        print(f"WARNING: {component} not of {spec}", file=sys.stderr)
    # pct = min(20, int(100/len(spec.pnames)))
    pct = 20
    print(f'\t <fieldset><legend>{spec.type}</legend><br/>')
    print('\t <div style="position: relative; overflow: hidden;">')
    # any consecutive Boolean fields shall be put into the same div
    check_group = False
    for attr in Attr.collect(spec):
        tbl = attr.get_tbl(component)
        fname = attr.attr
        fdesc = attr.name
        path = f"{basepath}.{fname}"
        check_box = fdesc[0] == '?'
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
                print(f'\t   <input type="radio" id="{fname}:{key}" name="{path}" value="{keystr(key)}" {is_checked(ischk)}/>')
                print(f'\t   <label for="{fname}:{key}">{tbl[key]} (<tt>{keystr(key)}</tt>)</label><br/>')
            if tblopt:
                print(f'\t   <input type="radio" id="{fname}:NN" name="{path}" value="NN" {is_checked(not value_set)}/>')
                print(f'\t   <label for="{fname}:NN">NN ()</label><br/>')
        elif fdesc[0:2] == "##":
            # Float number => NUMBER
            print(f'\t  <label for="{fname}">{fdesc[2:]}:</label><br/>')
            print(f'\t  <input type="number" name="{path}" id="{fname}" min=0 value="{value}" size=5/>')
        elif fdesc[0] == "#":
            # Float number => NUMBER
            if fdesc[1] == ".":
                if not value:
                    value = attr.default
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc[1:]}:</label><br/>')
            print(f'\t  <input type="number" name="{path}" id="{fname}" min=0 step=1 value="{value}" size=4/>')
        elif fdesc[0] == "?":
            # Bool => Checkbox
            letter = attr.letter
            print(f'\t  <input type="checkbox" name="{path}" id="{fname}" {is_checked(value)}/>')
            print(f'\t  <label for="{fname}">{fdesc[1:]} (<tt>{letter}</tt>)</label>')
        else:
            if fdesc[0] == '.':
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc}:</label><br/>')
            print(f'\t  <input type="text" name="{path}" id="{fname}" value="{value}" size=4/>')
        if not check_group:
            print('\t  </div>')
    if check_group:
        print('\t  </div>')

    print('\t </div>')
    print('\t </fieldset>')


def output_generate(namestr, flavorname, error):
    "input details to generate SCS flavor name"
    if not namestr or not flavorname or error:
        flavorname = Flavorname()
        print(f'\t<font color=red>ERROR: {html.escape(error, quote=True)}</font>')
        print('\t<br/>Starting with empty template ...')

    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    make_component_form(Main, flavorname.cpuram, "cpuram")
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t<br/>The following settings are all optional and (except for disk) meant for highly specialized / differentiated offerings.<br/>')
    print('\t<font size=-1>')
    make_component_form(Disk, flavorname.disk, "disk")
    make_component_form(Hype, flavorname.hype, "hype")
    make_component_form(HWVirt, flavorname.hwvirt, "hwvirt")
    make_component_form(CPUBrand, flavorname.cpubrand, "cpubrand")
    make_component_form(GPU, flavorname.gpu, "gpu")
    make_component_form(IB, flavorname.ib, "ib")
    print('\t</font><br/>')
    print('\tRemember that you are allowed to understate performance.<br/>')
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t</FORM>')
    if not namestr:
        return
    print(f"\t<br/><font size=+1 color=blue><b>SCS flavor name: <tt>{html.escape(namestr, quote=True)}</tt></b>")
    altname = outname(flavorname.shorten())
    print(f"\t<br/><b>Short SCS flavor name: <tt>{html.escape(altname, quote=True)}</tt></b></font>")


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
    namestr = ""
    flavorname = None
    error = ""
    try:
        if "flavor" in form:
            namestr = form["flavor"][0]
            flavorname = parser_v2(namestr)
        elif "cpuram.cpus" in form:
            flavorname = generate_name(form)
            namestr = outname(flavorname)
    except Exception as e:
        error = repr(e)
    with open("page/index.html", "r", encoding='utf-8') as infile:
        for line in infile:
            if find_parse.match(line):
                output_parse(namestr, flavorname, error)
            elif find_generate.match(line):
                output_generate(namestr, flavorname, error)
            else:
                print(line, end='')


if __name__ == "__main__":
    main(sys.argv[1:])
