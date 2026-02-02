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

from functools import partial
import html
import logging
import os
import re
import sys
import urllib.parse

from flavor_names import parser_v2, outname, Attr, Main, Disk, Hype, HWVirt, CPUBrand, GPU, IB, Flavorname, \
    Inputter, lookup_user_input, prettyname


logger = logging.getLogger(__name__)


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
    """Parse submitted form with flavor properties"""
    formdata = {key: val[0] for key, val in form.items()}
    inputter = Inputter(partial(lookup_user_input, formdata))
    flavorname = inputter()
    # validate formdata for extraneous fields
    for key, val in formdata.items():
        if val == "NN" or key in ("disk.nrdisks", "disk.disktype"):
            continue
        component_key, attr_key = key.split('.')
        component = getattr(flavorname, component_key, None)
        if component is None:
            raise RuntimeError(f"Unknown key {component_key}")
        attr = getattr(component.__class__, attr_key, None)
        if attr is None:
            raise RuntimeError(f"ERROR: Can not find attribute {attr_key} in {component_key}")
    return flavorname


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
        path = f"{spec.component_name}.{attr.attr}"
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
                ischk = value == key or (key == "NN" and value is None)
                value_set = value_set or ischk
                print(f'\t   <input type="radio" id="{fname}:{key}" name="{path}" value="{keystr(key)}" {is_checked(ischk)}/>')
                print(f'\t   <label for="{fname}:{key}">{tbl[key]} (<tt>{"" if key is None else key}</tt>)</label><br/>')
            if tblopt:
                print(f'\t   <input type="radio" id="{fname}:NN" name="{path}" value="NN" {is_checked(not value_set)}/>')
                print(f'\t   <label for="{fname}:NN">NN (<tt></tt>)</label><br/>')
        elif fdesc[0:2] == "##":
            # Float number => NUMBER
            print(f'\t  <label for="{fname}">{fdesc[2:]}:</label><br/>')
            # FIXME: This is a hack: we hardcode step=2 or 0.5 knowing that RAM is the only float
            step = 2 if value >= 10 else 0.5
            print(f'\t  <input type="number" name="{path}" id="{fname}" min=0 step={step} value="{value}" size=5/>')
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
    make_component_form(Main, flavorname.cpuram)
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t<br/>The following settings are all optional and (except for disk) meant for highly specialized / differentiated offerings.<br/>')
    print('\t<font size=-1>')
    make_component_form(Disk, flavorname.disk)
    make_component_form(Hype, flavorname.hype)
    make_component_form(HWVirt, flavorname.hwvirt)
    make_component_form(CPUBrand, flavorname.cpubrand)
    make_component_form(GPU, flavorname.gpu)
    make_component_form(IB, flavorname.ib)
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
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
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
        logger.exception(error)
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
