#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""Flavor naming checker
https://github.com/SovereignCloudStack/Operational-Docs/

Return codes:
0: Matching
1: No SCS flavor
10-19: Error in CPU:Ram spec
20-29: Error in Disk spec
30-39: Error in Hype spec
40-49: Error in optional -hwv support
50-59: Error in optional specific CPU description
60-69: Error in optional GPU spec
70-79: Unknown extension

When checking a list of flavors for completeness with respect
to mandatory flavors, we disregard non-scs flavors (code 1 above)
and only report the number of missing flavors or -- if none was found --
the sum of parsing errors (>=10) according to above scheme.

(c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
License: CC-BY-SA 4.0
"""

import sys
import os
import re

# globals
verbose = False
debug = False
completecheck = False
disallow_old = False
prefer_old = False
accept_old_mand = False

# search strings
scsPre = re.compile(r'^SCS\-')
# TODO SCSx:
# scsPre2 = re.compile(r'^SCSx\-')

# List of SCS mandatory flavors: Read from file


def usage():
    "help"
    print("Usage: flavor-name-check.py [-d] [-v] [-2] [-1] [-o] [-c] [-C mand.yaml] [-i | NAME [NAME [...]]]")
    print("Flavor name checker returns 0 if no error, 1 for non SCS flavors and 10+ for wrong flavor names")
    print("-d enables debug mode, -v outputs a verbose description, -i enters interactive input mode")
    print("-2 disallows old v1 flavor naming, -1 checks old names for completeness, -o accepts them still")
    print("-c checks the SCS names AND checks the list for completeness w.r.t. SCS mandatory flavors.")
    print("-C mand.yaml reads the mandatory flavor list from mand.yaml instead of SCS-Spec.MandatoryFlavors.yaml")
    print("Example: flavor-name-check.py -c $(openstack flavor list -f value -c Name)")
    sys.exit(2)


def to_bool(stg):
    "interpret string input as bool"
    if stg == "" or stg == "0" or stg.upper()[0] == "N" or stg.upper()[0] == "F":
        return False
    if stg == "1" or stg.upper()[0] == "Y" or stg.upper()[0] == "T":
        return True
    raise ValueError


def is_scs(name):
    "return number of matching chars of SCS- prefix"
    if scsPre.match(name):
        return 4
    # TODO SCSx: Add check for SCSx-
    # if scsPre2.match(name):
    #     return 5
    return 0


# field limiters
new_delim = "_"
old_delim = "-"
new_quant = "-"
old_quant = ":"


class Prop:
    "Class to hold properties"
    # Name of the property
    type = ""
    # regular expression to parse input
    parsestr = re.compile(r"")
    oldparsestr = None
    # attributes that are set
    pattrs = ()
    # Names of attributes; special meaning of first char of name:
    # #  => integer
    # ## => float
    # ?  => boolean
    # .  => optional string
    # #. => optional integer
    pnames = ()
    # output conversion (see comment at out() function
    outstr = ""

    def end(self, string, limiter=new_delim):
        "find delimiting limiter and cut off"
        idx = string[1:].find(limiter)
        if idx >= 1:
            return string[:idx+1]
        return string

    def parse(self, old=False):
        "Try to match parsestr; return number of chars successfully consumed"
        if old:
            pstr = self.oldparsestr
            numdel = old_quant
            lim = old_delim
        else:
            pstr = self.parsestr
            numdel = new_quant
            lim = new_delim
        if debug:
            print(self.string)
        m = pstr.match(self.string)
        if debug:
            print(m)
        if not m:
            m = pstr.match(self.end(self.string, lim))
            if not m:
                return 0
        if debug:
            print(m.groups())
        for i in range(0, len(m.groups())):
            attr = m.group(i+1)
            if not self.pnames[i]:
                continue
            if self.pnames[i][0] == "#":
                if self.pnames[i][1] == "#":
                    attr = float(attr)
                else:
                    if attr:
                        if attr[0] == numdel:
                            attr = int(attr[1:])
                        elif attr[-1] == "x":
                            attr = int(attr[:-1])
                        else:
                            attr = int(attr)
                    else:
                        attr = 0
            elif self.pnames[i][0] == "?":
                attr = bool(attr)
            self.__setattr__(self.pattrs[i], attr)
        # return len(self.string)
        return len(m.group(0))

    def __init__(self, string, forceold = False):
        "c'tor parses the string and stores the reuslts"
        # global disallow_old
        self.isold = False
        if not forceold:
            self.string = self.end(string)
            self.parsed = self.parse()
            if self.parsed:
                return
        if disallow_old:
            return
        if not self.oldparsestr:
            self.oldparsestr = self.parsestr
        self.string = self.end(string, old_delim)
        self.parsed = self.parse(True)
        if self.parsed:
            self.isold = True

    def __repr__(self):
        "verbose representation"
        if not self.parsed:
            return f" No {self.type}"
        stg = f" {self.type}:"
        for i in range(0, len(self.pattrs)):
            if not self.pnames[i]:
                continue
            fname = self.pattrs[i]
            try:
                attr = self.__getattribute__(fname)
            except AttributeError:
                attr = None
            if hasattr(self, f"tbl_{fname}"):
                self.create_dep_tbl(i, attr)
                if debug:
                    tmp = self.__getattribute__(f"tbl_{fname}")
                    print(f"  Table lookup for element '{attr}' in {tmp}")
                try:
                    attr = self.__getattribute__(f"tbl_{fname}")[attr]
                except KeyError:
                    # print(f'   Table {fname} has no attribute "{attr}"')
                    pass
            stg += " " + self.pnames[i] + ": " + str(attr) + ","
        return stg[:-1]

    def out(self):
        """Output name again:
           Using templating language with std C/Python % formatting and a few extras:
           %? outputs a string if the parameter is True, otherwise nothing (string delimited by next non-alnum char)
           %.Nf gets converted to %.0f if the number is an integer
           %1x gets converted to %ix if the number is not == 1, otherwise it's left out
           %0i gets converted to %i if the number is not == 0, otherwise it's left out
           %:i gets converted to :%i if number is non-null, otherwise left out
           """
        par = 0
        i = 0
        ostr = ""
        lst = []
        while i < len(self.outstr):
            if self.outstr[i] != '%':
                ostr += self.outstr[i]
                i += 1
                continue
            att = self.__getattribute__(self.pattrs[par])
            if self.outstr[i+1] == ".":
                ostr += self.outstr[i:i+2]
                if int(att) == att:
                    ostr += "0"
                else:
                    ostr += self.outstr[i+2]
                i += 3
                lst.append(att)
                par += 1
            elif self.outstr[i+1] == "?":
                n = i+2
                if att:
                    n = i+2
                    while n < len(self.outstr) and self.outstr[n].isalnum():
                        ostr += self.outstr[n]
                        n += 1
                else:
                    n += 1
                i = n
                par += 1
            elif self.outstr[i+1] == "1":
                if att == 1:
                    i += 3
                else:
                    ostr += "%i"
                    i += 2
                    lst.append(att)
                par += 1
            elif self.outstr[i+1] == "0":
                if att == 0:
                    i += 3
                else:
                    ostr += "%i"
                    i += 3
                    lst.append(att)
                par += 1
            elif self.outstr[i+1] == ":":   # change?
                if att:
                    ostr += "-%"
                    i += 2
                    lst.append(att)
                else:
                    i += 3
                par += 1
            else:
                ostr += self.outstr[i]
                i += 1
                lst.append(self.__getattribute__(self.pattrs[par]))
                par += 1
        if debug:
            print(f"{ostr}: {lst}")
        return ostr % tuple(lst)

    def create_dep_tbl(self, idx, val):
        "Based on choice of attr idx, can we select a table for idx+1?"
        fname = self.pattrs[idx]
        otbl = f"tbl_{fname}"
        if not hasattr(self, otbl):
            return False
        ntbl = ""
        dtbl = ""
        if idx < len(self.pattrs) - 1:
            ntbl = f"tbl_{self.pattrs[idx+1]}"
            dtbl = f"tbl_{fname}_{val}_{self.pattrs[idx+1]}"
        else:
            return False
        if hasattr(self, ntbl):
            return True
        if hasattr(self, dtbl):
            self.__setattr__(ntbl, self.__getattribute__(dtbl))
            return True
        return False

    def std_validator(self):
        """Check that all numbers are positive, all selections valid.
           return code 0 => OK, 1 ... N => error in field x-1"""
        for i in range(0, len(self.pnames)):
            val = None
            try:
                val = self.__getattribute__(self.pattrs[i])
            except AttributeError:
                pass
            # Empty entry OK
            if (self.pnames[i][0] == "." or self.pnames[i][0:2] == "#.") and not val:
                # First entry that's empty will skip the complete section
                if i == 0:
                    return 0
                continue
            # Float numbers: postitive, half
            if self.pnames[i][0:2] == "##":
                if val <= 0 or int(2*val) != 2*val:
                    return i+1
                continue
            # Integers: positive
            if self.pnames[i][0] == "#":
                if not val or val <= 0:
                    return i+1
                continue
            # Tables
            if hasattr(self, f"tbl_{self.pattrs[i]}"):
                tbl = self.__getattribute__(f"tbl_{self.pattrs[i]}")
                if val not in tbl:
                    return i+1
                self.create_dep_tbl(i, val)
                continue
        return 0

    def validate(self):
        "Hook to add checks. By default only look if parser succeeded."
        return self.std_validator()

    def input(self):
        "Interactive input"
        self.parsed = 0
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
                        val = to_bool(val)
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


class Main(Prop):
    "Class representing the first part (CPU+RAM)"
    type = "CPU-RAM"
    parsestr = re.compile(r"([0-9]*)([LVTC])(i|)\-([0-9\.]*)(u|)(o|)")
    oldparsestr = re.compile(r"([0-9]*)([LVTC])(i|):([0-9\.]*)(u|)(o|)")
    pattrs = ("cpus", "cputype", "cpuinsecure",
              "ram", "raminsecure", "ramoversubscribed")
    pnames = ("#vCPUs", "CPU type", "?Insec SMT", "##GiB RAM", "?no ECC", "?RAM Over")
    outstr = "%i%s%?i-%.1f%?u%?o"
    tbl_cputype = {"L": "LowPerf vCPU", "V": "vCPU", "T": "SMT Thread", "C": "Dedicated Core"}


class Disk(Prop):
    "Class representing the disk part (CPU+RAM)"
    type = "Disk"
    parsestr = re.compile(r"\-([0-9]*x|)([0-9]*)([nhsp]|)")
    oldparsestr = re.compile(r":([0-9]*x|)([0-9]*)([nhsp]|)")
    pattrs = ("nrdisks", "disksize", "disktype")
    pnames = ("#:NrDisks", "#.GB Disk", ".Disk type")
    outstr = "%1x%0i%s"
    tbl_disktype = {"n": "Networked", "h": "Local HDD", "s": "SSD", "p": "HiPerf NVMe"}

    def __init__(self, string, forceold=False):
        "Override c'tor, as unset nrdisks should be 1, not 0"
        super().__init__(string, forceold)
        try:
            if not self.nrdisks:
                self.nrdisks = 1
        except AttributeError:
            self.nrdisks = 1


class Hype(Prop):
    "Class repesenting Hypervisor"
    type = "Hypervisor"
    parsestr = re.compile(r"_(kvm|xen|vmw|hyv|bms)")
    oldparsestr = re.compile(r"\-(kvm|xen|vmw|hyv|bms)")
    pattrs = ("hype",)
    pnames = (".Hypervisor",)
    outstr = "%s"
    tbl_hype = {"kvm": "KVM", "xen": "Xen", "hyv": "Hyper-V", "vmw": "VMware", "bms": "Bare Metal System"}


class HWVirt(Prop):
    "Class repesenting support for hardware virtualization"
    type = "Hardware/NestedVirtualization"
    parsestr = re.compile(r"_(hwv)")
    oldparsestr = re.compile(r"\-(hwv)")
    pattrs = ("hwvirt",)
    pnames = ("?HardwareVirt",)
    outstr = "%?hwv"
    # tbl_hype = {"hwv": "HW virtualization (nested)"}


class CPUBrand(Prop):
    "Class repesenting CPU brand"
    type = "CPUBrand"
    parsestr = re.compile(r"_([izar])([0-9]*)(h*)$")
    oldparsestr = re.compile(r"\-([izar])([0-9]*)(h*)$")
    pattrs = ("cpuvendor", "cpugen", "perf")
    pnames = (".CPU Vendor", "#.CPU Gen", "Performance")
    outstr = "%s%0i%s"
    tbl_cpuvendor = {"i": "Intel", "z": "AMD", "a": "ARM", "r": "RISC-V"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"}
    # Generation decoding
    tbl_cpuvendor_i_cpugen = {0: "Unspec/Pre-Skylake", 1: "Skylake", 2: "Cascade Lake", 3: "Ice Lake"}
    tbl_cpuvendor_z_cpugen = {0: "Unspec/Pre-Zen", 1: "Zen 1", 2: "Zen 2", 3: "Zen 3", 4: "Zen 4"}
    tbl_cpuvendor_a_cpugen = {0: "Unspec/Pre-A76", 1: "A76/NeoN1", 2: "A78/X1/NeoV1", 3: "A710/NeoN2"}
    # tbl_cpuvendor_r_cpugen = {0: "SF U54", 1: "SF U74", 2: "SF U84"}


class GPU(Prop):
    "Class repesenting GPU support"
    type = "GPU"
    parsestr = re.compile(r"_([gG])([NAI])([^-]*)(\-[0-9]*|)(h*)")
    oldparsestr = re.compile(r"\-([gG])([NAI])([^:-]*)(:[0-9]*|)(h*)")
    pattrs = ("gputype", "brand", "gen", "cu", "perf")
    pnames = (".Type", ".Brand", ".Gen", "#.CU/EU/SM", "Performance")
    outstr = "%s%s%s%:i%s"
    tbl_gputype = {"g": "vGPU", "G": "Pass-Through GPU"}
    tbl_brand = {"N": "nVidia", "A": "AMD", "I": "Intel"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"}
    # Generation decoding
    tbl_brand_N_gen = {"f": "Fermi", "k": "Kepler", "m": "Maxwell", "p": "Pascal",
                       "v": "Volta", "t": "Turing", "a": "Ampere"}
    tbl_brand_A_gen = {"0.4": "GCN4.0/Polaris", "0.5": "GCN5.0/Vega", "1": "RDNA1/Navi1x", "2": "RDNA2/Navi2x"}
    tbl_brand_I_gen = {"0.9": "Gen9/Skylake", "0.95": "Gen9.5/KabyLake", "1": "Xe1/Gen12.1"}


class IB(Prop):
    "Class representing Infiniband"
    type = "Infiniband"
    parsestr = re.compile(r"_(ib)")
    oldparsestr = re.compile(r"\-(ib)")
    pattrs = ("ib",)
    pnames = ("?IB",)
    outstr = "%?ib"


def outname(cpuram, disk, hype, hvirt, cpubrand, gpu, ibd):
    "Return name constructed from tuple"
    # TODO SCSx: Differentiate b/w SCS- and SCSx-
    out = "SCS-" + cpuram.out()
    if disk.parsed:
        out += "-" + disk.out()
    if hype.parsed:
        out += "_" + hype.out()
    if hvirt.parsed:
        out += "_" + hvirt.out()
    if cpubrand.parsed:
        out += "_" + cpubrand.out()
    if gpu.parsed:
        out += "_" + gpu.out()
    if ibd.parsed:
        out += "_" + ibd.out()
    return out


def printflavor(name, item_list):
    "Output details on flavor with name name described by tuple in lst"
    print(f"Flavor: {name}")
    for item in item_list:
        print(item)
    print()


def parseone(name, cname, forceold=False, checkold=True):
    obj = cname(name, forceold)
    if checkold and not forceold and obj.isold:
        raise NameError(f"Error 80: New start, old end of flavor name {name}")
    return obj


def parsename(name):
    """Extract properties from SCS flavor name, return None (if not SCS-),
       raise NameError exception (if not conforming) or return tuple
       (cpuram, disk, hype, hvirt, cpubrand, gpu, ib)"""
    # global verbose, debug, prefer_old
    scsln = is_scs(name)
    if not scsln:
        if verbose:
            print(f"WARNING: {name}: Not an SCS flavor")
        return None
    n = name[scsln:]
    isold = False
    cpuram = parseone(n, Main, isold, False)
    if cpuram.parsed == 0:
        raise NameError(f"Error 10: Failed to parse main part of {n}")
    isold = isold or cpuram.isold
    n = n[cpuram.parsed:]
    disk = parseone(n, Disk, isold)
    n = n[disk.parsed:]
    hype = parseone(n, Hype, isold)
    n = n[hype.parsed:]
    hvirt = parseone(n, HWVirt, isold)
    n = n[hvirt.parsed:]
    # FIXME: Need to ensure we don't misparse -ib here
    cpubrand = parseone(n, CPUBrand, isold)
    n = n[cpubrand.parsed:]
    gpu = parseone(n, GPU, isold)
    n = n[gpu.parsed:]
    ibd = parseone(n, IB, isold)
    n = n[ibd.parsed:]
    if verbose:
        printflavor(name, (cpuram, disk, hype, hvirt, cpubrand, gpu, ibd))
    if isold and not prefer_old:
        print(f'WARNING: Old flavor name found: "{name}"')
    elif prefer_old and not isold:
        print(f'WARNING: New flavor name found: "{name}"')
    if n:
        print(f"ERROR: Could not parse: {n}")
        raise NameError(f"Error 70: Could not parse {n} (extras?)")

    errbase = 0
    for elem in (cpuram, disk, hype, hvirt, cpubrand, gpu, ibd):
        errbase += 10
        err = elem.validate()
        if err:
            raise NameError(f"Validation error {err + errbase} (in elem {err - 1} "
                            f"({elem.pnames[err - 1]}) in {elem.type})")

    return (cpuram, disk, hype, hvirt, cpubrand, gpu, ibd)


def inputflavor():
    "Interactively input a flavor"
    cpuram = Main("")
    cpuram.input()
    disk = Disk("")
    disk.input()
    hype = Hype("")
    hype.input()
    hvirt = HWVirt("")
    hvirt.input()
    cpubrand = CPUBrand("")
    cpubrand.input()
    gpu = GPU("")
    gpu.input()
    ibd = IB("")
    ibd.input()
    return (cpuram, disk, hype, hvirt, cpubrand, gpu, ibd)


# Path to the python script, used to search mandatory flavor YAML file
_bindir = sys.argv[0]
_bindir_pidx = _bindir.rfind('/')
if _bindir_pidx != -1:
    _bindir = (_bindir[:_bindir_pidx],)
else:
    _bindir = os.environ.get('PATH').split(':')


def new_to_old(nm):
    "v2 to v1 flavor name transformation"
    nm = nm.replace('-', ':')
    nm = nm.replace('_', '-')
    nm = nm.replace('SCS:', 'SCS-')
    return nm


def old_to_new(nm):
    "v1 to v2 flavor name transformation"
    nm = nm.replace('-', '_')
    nm = nm.replace(':', '-')
    nm = nm.replace('SCS_', 'SCS-')
    return nm


def findflvfile(fnm):
    "Search for flavor file and return found path"
    searchpath = (".", "..", *_bindir, _bindir[0] + "/..", '/opt/share/SCS')
    if fnm.rfind('/') == -1:
        for spath in searchpath:
            tnm = f"{spath}/{fnm}"
            if debug:
                print(f"Search {tnm}")
            if os.access(tnm, os.R_OK):
                fnm = tnm
                break
    return fnm


def readmandflavors(fnm):
    "Read mandatory (and recommended) flavors from passed YAML file, search in a few paths"
    import yaml
    fnm = findflvfile(fnm)
    with open(fnm, "r", encoding="UTF-8)") as fobj:
        yamldict = yaml.safe_load(fobj)
    man_ydict = yamldict["SCS-Spec"]["MandatoryFlavors"]
    rec_ydict = yamldict["SCS-Spec"]["RecommendedFlavors"]
    if prefer_old:
        for ix in range(0, len(man_ydict)):
            man_ydict[ix] = new_to_old(man_ydict[ix])
        for ix in range(0, len(rec_ydict)):
            rec_ydict[ix] = new_to_old(rec_ydict[ix])
    return man_ydict, rec_ydict


# Default file name for mandatpry flavors
mandFlavorFile = "SCS-Spec.MandatoryFlavors.yaml"


def main(argv):
    "Entry point when used as selfstanding tool"
    global verbose, debug, disallow_old, completecheck, prefer_old, accept_old_mand
    # Number of good SCS flavors
    scs = 0
    # Number of non-SCS flavors
    nonscs = 0
    # Number of errors
    error = 0

    # TODO: Use getopt for proper option parsing
    if len(argv) < 1 or argv[0] == "-h":
        usage()
    if argv[0] == "-d":
        debug = True
        argv = argv[1:]
    if argv[0] == "-v":
        verbose = True
        argv = argv[1:]
    if argv[0] == "-2":
        disallow_old = True
        argv = argv[1:]
    if argv[0] == "-1":
        prefer_old = True
        argv = argv[1:]
    if argv[0] == "-o":
        accept_old_mand = True
        argv = argv[1:]
    if argv[0] == "-c":
        completecheck = True
        scsMandatory, scsRecommended = readmandflavors(mandFlavorFile)
        scsMandNum = len(scsMandatory)
        scsRecNum = len(scsRecommended)
        if debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[1:]
    if argv[0] == "-C":
        completecheck = True
        scsMandatory, scsRecommended = readmandflavors(argv[1])
        scsMandNum = len(scsMandatory)
        scsRecNum = len(scsRecommended)
        if debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[2:]

    # Interactive input of flavor
    if len(argv) and argv[0] == "-i":
        ret = inputflavor()
        print()
        nm1 = outname(*ret)
        print(nm1)
        ret2 = parsename(nm1)
        nm2 = outname(*ret2)
        if nm1 != nm2:
            print(f"WARNING: {nm1} != {nm2}")
            # raise NameError(f"{nm} != {nm2}")
        # print(outname(*ret))
        argv = argv[1:]
        scs = 1

    # TODO: Option to get flavor list directly from API
    # TODO: Validate additional aspects
    # - vCPU, RAM, Disk (as reported via std. OpenStack API)
    # - Check extra_specs (according to TBW SCS spec)
    flavorlist = argv

    for name in flavorlist:
        if not name:
            continue
        ret = parsename(name)
        if not ret:
            nonscs += 1
            continue
        scs += 1
        namecheck = outname(*ret)
        if completecheck:
            if name in scsMandatory:
                scsMandatory.remove(name)
            elif name in scsRecommended:
                scsRecommended.remove(name)
            elif accept_old_mand:
                newnm = old_to_new(name)
                if newnm in scsMandatory:
                    scsMandatory.remove(newnm)
                elif newnm in scsRecommended:
                    scsRecommended.remove(newnm)
        if debug:
            print(f"In {name}, Out {namecheck}")

        if prefer_old:
            namecheck = new_to_old(namecheck)
        if namecheck != name:
            # raise NameError(f"{name} != {namecheck}")
            print(f"WARNING: {name} != {namecheck}")

    if completecheck:
        print(f"Found {scs} SCS flavors ({scsMandNum} mandatory, {scsRecNum} recommended), {nonscs} non-SCS flavors")
        if scsMandatory:
            print(f"Missing {len(scsMandatory)} mandatory flavors: {scsMandatory}")
            error += len(scsMandatory)
        if scsRecommended:
            print(f"Missing {len(scsRecommended)} recommended flavors: {scsRecommended}")
        return error
    return nonscs+error


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
