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
    print('\tInput an SCS flavor name such as e.g. SCS-2V-8 ...')
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    print('\t  <label for="flavor"?Flavor name:</label>')
    print(f'\t  <INPUT TYPE="text" ID="flavor" NAME="flavor" SIZE=24 VALUE="{html.escape(FLAVOR_NAME, quote=True)}"/>')
    print('\t  <INPUT TYPE="submit" VALUE="Parse"/>')
    # print('  <INPUT TYPE="reset"  VALUE="Clear"/>\n</FORM>')
    print('\t</FORM>')
    if FLAVOR_NAME:
        print(f"\t<br/><b>Flavor <tt>{html.escape(FLAVOR_NAME, quote=True)}</tt>:</b>")
        if FLAVOR_SPEC:
            print(f"\t{html.escape(fnmd.prettyname(FLAVOR_SPEC), quote=True)}")
        else:
            print("\tNot an SCS flavor")
            if ERROR:
                print(f"\t<br/>{html.escape(ERROR, quote=True)})")


def find_spec(lst, key):
    "Find index of class name key in lst, -1 means not found"
    for i in range(0, len(lst)):
        if type(lst[i]).type == key:
            return i
    return -1


def find_attr(cls, key):
    "Find index of attribute in object cls, -1 means not found"
    for i in range(0, len(cls.pattrs)):
        if cls.pattrs[i] == key:
            return i
    return -1


def generate_name(form):
    "Parse submitted form with flavor properties"
    global ERROR, FLAVOR_SPEC, FLAVOR_NAME
    ERROR = ""
    FLAVOR_NAME = ""
    FLAVOR_SPEC = (fnmck.Main("0L-0"), fnmck.Disk(""), fnmck.Hype(""), fnmck.HWVirt(""),
                   fnmck.CPUBrand(""), fnmck.GPU(""), fnmck.IB(""))
    for key, val in form.items():
        val = val[0]
        print(f'{key}={val}', file=sys.stderr)
        keypair = key.split(':')
        idx = find_spec(FLAVOR_SPEC, keypair[0])
        if idx < 0:
            ERROR = f"Unknown key {keypair[0]}"
            return None
        idx2 = find_attr(FLAVOR_SPEC[idx], keypair[1])
        if idx2 < 0:
            ERROR = f"Can not find attribute {keypair[1]} in {keypair[1]}"
            return None
        fdesc = FLAVOR_SPEC[idx].pnames[idx2]
        if val and val != "" and val != "NN" and val != "0" and not (val == "1" and fdesc[0:2] == "#:"):
            FLAVOR_SPEC[idx].parsed += 1
        # Now parse fdesc to get the right value
        if fdesc[0:2] == '##':
            setattr(FLAVOR_SPEC[idx], keypair[1], float(val))
        elif fdesc[0] == '#':
            if fdesc[1] != '.' and not int(val) > 0:
                ERROR = f"{key} must be > 0, found {val}"
                return None
            if fdesc[1] == ':' and not int(val):
                val = '1'
            setattr(FLAVOR_SPEC[idx], keypair[1], int(val))
        # TODO: Handle boolean and tables
        else:
            if val == "NN":
                val = ""
            setattr(FLAVOR_SPEC[idx], keypair[1], val)
    # Eliminate empty features
    for spec in FLAVOR_SPEC:
        if spec.pnames[0][0] == '.' and not getattr(spec, spec.pattrs[0]):
            spec.parsed = 0
            if "perf" in spec.pnames:
                setattr(spec, "perf", "")
            if "gen" in spec.pnames:
                setattr(spec, "gen", "")
    FLAVOR_NAME = fnmck.outname(*FLAVOR_SPEC)
    print(*FLAVOR_SPEC, file=sys.stderr, sep='\n')
    return FLAVOR_SPEC


def input_method(self):
    "Interactive input method for reference"
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
    "Checked attribute string"
    if flag:
        return "checked"
    else:
        return ""


def keystr(key):
    "Empty string gets converted to NN"
    if key == "":
        return "NN"
    else:
        return key


