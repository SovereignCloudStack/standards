#!/usr/bin/env python3
#
# Flavor naming checker
# https://github.com/SovereignCloudStack/Operational-Docs/
#
# Return codes:
# 0: Matching
# 1: No SCS flavor
# 10-19: Error in CPU:Ram spec
# 20-29: Error in Disk spec
# 30-39: Error in Hype spec
# 40-49: Error in optional -hwv support
# 50-59: Error in optional specific CPU description
# 60-69: Error in optional GPU spec
# 70-79: Unknown extension
#
# When checking a list of flavors for completeness with respect
# to mandatory flavors, we disregard non-scs flavors (code 1 above)
# and only report the number of missing flavors or -- if none was found --
# the sum of parsing errors (>=10) according to above scheme.
#
# (c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
# License: CC-BY-SA 4.0

import sys
import os
import re

# globals
verbose = False
debug = False
completecheck = False

# search strings
scsPre = re.compile(r'^SCS\-')
# TODO SCSx:
#scsPre2 = re.compile(r'^SCSx\-')

# List of SCS mandatory flavors: Read from file

# help
def usage():
    print("Usage: flavor-name-check.py [-d] [-v] [-c] [-C mand.yaml] [-i | NAME [NAME [...]]]")
    print("Flavor name checker returns 0 if no error, 1 for non SCS flavors and 10+ for wrong flavor names")
    print("-d enables debug mode, -v outputs a verbose description, -i enters interactive input mode")
    print("-c checks the SCS names AND checks the list for completeness w.r.t. SCS mandatory flavors.")
    print("-C mand.yaml reads the mandatory flavor list from mand.yaml instead of SCS-Spec.MandatoryFlavors.yaml")
    print("Example: flavor-name-check.py -c $(openstack flavor list -f value -c Name)")
    sys.exit(2)


def to_bool(stg):
    if stg == "" or stg == "0" or stg.upper()[0] == "N" or stg.upper()[0] == "F":
        return False
    if stg == "1" or stg.upper()[0] == "Y" or stg.upper()[0] == "T":
        return True
    raise ValueError


def is_scs(nm):
    "return number of matching chars of SCS- prefix"
    if scsPre.match(nm):
        return 4
    # TODO SCSx: Add check for SCSx-
    #if scsPre2.match(nm):
    #    return 5
    return 0

class Prop:
    # Name of the property
    type = ""
    # regular expression to parse input
    parsestr = re.compile(r"")
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

    def end(self, string):
        "find delimiting '-' and cut off"
        ix = string[1:].find('-')
        if ix >= 1:
            return string[:ix+1]
        else:
            return string

    def parse(self):
        "Try to match parsestr; return number of chars successfully consumed"
        if debug:
            print(self.string)
        m = self.parsestr.match(self.string)
        if debug:
            print(m)
        if not m:
            m = self.parsestr.match(self.end(self.string))
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
                        if (attr[0] == ":"):
                            attr = int(attr[1:])
                        elif (attr[-1] == "x"):
                            attr = int(attr[:-1])
                        else:
                            attr = int(attr)
                    else:
                        attr = 0
            elif self.pnames[i][0] == "?":
                attr = bool(attr)
            self.__setattr__(self.pattrs[i], attr)
        #return len(self.string)
        return len(m.group(0))

    def __init__(self, string):
        self.string = self.end(string)
        self.parsed = self.parse()

    def __repr__(self):
        "verbose representation"
        if not self.parsed:
            return f" No {self.type}"
        st = f" {self.type}:"
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
                    print(f"  Table lookup for element {attr} in {tmp}")
                try:
                    attr = self.__getattribute__(f"tbl_{fname}")[attr]
                except AttributeError:
                    pass
            st += " " + self.pnames[i] + ": " + str(attr) + ","
        return st[:-1]

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
            elif self.outstr[i+1] == ":":
                if att:
                    ostr += ":%"
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
        else:
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
                        if fdesc[1] == ":" and not val:
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
                except BaseException as e:
                    print(e)
                    print(" INVALID!")
                    continue
                self.parsed += 1
                break
            self.__setattr__(fname, val)


class Main(Prop):
    type = "CPU:RAM"
    parsestr = re.compile(r"([0-9]*)([LVTC])(i|):([0-9\.]*)(u|)(o|)")
    pattrs = ("cpus", "cputype", "cpuinsecure",
              "ram", "raminsecure", "ramoversubscribed")
    pnames = ("#vCPUs", "CPU type", "?Insec SMT", "##GiB RAM", "?no ECC", "?RAM Over")
    outstr = "%i%s%?i:%.1f%?u%?o"
    tbl_cputype = {"L": "LowPerf vCPU", "V": "vCPU", "T": "SMT Thread", "C": "Dedicated Core"}


