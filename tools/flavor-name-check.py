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
    outstr = ""

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
            fname = self.parsestr[1][i]
            try:
                attr = self.__getattribute__(fname)
            except AttributeError as e:
                attr = None
            if hasattr(self, "tbl_%s" % fname):
                if i < len(self.parsestr[1])-1:
                    nextname = self.parsestr[1][i+1]
                else:
                    nextname = None
                # dependent table?
                if nextname and not hasattr(self, "tbl_%s" % nextname) \
                            and hasattr(self, "tbl_%s_%s_%s" % (fname, attr, nextname)):
                    self.__setattr__("tbl_%s" % nextname, 
                            self.__getattribute__("tbl_%s_%s_%s" % (fname, attr, nextname)))
                    if debug:
                        print("  Set dependent table tbl_%s to %s" % (nextname, self.__getattribute__("tbl_%s" % nextname)))
                if debug:
                    print("  Table lookup for element %s in %s" % (attr, self.__getattribute__("tbl_%s" % fname)))
                attr = self.__getattribute__("tbl_%s" % fname)[attr]
            st += " " + self.parsestr[2][i] + ": " + str(attr) + ","
        return st[:-1]

    def out(self):
        par = 0
        i = 0
        ostr = ""
        lst = []
        while i < len(self.outstr):
            if self.outstr[i] != '%':
                ostr += self.outstr[i]
                i += 1
                continue
            att = self.__getattribute__(self.parsestr[1][par])
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
                n = i + 2
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
                lst.append(self.__getattribute__(self.parsestr[1][par]))
                par += 1
        if debug:
            print("%s: %s" % (ostr, lst))
        return ostr % tuple(lst)





class Main(Prop):
    type = "CPU:RAM"
    parsestr = (re.compile(r"([0-9]*)([VTC])(i|)(l|):([0-9\.]*)(u|)(o|)"),
        ("cpus", "cputype", "cpuinsecure", "cpuoversubscribed",
         "ram", "raminsecure", "ramoversubscribed"),
        ("#vCPUs", "CPU type", "?Insec SMT", "?CPU Over>3/T(5/C)", "##GiB RAM", "?no ECC", "?RAM Over"))
    outstr = "%i%s%?i%?l:%.1f%?u%?o"
    tbl_cputype = {"V": "vGPU", "T": "SMT Thread", "C": "Dedicated Core"}

class Disk(Prop):
    type = "Disk"
    parsestr = (re.compile(r":([0-9]*x|)([0-9]*)([CSLN]|)"),
        ("nrdisks", "disksize", "disktype"),
        ("#NrDisks", "#GB Disk", "Disk type"))
    outstr = "%1x%i%s"
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
    outstr = "%s%i%s"
    # TODO: Generation decoding
    tbl_cpuvendor_i_cpugen = { 0: "Pre-Skylake", 1: "Skylake", 2: "Cascade Lake", 3: "Ice Lake" }
    tbl_cpuvendor_z_cpugen = { 0: "Pre-Zen", 1: "Zen 1", 2: "Zen 2", 3: "Zen 3" }
    tbl_cpuvendor_a_cpugen = { 0: "Pre-A76", 1: "A76/NeoN1", 2: "A78/X1/NeoV1", 3: "Anext/NeoN2" }
    #tbl_cpuvendor_r_cpugen = { 0: "SF U54", 1: "SF U74", 2: "SF U84"}

class GPU(Prop):
    type = "GPU"
    parsestr = (re.compile(r"\-([gG])([nai])([^:-]*)(:[0-9]*|)(h*)"),
            ("gputype", "brand", "gen", "cu", "perf"),
            ("Type", "Brand", "Gen", "#CU", "Performance"))
    tbl_gputype = {"g": "vGPU", "G": "Pass-Through GPU"}
    tbl_brand = {"n": "nVidia", "a": "AMD", "i": "Intel"}
    tbl_perf = {"": "Std Perf", "h": "High Perf", "hh" : "Very High Perf", "hhh": "Very Very High Perf"}
    outstr = "%s%s%s%:i%s"
    # TODO: Generation decoding
    tbl_brand_n_gen = {"f": "Fermi", "k": "Kepler", "m": "Maxwell", "p": "Pascal", "v": "Volta", "t": "Turing", "a": "Ampere"}
    tbl_brand_a_gen = {"0.4": "GCN4.0/Polaris", "0.5": "GCN5.0/Vega", "1": "RDNA1/Navi1x", "2": "RDNA2/Navi2x"}
    tbl_brand_i_gen = {"0.9": "Gen9/Skylake", "0.95": "Gen9.5/KabyLake", "1": "Xe1/Gen12.1"}


class IB(Prop):
    type = "Infiniband"
    parsestr = (re.compile(r"\-(IB)"),
            ("ib",),
            ("?IB",))
    outstr = "%?IB"



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

        # Reconstruct name
        out = "SCS-" + cpuram.out()
        if disk.parsed:
            out += ":" + disk.out()
        if cpubrand.parsed:
            out += "-" + cpubrand.out()
        if gpu.parsed:
            out += "-" + gpu.out()
        if ib.parsed:
            out += "-" + ib.out()

        if debug:
            print("In %s, Out %s" % (name, out))

        if out != name:
            raise NameError("%s != %s" % (name, out))

    return error

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