def form_attr(attr):
    """This mirrors flavor-name-check.py input(), but instead generates a web form.
       Defaults come from attr, the form is constructed from the attr's class
       attributes (like the mentioned input function). tblopt indicates whether
       chosing a value in a table is optional."""
    spec = type(attr)
    # pct = min(20, int(100/len(spec.pnames)))
    pct = 20
    # print(attr, spec)
    if ERROR:
        print(f'\tERROR: {html.escape(ERROR, quote=True)}<br/>')
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
            value = getattr(attr, fname)
        except AttributeError:
            pass
        # FIXME: Handle leading . qualifier
        # Table => READIO
        if hasattr(spec, f"tbl_{fname}"):
            tbl = getattr(attr, f"tbl_{fname}")
        if tbl:
            tblopt = False
            if fdesc[0] == '.':
                tblopt = True
                fdesc = fdesc[1:]
            # print(f'\t  <label for="{fname}">{fname[0].upper()+fname[1:]}:</label><br/>')
            print(f'\t  <label for="{fname}">{fdesc}:</label><br/>')
            value_set = False
            for key in tbl.keys():
                ischk = value == key or (not key and not value)
                value_set = value_set or ischk
                print(f'\t   <input type="radio" id="{fname}:{key}" name="{spec.type}:{fname}" value="{keystr(key)}" {is_checked(ischk)}/>')
                print(f'\t   <label for="{fname}:{key}">{tbl[key]}</label><br/>')
            if tblopt:
                print(f'\t   <input type="radio" id="{fname}:NN" name="{spec.type}:{fname}" value="NN" {is_checked(not value_set)}/>')
                print(f'\t   <label for="{fname}:NN">NN</label><br/>')
        elif fdesc[0:2] == "##":
            # Float number => NUMBER
            print(f'\t  <label for="{fname}">{fdesc[2:]}:</label><br/>')
            print(f'\t  <input type="number" name="{spec.type}:{fname}" id="{fname}" min=0 value={value} size=5/>')
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
            print(f'\t  <input type="number" name="{spec.type}:{fname}" id="{fname}" min=0 step=1 value={value} size=4/>')
        elif fdesc[0] == "?":
            # Bool => Checkbox
            print(f'\t  <input type="checkbox" name="{spec.type}:{fname}" id="{fname}" {is_checked(value)}/>')
            print(f'\t  <label for="{fname}">{fdesc[1:]}</label>')
        else:
            # FIXME: Handle dependent tables
            if fdesc[0] == '.':
                fdesc = fdesc[1:]
            print(f'\t  <label for="{fname}">{fdesc}:</label><br/>')
            print(f'\t  <input type="text" name="{spec.type}:{fname}" id="{fname}" value={value} size=4/>')
        if fdesc[0] != "?" or i == len(spec.pnames)-1 or spec.pnames[i+1][0] != "?":
            print('\t  </div>')
        else:
            print('\t  <br/>')

    print('\t </div>')
    print('\t </fieldset>')


def output_generate():
    "input details to generate SCS flavor name"
    global FLAVOR_SPEC
    if not FLAVOR_SPEC:
        print(f'\tERROR: {html.escape(ERROR, quote=True)}')
        print('\t<br/>Starting with empty template ...')
        # return
        FLAVOR_SPEC = (fnmck.Main("0L-0"), fnmck.Disk(""), fnmck.Hype(""), fnmck.HWVirt(""),
                       fnmck.CPUBrand(""), fnmck.GPU(""), fnmck.IB(""))
    cpu, disk, hype, hvirt, cpubrand, gpu, ibd = FLAVOR_SPEC
    print('\t<br/>\n\t<FORM ACTION="/cgi-bin/flavor-form.py" METHOD="GET">')
    form_attr(cpu)
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t<br/>The following settings are all optional and (except for disk) meant for highly specialized / differentiated offerings.<br/>')
    print('\t<font size=-1>')
    form_attr(disk)
    form_attr(hype)
    form_attr(hvirt)
    form_attr(cpubrand)
    form_attr(gpu)
    form_attr(ibd)
    print('\t</font><br/>')
    print('\tRemember that you are allowed to understate performance.<br/>')
    print('\t<INPUT TYPE="submit" VALUE="Generate"/><br/>')
    print('\t</FORM>')
    if FLAVOR_NAME:
        print(f"\t<br/><b>SCS flavor name: <tt>{html.escape(FLAVOR_NAME, quote=True)}</tt></b>")
        altname = fnmck.outname(cpu, disk, None, None, None, gpu, ibd)
        print(f"\t<br/><b>Short SCS flavor name: <tt>{html.escape(altname, quote=True)}</tt></b>")
    else:
        print(f'\tERROR: {html.escape(ERROR, quote=True)}')


def main(argv):
    "Entry point for cgi flavor parsing"
    print("Content-Type: text/html\n")
    form = {"flavor": [""]}
    if 'QUERY_STRING' in os.environ:
        form = urllib.parse.parse_qs(os.environ['QUERY_STRING'])
        print(f'QUERY_STRING: {os.environ["QUERY_STRING"]}', file=sys.stderr)
    # For testing
    if len(argv) > 0:
        form = {"flavor": [argv[0],]}
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