class Disk(Prop):
    type = "Disk"
    parsestr = re.compile(r":([0-9]*x|)([0-9]*)([nhsp]|)")
    pattrs = ("nrdisks", "disksize", "disktype")
    pnames = ("#:NrDisks", "#.GB Disk", ".Disk type")
    outstr = "%1x%0i%s"
    tbl_disktype = {"n": "Networked", "h": "Local HDD", "s": "SSD", "p": "HiPerf NVMe"}

    def __init__(self, string):
        super().__init__(string)
        try:
            if not self.nrdisks:
                self.nrdisks = 1
        except:
            self.nrdisks = 1


class Hype(Prop):
    type = "Hypervisor"
    parsestr = re.compile(r"\-(kvm|xen|vmw|hyv|bms)")
    pattrs = ("hype",)
    pnames = (".Hypervisor",)
    outstr = "%s"
    tbl_hype = {"kvm": "KVM", "xen": "Xen", "hyv": "Hyper-V", "vmw": "VMware", "bms": "Bare Metal System"}


class HWVirt(Prop):
    type = "Hardware/NestedVirtualization"
    parsestr = re.compile(r"\-(hwv)")
    pattrs = ("hwvirt",)
    pnames = ("?HardwareVirt",)
    outstr = "%?hwv"
    #tbl_hype = {"hwv": "HW virtualization (nested)"}


