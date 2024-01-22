#!/usr/bin/env python3
import os
import os.path
import re
import sys

import yaml


class TypeCheck:
    def __call__(self, attr, value):
        raise ValueError(f"{attr} can not be set to {value}")


class OptionalCheck(TypeCheck):
    def __init__(self, check):
        self.check = check

    def __call__(self, attr, value):
        if value is None:
            return
        self.check(attr, value)


class TblCheck(TypeCheck):
    def __init__(self, tbl):
        self.tbl = tbl

    def __call__(self, attr, value):
        if value not in self.tbl:
            raise ValueError(f"{attr} can not be set to {value!r}; must be one of {tuple(self.tbl)}")


class BoolCheck(TypeCheck):
    def __call__(self, attr, value):
        if not isinstance(value, bool):
            raise ValueError(f"{attr} can not be set to {value!r}; must be boolean")


class IntCheck(TypeCheck):
    def __call__(self, attr, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{attr} can not be set to {value!r}; must be positive integer")


class FloatCheck(TypeCheck):
    def __call__(self, attr, value):
        if not isinstance(value, float) or value <= 0 or int(2 * value) != 2 * value:
            raise ValueError(f"{attr} can not be set to {value!r}; must be positive multiple of 0.5")


class Attr:
    typ = None
    default = None

    def __init__(self, name, default=None):
        self.name = name
        if default != self.default:
            self.default = default  # instance attribute will override class attibute
        # the following will be set via __set_name__
        self.attr = None
        self._attr = None

    def get_tbl(self, obj):
        return None

    def validate(self, val):
        if self.typ is None:
            return
        self.typ(self.attr, val)

    def __set_name__(self, owner, name):
        self.attr = name
        self._attr = '_' + name

    def __get__(self, obj, objclass=None):
        if obj is None:
            return self
        return getattr(obj, self._attr, self.default)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self._attr, value)


class IntAttr(Attr):
    typ = IntCheck()


class OptIntAttr(Attr):
    typ = OptionalCheck(IntCheck())


class FloatAttr(Attr):
    typ = FloatCheck()


class BoolAttr(Attr):
    typ = BoolCheck()


class TblAttr(Attr):
    def __init__(self, name, tbl, default=None):
        super().__init__(name, default)
        self.tbl = tbl
        self.typ = TblCheck(tbl)

    def get_tbl(self, obj):
        return self.tbl


class DepTblAttr(Attr):
    def __init__(self, name, key_attr, deptbl, default=None):
        super().__init__(name, default)
        self.key_attr = key_attr
        self.deptbl = deptbl
        self.typs = {key: TblCheck(tbl) for key, tbl in deptbl.items()}

    def get_tbl(self, obj):
        return self.deptbl.get(self.key_attr.__get__(obj))

    def __set__(self, obj, value):
        self.typs[self.key_attr.__get__(obj)](self.attr, value)
        super().__set__(obj, value)


class Main:
    """Class representing the first part (CPU+RAM)"""
    type = "CPU-RAM"
    cpus = IntAttr("#vCPUs")
    cputype = TblAttr("CPU type", {"L": "LowPerf vCPUs", "V": "vCPUs", "T": "SMT Threads", "C": "Dedicated Cores"})
    cpuinsecure = BoolAttr("?Insec SMT")
    ram = FloatAttr("##GiB RAM")
    raminsecure = BoolAttr("?no ECC")
    ramoversubscribed = BoolAttr("?RAM Over")


class Disk:
    """Class representing the disk part"""
    type = "Disk"
    nrdisks = IntAttr("#:NrDisks")
    nrdisks.default = 1
    disksize = OptIntAttr("#.GB Disk")
    disktype = TblAttr(".Disk type", {'': '', "n": "Networked", "h": "Local HDD", "s": "SSD", "p": "HiPerf NVMe"})


class Hype:
    """Class repesenting Hypervisor"""
    type = "Hypervisor"
    hype = TblAttr(".Hypervisor", {'': '', "kvm": "KVM", "xen": "Xen", "hyv": "Hyper-V", "vmw": "VMware", "bms": "Bare Metal System"})


class HWVirt:
    """Class repesenting support for hardware virtualization"""
    type = "Hardware/NestedVirtualization"
    hwvirt = BoolAttr("?HardwareVirt")


