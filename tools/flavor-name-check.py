#!/usr/bin/env python3
#
# Flavor naming checker
# https://github.com/SovereignCloudStack/Operational-Docs/
# 
# Return codes:
# 0: Matching
# 1: No SCS flavor
# 10-19: Error in CPU spec
# 20-29: Error in Ram spec
# 30-39: Error in Disk spec
# 40-49: Error in optional specific CPU description
# 50-59: Error in optional GPU spec
# 60-69: Unknown extension
# 
# (c) Kurt Garloff <garloff@osb-alliance.com>, 5/2021
# License: CC-BY-SA 4.0


import os, sys, re

# globals
verbose = False
debug = False

# search strings
scsPre = re.compile(r'^SCS\-')

# help
def usage():
    print("Usage: flavor-name-check.py [-v] NAME [NAME [...]]")
    print("Flavor name checker returns 0 if no error, 1 for non SCS flavors and 10+ for wrong flavor names")
    sys.exit(2)

def is_scs(nm):
    return scsPre.match(nm) != None

class Prop:
    type = ""
    parsestr = (re.compile(r""),(),())

    def end(self, string):
        ix = string.find('-')
        if ix >= 1:
            return string[:ix]
        else:
            return string

    def parse(self):
        if debug:
            print(self.string)
        m = self.parsestr[0].match(self.string)
        if debug:
            print(m)
        if not m:
            return 0
        if debug:
            print(m.groups())
        for i in range(0, len(m.groups())):
            attr = m.group(i+1)
            if not self.parsestr[2][i]:
                continue
            if self.parsestr[2][i][0] == "#":
                if self.parsestr[2][i][1] == "#":
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
            elif self.parsestr[2][i][0] == "?":
                attr = bool(attr)
            self.__setattr__(self.parsestr[1][i], attr)
        #return len(self.string)
        return len(m.group(0))

    def __init__(self, string):
        self.string = self.end(string)
        self.parsed = self.parse()

    def __repr__(self):
        if not self.parsed:
            return " No %s" % self.type
        st = " " + self.type + ":"
        for i in range(0, len(self.parsestr[1])):
            if not self.parsestr[2][i]:
                continue
            try:
                attr = str(self.__getattribute__(self.parsestr[1][i]))
            except AttributeError as e:
                attr = None
            if hasattr(self, "tbl_%s" % self.parsestr[1][i]):
                attr = self.__getattribute__("tbl_%s" % self.parsestr[1][i])[attr]
            st += " " + self.parsestr[2][i] + ": " + str(attr) + ","
        return st[:-1]


class Main(Prop):
    type = "CPU:RAM"
    parsestr = (re.compile(r"([0-9]*)([VTC])(i|)(l|):([0-9\.]*)(u|)(o|)"),
        ("cpus", "cputype", "cpuinsecure", "cpuoversubscribed",
         "ram", "raminsecure", "ramoversubscribed"),
        ("#vCPUs", "CPU type", "?Insec SMT", "?CPU Over", "##GiB RAM", "?no ECC", "?RAM Over"))
    tbl_cputype = {"V": "vGPU", "T": "SMT Thread", "C": "Dedicated Core"}

class Disk(Prop):
    type = "Disk"
    parsestr = (re.compile(r":([0-9]*x|)([0-9]*)([CSLN]|)"),
        ("nrdisks", "disksize", "disktype"),
        ("#NrDisks", "#GB Disk", "Disk type"))
    tbl_disktype = {"C": "Shared networked", "L": "Local", "S": "SSD", "N": "Local NVMe"}
    def __init__(self, string):
        super().__init__(string)
        try:
            if self.nrdisks == 0:
                self.nrdisks = 1
        except:
            pass

class CPUBrand(Prop):
    type = "CPUBrand"
    parsestr = (re.compile(r"\-([izar])([0-9]*)(h*)"),
            ("cpuvendor", "cpugen", "perf"),
            ("CPU Vendor", "#CPU Gen", "Performance"))
    tbl_cpuvendor = {"i": "Intel", "z": "AMD", "a": "ARM", "r": "RISC-V"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh" : "Very High Perf", "hhh": "Very Very High Perf"}
    # TODO: Generation decoding

class GPU(Prop):
    type = "GPU"
    parsestr = (re.compile(r"\-([gG])([nai])([^:-]*)(:[0-9]*|)"),
            ("gputype", "brand", "gen", "cu"),
            ("Type", "Brand", "Gen", "#CU"))
    tbl_gputype = {"g": "vGPU", "G": "Pass-Through GPU"}
    tbl_brand = {"n": "nVidia", "a": "AMD", "i": "Intel"}
    # TODO: Generation decoding

class IB(Prop):
    type = "Infiniband"
    parsestr = (re.compile(r"\-(IB)"),
            ("ib",),
            ("?IB",))



def main(argv):
    global verbose, debug
    if len(argv) < 1:
        usage()
    if (argv[0]) == "-d":
        debug = True
        argv = argv[1:]
    if (argv[0]) == "-v":
        verbose = True
        argv = argv[1:]

    error = 0
    for name in argv:
        if not is_scs(name):
            if not error:
                error = 1
            if verbose:
                print("WARNING: %s: Not an SCS flavor" % name)
            continue
        n = name[4:]
        cpuram = Main(n)
        if cpuram.parsed == 0:
            error = 10
        n = n[cpuram.parsed:]
        disk = Disk(n)
        n = n[disk.parsed:]
        cpubrand = CPUBrand(n)
        n = n[cpubrand.parsed:]
        gpu = GPU(n)
        n = n[gpu.parsed:]
        ib = IB(n)
        n = n[ib.parsed:]
        if verbose:
            print("Flavor: %s" % name)
            print(cpuram)
            print(disk)
            print(cpubrand)
            print(gpu)
            print(ib)
            print()

        if n:
            print("ERROR: Remainder: %s" % n)
            error = 60

    return error

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