class CPUBrand(Prop):
    type = "CPUBrand"
    parsestr = re.compile(r"\-([izar])([0-9]*)(h*)$")
    pattrs = ("cpuvendor", "cpugen", "perf")
    pnames = (".CPU Vendor", "#.CPU Gen", "Performance")
    outstr = "%s%0i%s"
    tbl_cpuvendor = {"i": "Intel", "z": "AMD", "a": "ARM", "r": "RISC-V"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"}
    # Generation decoding
    tbl_cpuvendor_i_cpugen = {0: "Unspec/Pre-Skylake", 1: "Skylake", 2: "Cascade Lake", 3: "Ice Lake"}
    tbl_cpuvendor_z_cpugen = {0: "Unspec/Pre-Zen", 1: "Zen 1", 2: "Zen 2", 3: "Zen 3", 4: "Zen 4"}
    tbl_cpuvendor_a_cpugen = {0: "Unspec/Pre-A76", 1: "A76/NeoN1", 2: "A78/X1/NeoV1", 3: "A710/NeoN2"}
    #tbl_cpuvendor_r_cpugen = {0: "SF U54", 1: "SF U74", 2: "SF U84"}


class GPU(Prop):
    type = "GPU"
    parsestr = re.compile(r"\-([gG])([NAI])([^:-]*)(:[0-9]*|)(h*)")
    pattrs = ("gputype", "brand", "gen", "cu", "perf")
    pnames = (".Type", ".Brand", ".Gen", "#.CU/EU/SM", "Performance")
    outstr = "%s%s%s%:i%s"
    tbl_gputype = {"g": "vGPU", "G": "Pass-Through GPU"}
    tbl_brand = {"N": "nVidia", "A": "AMD", "I": "Intel"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"}
    # Generation decoding
    tbl_brand_N_gen = {"f": "Fermi", "k": "Kepler", "m": "Maxwell", "p": "Pascal", "v": "Volta", "t": "Turing", "a": "Ampere"}
    tbl_brand_A_gen = {"0.4": "GCN4.0/Polaris", "0.5": "GCN5.0/Vega", "1": "RDNA1/Navi1x", "2": "RDNA2/Navi2x"}
    tbl_brand_I_gen = {"0.9": "Gen9/Skylake", "0.95": "Gen9.5/KabyLake", "1": "Xe1/Gen12.1"}


class IB(Prop):
    type = "Infiniband"
    parsestr = re.compile(r"\-(ib)")
    pattrs = ("ib",)
    pnames = ("?IB",)
    outstr = "%?ib"


def outname(cpuram, disk, hype, hvirt, cpubrand, gpu, ib):
    "Return name constructed from tuple"
    # TODO SCSx: Differentiate b/w SCS- and SCSx-
    out = "SCS-" + cpuram.out()
    if disk.parsed:
        out += ":" + disk.out()
    if hype.parsed:
        out += "-" + hype.out()
    if hvirt.parsed:
        out += "-" + hvirt.out()
    if cpubrand.parsed:
        out += "-" + cpubrand.out()
    if gpu.parsed:
        out += "-" + gpu.out()
    if ib.parsed:
        out += "-" + ib.out()
    return out


def printflavor(nm, item_list):
    "Output details on flavor with name nm described by tuple in lst"
    print(f"Flavor: {nm}")
    for item in item_list:
        print(item)
    print()


def parsename(nm):
    """Extract properties from SCS flavor name, return None (if not SCS-),
       raise NameError exception (if not conforming) or return tuple
       (cpuram, disk, hype, hvirt, cpubrand, gpu, ib)"""
    scsln = is_scs(nm)
    if not scsln:
        if verbose:
            print(f"WARNING: {nm}: Not an SCS flavor")
        return None
    n = nm[scsln:]
    cpuram = Main(n)
    if cpuram.parsed == 0:
        raise NameError(f"Error 10: Failed to parse main part of {n}")

    n = n[cpuram.parsed:]
    disk = Disk(n)
    n = n[disk.parsed:]
    hype = Hype(n)
    n = n[hype.parsed:]
    hvirt = HWVirt(n)
    n = n[hvirt.parsed:]
    # FIXME: Need to ensure we don't misparse -ib here
    cpubrand = CPUBrand(n)
    n = n[cpubrand.parsed:]
    gpu = GPU(n)
    n = n[gpu.parsed:]
    ib = IB(n)
    n = n[ib.parsed:]
    if verbose:
        printflavor(nm, (cpuram, disk, hype, hvirt, cpubrand, gpu, ib))

    if n:
        print(f"ERROR: Could not parse: {n}")
        raise NameError(f"Error 70: Could not parse {n} (extras?)")

    errbase = 0
    for el in (cpuram, disk, hype, hvirt, cpubrand, gpu, ib):
        errbase += 10
        err = el.validate()
        if err:
            raise NameError(f"Validation error {err + errbase} (in el {err - 1} ({el.pnames[err - 1]}) in {el.type})")

    return (cpuram, disk, hype, hvirt, cpubrand, gpu, ib)


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
    ib = IB("")
    ib.input()
    return (cpuram, disk, hype, hvirt, cpubrand, gpu, ib)

# Path to the python script, used to search mandatory flavor YAML file
_bindir = sys.argv[0]
_bindir_pidx = _bindir.rfind('/')
if _bindir_pidx != -1:
	_bindir = (_bindir[:_bindir_pidx],)
else:
	_bindir = os.environ('PATH').split(':')

def readmandflavors(fnm):
    "Read mandatory flavors from passed YAML file, search in a few paths"
    import yaml
    searchpath = (".",  *_bindir, '/opt/share/SCS')
    if fnm.rfind('/') == -1:
        for sp in searchpath:
            tnm = "%s/%s" % (sp, fnm)
            if debug:
                print("Search %s" % tnm)
            if os.access(tnm, os.R_OK):
                fnm = tnm
                break
    yamldict = yaml.safe_load(open(fnm, "r"))
    return yamldict["SCS-Spec"]["MandatoryFlavors"]

# Default file name for mandatpry flavors
mandFlavorFile = "SCS-Spec.MandatoryFlavors.yaml"

def main(argv):
    "Entry point when used as selfstanding tool"
    global verbose, debug, completecheck
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
    if argv[0] == "-c":
        completecheck = True
        scsMandatory = readmandflavors(mandFlavorFile)
        scsMandNum = len(scsMandatory)
        if debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[1:]
    if argv[0] == "-C":
        completecheck = True
        scsMandatory = readmandflavors(argv[1])
        scsMandNum = len(scsMandatory)
        if debug:
            print(f"Check for completeness ({scsMandNum}): {scsMandatory}")
        argv = argv[2:]

    # Interactive input of flavor
    if argv[0] == "-i":
        ret = inputflavor()
        print()
        nm = outname(*ret)
        print(nm)
        ret2 = parsename(nm)
        nm2 = outname(*ret2)
        if nm != nm2:
            print(f"WARNING: {nm} != {nm2}")
            #raise NameError(f"{nm} != {nm2}")
        #print(outname(*ret))
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
        if completecheck and name in scsMandatory:
            scsMandatory.remove(name)

        if debug:
            print(f"In {name}, Out {namecheck}")

        if namecheck != name:
            #raise NameError(f"{name} != {namecheck}")
            print(f"WARNING: {name} != {namecheck}")

    if completecheck:
        print(f"Found {scs} SCS flavors ({scsMandNum} mandatory), {nonscs} non-SCS flavors")
        if scsMandatory:
            print(f"Missing mandatory flavors: {scsMandatory}")
            return len(scsMandatory)
        else:
            return error
    else:
        return nonscs+error


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