class CPUBrand:
    """Class repesenting CPU brand"""
    type = "CPUBrand"
    cpuvendor = TblAttr(".CPU Vendor", {"i": "Intel", "z": "AMD", "a": "ARM", "r": "RISC-V"})
    cpugen = DepTblAttr("#.CPU Gen", cpuvendor, {
        "i": {0: "Unspec/Pre-Skylake", 1: "Skylake", 2: "Cascade Lake", 3: "Ice Lake", 4: "Sapphire Rapids"},
        "z": {0: "Unspec/Pre-Zen", 1: "Zen 1", 2: "Zen 2", 3: "Zen 3", 4: "Zen 4"},
        "a": {0: "Unspec/Pre-A76", 1: "A76/NeoN1", 2: "A78/X1/NeoV1", 3: "A710/NeoN2"},
    })
    perf = TblAttr("Performance", {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"})


class GPU:
    """Class repesenting GPU support"""
    type = "GPU"
    gputype = TblAttr(".Type", {"g": "vGPU", "G": "Pass-Through GPU"})
    brand = TblAttr(".Brand", {'': '', "N": "nVidia", "A": "AMD", "I": "Intel"})
    gen = DepTblAttr(".Gen", brand, {
        '': {'': ''},
        "N": {'': '', "f": "Fermi", "k": "Kepler", "m": "Maxwell", "p": "Pascal",
              "v": "Volta", "t": "Turing", "a": "Ampere", "l": "AdaLovelace"},
        "A": {'': '', "0.4": "GCN4.0/Polaris", "0.5": "GCN5.0/Vega", "1": "RDNA1/Navi1x", "2": "RDNA2/Navi2x", "3": "RDNA3/Navi3x"},
        "I": {'': '', "0.9": "Gen9/Skylake", "0.95": "Gen9.5/KabyLake", "1": "Xe1/Gen12.1", "2": "Xe2"},
    })
    cu = OptIntAttr("#.CU/EU/SM")
    perf = TblAttr("Performance", {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"})


class IB:
    """Class representing Infiniband"""
    type = "Infiniband"
    ib = BoolAttr("?IB")


class Flavorname:
    def __init__(self):
        self.cpuram = None
        self.disk = None
        self.hype = None
        self.hwvirt = None
        self.cpubrand = None
        self.gpu = None
        self.ib = None


class Inputter:
    def to_bool(self, s):
        """interpret string input as bool"""
        s = s.upper()
        if s == "" or s == "0" or s[0] == "N" or s[0] == "F":
            return False
        if s == "1" or s[0] == "Y" or s[0] == "T":
            return True
        raise ValueError

    def input_component(self, targetcls):
        parsed = 0
        target = targetcls()
        print(targetcls.type)
        attrs = [att for att in targetcls.__dict__.values() if isinstance(att, Attr)]
        for i, attr in enumerate(attrs):
            fname = attr.attr
            fdesc = attr.name
            tbl = attr.get_tbl(target)
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
                        val = self.to_bool(val)
                        if not val:
                            break
                    elif fdesc[0:2] == "##":
                        val = float(val)
                    elif fdesc[0] == "#":
                        if fdesc[1] == ":" and not val:     # change?
                            val = 1
                            break
                        if fdesc[1] == "." and not val:
                            val = None
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
                            parsed += 1
                            break
                        print(" INVALID!")
                        continue
                except BaseException as exc:
                    print(exc)
                    print(" INVALID!")
                    continue
                parsed += 1
                break
            attr.__set__(target, val)
        return parsed and target or None

    def __call__(self):
        flavorname = Flavorname()
        flavorname.cpuram = self.input_component(Main)
        flavorname.disk = self.input_component(Disk)
        if flavorname.disk and not (flavorname.disk.nrdisk and flavorname.disk.disksize):
            # special case...
            flavorname.disk = None
        flavorname.hype = self.input_component(Hype)
        flavorname.hvirt = self.input_component(HWVirt)
        flavorname.cpubrand = self.input_component(CPUBrand)
        flavorname.gpu = self.input_component(GPU)
        flavorname.ibd = self.input_component(IB)
        return flavorname


class Outputter:
    prefix = "SCS-"
    cpuram = "%i%s%?i-%f%?u%?o"
    disk = "-%1x%0i%s"
    hype = "_%s"
    hwvirt = "_%?hwv"
    cpubrand = "_%s%0i%s"
    gpu = "_%s%s%s%:i%s"
    ib = "_%?ib"

    def output_component(self, pattern, component, parts):
        if component is None:
            return
        attr_iter = iter([att for att in component.__class__.__dict__.values() if isinstance(att, Attr)])
        i = 0
        while i < len(pattern):
            j = i
            while i < len(pattern) and pattern[i] != "%":
                i += 1
            if i > j:
                parts.append(pattern[j:i])
            if i == len(pattern):
                break
            i += 1  # skip %
            attr = next(attr_iter)
            value = attr.__get__(component)
            if pattern[i] == "?":
                j = i + 1
                while j < len(pattern) and pattern[j].isalnum():
                    j += 1
                if value:
                    parts.append(pattern[i + 1:j])
                i = j - 1
            elif pattern[i] == "s":
                parts.append(str(value))
            elif pattern[i] == "i":
                parts.append(str(value))
            elif pattern[i:i+2] == "0i":
                if value != int(pattern[i]):
                    parts.append(str(value))
                i += 1
            elif pattern[i:i+2] == ":i":
                if value:
                    parts.append(f"-{value}")
                i += 1
            elif pattern[i:i+2] == "1x":
                if value != int(pattern[i]):
                    parts.append(f"{value}x")
                i += 1
            elif pattern[i] == "f":
                if value == int(value):
                    parts.append(f"{value:.0f}")
                else:
                    parts.append(f"{value:.1f}")
            else:
                print(pattern, i)
                raise RuntimeError("Pattern problem")
            i += 1
    
    def __call__(self, flavorname):
        parts = [self.prefix]
        self.output_component(self.cpuram, flavorname.cpuram, parts)
        self.output_component(self.disk, flavorname.disk, parts)
        self.output_component(self.hype, flavorname.hype, parts)
        self.output_component(self.hwvirt, flavorname.hwvirt, parts)
        self.output_component(self.cpubrand, flavorname.cpubrand, parts)
        self.output_component(self.gpu, flavorname.gpu, parts)
        self.output_component(self.ib, flavorname.ib, parts)
        return "".join(parts)


class SyntaxV1:
    prefix = "SCS-"
    cpuram = re.compile(r"([0-9]*)([LVTC])(i|):([0-9\.]*)(u|)(o|)")
    disk = re.compile(r":(?:([0-9]*)x|)([0-9]*)([nhsp]|)")
    hype = re.compile(r"\-(kvm|xen|vmw|hyv|bms)")
    hwvirt = re.compile(r"\-(hwv)")
    cpubrand = re.compile(r"\-([izar])([0-9]*)(h*)")
    gpu = re.compile(r"\-([gG])([NAI])([^:-]*)(?::([0-9]*)|)(h*)")
    ib = re.compile(r"\-(ib)")


class SyntaxV2:
    prefix = "SCS-"
    cpuram = re.compile(r"([0-9]*)([LVTC])(i|)\-([0-9\.]*)(u|)(o|)")
    disk = re.compile(r"\-(?:([0-9]*)x|)([0-9]*)([nhsp]|)")
    hype = re.compile(r"_(kvm|xen|vmw|hyv|bms)")
    hwvirt = re.compile(r"_(hwv)")
    cpubrand = re.compile(r"_([izar])([0-9]*)(h*)")
    gpu = re.compile(r"_([gG])([NAI])([^-]*)(?:\-([0-9]*)|)(h*)")
    ib = re.compile(r"_(ib)")


class ComponentParser:
    def __init__(self, parsestr, targetcls):
        self.parsestr = parsestr
        self.targetcls = targetcls

    def parse(self, s, pos):
        m = self.parsestr.match(s, pos)
        if m is None:
            return None, pos
        match_attr = [att for att in self.targetcls.__dict__.values() if isinstance(att, Attr)]
        groups = m.groups()
        if len(groups) != len(match_attr):
            raise ValueError(f"unexpected number of matching groups: {match_attr} vs {groups}")
        t = self.targetcls()
        for attr, group in zip(match_attr, groups):
            if attr.name[:2] == "##":
                attr.__set__(t, float(group))
            elif attr.name[:1] == "#":
                attr.__set__(t, int(group) if group else attr.default)
            elif attr.name[:1] == "?":
                attr.__set__(t, bool(group))
            else:
                attr.__set__(t, group)
        return t, pos + len(m.group(0))


class Parser:
    def __init__(self, syntax):
        self.prefix = syntax.prefix
        self.cpuram = ComponentParser(syntax.cpuram, Main)
        self.disk = ComponentParser(syntax.disk, Disk)
        self.hype = ComponentParser(syntax.hype, Hype)
        self.hwvirt = ComponentParser(syntax.hwvirt, HWVirt)
        self.cpubrand = ComponentParser(syntax.cpubrand, CPUBrand)
        self.gpu = ComponentParser(syntax.gpu, GPU)
        self.ib = ComponentParser(syntax.ib, IB)

    def __call__(self, s, pos=0):
        if not s[pos:].startswith(self.prefix):
            return
        pos += len(self.prefix)
        flavorname = Flavorname()
        for key, p in self.__dict__.items():
            if not isinstance(p, ComponentParser):
                continue
            t, pos = p.parse(s, pos)
            setattr(flavorname, key, t)
        if flavorname.cpuram is None:
            raise ValueError(f"Error 10: Failed to parse main part of {s}")
        if pos != len(s):
            raise ValueError(f"Failed to parse name {s} to completion (after {pos})")
        return flavorname


parser_v1 = Parser(SyntaxV1)
parser_v2 = Parser(SyntaxV2)
inputter = Inputter()
outputter = Outputter()


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


class CompatLayer:
    """
    This class provides the functionality that was previously imported via
    
    fnmck = importlib.import_module("flavor-name-check")

    Instead, you now do
    
    fnmck = CompatLayer()
    
    A few adaptation are necessary though because this package uses `Flavorname`
    instead of the old `tuple` of `Prop`s.
    """
    def __init__(self):
        self.verbose = False
        self.debug = False
        self.quiet = False
        self.disallow_old = False
        self.prefer_old = False
        self.v3_flv = False
        self.mandFlavorFile = "SCS-Spec.MandatoryFlavors.yaml"
        bindir = os.path.basename(sys.argv[0])
        self.searchpath = (bindir, ) if bindir else os.environ['PATH'].split(':')

    def parsename(self, namestr):
        """
        Parse flavor name: returns None (if non-SCS) or Flavorname instance
        raises exception if name appears SCS, but not conforming to syntax
        """
        is_old = False
        try:
            flavorname = parser_v2(namestr)
        except Exception:
            if self.disallow_old:
                raise
            flavorname = parser_v1(namestr)
            is_old = True
        if not self.quiet and flavorname is not None and self.prefer_old != is_old:
            print(f"WARNING: flavor name not v{2 - self.prefer_old}: {namestr}")
        return flavorname

    def outname(self, flavorname):
        outputter(flavorname)

    def inputflavor():
        """Interactively input a flavor"""
        return inputter()

    def old_to_new(self, nm):
        return old_to_new(nm)

    def new_to_old(self, nm):
        return new_to_old(nm)

    def findflvfile(self, fnm):
        """Search for flavor file and return found path"""
        searchpath = (".", "..", *self.searchpath, self.searchpath[0] + "/..", '/opt/share/SCS')
        if os.path.dirname(fnm):
            return fnm
        for spath in searchpath:
            tnm = os.path.join(spath, fnm)
            if self.debug:
                print(f"Search {tnm}")
            if os.access(tnm, os.R_OK):
                return tnm

    def readflavors(self, fnm, v3mode):
        """Read mandatory and recommended flavors from passed YAML file"""
        fnm = self.findflvfile(fnm)
        if self.debug:
            print(f"DEBUG: Reading flavors from {fnm}")
        with open(fnm, "r", encoding="UTF-8)") as fobj:
            yamldict = yaml.safe_load(fobj)
        # Translate to old names in-place
        if self.prefer_old:
            for name_type in yamldict["SCS-Spec"].values():
                for i, name in enumerate(name_type):
                    name_type[i] = new_to_old(name)
        mand = yamldict["SCS-Spec"]["MandatoryFlavors"]
        recd = yamldict["SCS-Spec"]["RecommendedFlavors"]
        if v3mode:
            mand.extend(yamldict["SCS-Spec"].get("MandatoryFlavorsV3", ()))
            recd.extend(yamldict["SCS-Spec"].get("RecommendedFlavorsV3", ()))
            return mand, recd
        else:
            return [*mand, *recd], []


if __name__ == "__main__":
    namestr = "SCS-16T-64-3x10_GNa-64_ib"
    print(namestr)
    print(outputter(parser_v1("SCS-16T:64:3x10s-GNa:64-ib")))
    print(namestr == outputter(parser_v2(namestr)))
    print(outputter(inputter()))
