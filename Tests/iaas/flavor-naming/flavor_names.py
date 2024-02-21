#!/usr/bin/env python3
import os
import os.path
import re
import sys
from pathlib import Path
from typing import Optional

import yaml


CPUTYPE_KEY = {'L': 'crowded-core', 'V': 'shared-core', 'T': 'dedicated-thread', 'C': 'dedicated-core'}
DISKTYPE_KEY = {'n': 'network', 'h': 'hdd', 's': 'ssd', 'p': 'nvme'}
HERE = Path(__file__).parent


class TypeCheck:
    """class for validating the type of some attribute within a flavor name"""
    def __call__(self, attr: str, value):
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
    """class to represent one attribute, such as brand, of one component, such as gpu, of a flavor name"""
    typ = None
    default = None

    @staticmethod
    def collect(cls):
        """return all instances of `Attr` in the dict of given cls"""
        return [att for att in cls.__dict__.values() if isinstance(att, Attr)]

    def __init__(self, name, default=None, letter=None):
        self.name = name
        self.letter = letter
        if default != self.default:
            self.default = default  # instance attribute will override class attibute
        # the following will be set automatically via __set_name__
        self.attr = None
        self._attr = None

    def get_tbl(self, obj):
        return None

    def validate(self, val):
        if self.typ is None:
            return
        self.typ(self.attr, val)

    # the following methods make this class a `Descriptor`,
    # see <https://docs.python.org/3/howto/descriptor.html>

    def __set_name__(self, owner, name):
        if self.letter is None:
            self.letter = name
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
    component_name = "cpuram"
    cpus = IntAttr("#vCPUs")
    cputype = TblAttr("CPU type", {"L": "LowPerf vCPUs", "V": "vCPUs", "T": "SMT Threads", "C": "Dedicated Cores"})
    cpuinsecure = BoolAttr("?Insec SMT", letter="i")
    ram = FloatAttr("##GiB RAM")
    raminsecure = BoolAttr("?no ECC", letter="u")
    ramoversubscribed = BoolAttr("?RAM Over", letter="o")


class Disk:
    """Class representing the disk part"""
    type = "Disk"
    component_name = "disk"
    nrdisks = IntAttr("#.NrDisks", default=1)
    disksize = OptIntAttr("#.GB Disk")
    disktype = TblAttr("Disk type", {'': '(unspecified)', "n": "Networked", "h": "Local HDD", "s": "SSD", "p": "HiPerf NVMe"})


class Hype:
    """Class repesenting Hypervisor"""
    type = "Hypervisor"
    component_name = "hype"
    hype = TblAttr(".Hypervisor", {"kvm": "KVM", "xen": "Xen", "hyv": "Hyper-V", "vmw": "VMware", "bms": "Bare Metal System"})


class HWVirt:
    """Class repesenting support for hardware virtualization"""
    type = "Hardware/NestedVirtualization"
    component_name = "hwvirt"
    hwvirt = BoolAttr("?HardwareVirt", letter="hwv")


class CPUBrand:
    """Class repesenting CPU brand"""
    type = "CPUBrand"
    component_name = "cpubrand"
    cpuvendor = TblAttr("CPU Vendor", {"i": "Intel", "z": "AMD", "a": "ARM", "r": "RISC-V"})
    cpugen = DepTblAttr("#.CPU Gen", cpuvendor, {
        "i": {None: '(unspecified)', 0: "Unspec/Pre-Skylake", 1: "Skylake", 2: "Cascade Lake", 3: "Ice Lake", 4: "Sapphire Rapids"},
        "z": {None: '(unspecified)', 0: "Unspec/Pre-Zen", 1: "Zen 1", 2: "Zen 2", 3: "Zen 3", 4: "Zen 4"},
        "a": {None: '(unspecified)', 0: "Unspec/Pre-A76", 1: "A76/NeoN1", 2: "A78/X1/NeoV1", 3: "A710/NeoN2"},
    })
    perf = TblAttr("Performance", {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"})


class GPU:
    """Class repesenting GPU support"""
    type = "GPU"
    component_name = "gpu"
    gputype = TblAttr("Type", {"g": "vGPU", "G": "Pass-Through GPU"})
    brand = TblAttr("Brand", {"N": "nVidia", "A": "AMD", "I": "Intel"})
    gen = DepTblAttr("Gen", brand, {
        "N": {'': '(unspecified)', "f": "Fermi", "k": "Kepler", "m": "Maxwell", "p": "Pascal",
              "v": "Volta", "t": "Turing", "a": "Ampere", "l": "AdaLovelace"},
        "A": {'': '(unspecified)', "0.4": "GCN4.0/Polaris", "0.5": "GCN5.0/Vega", "1": "RDNA1/Navi1x", "2": "RDNA2/Navi2x", "3": "RDNA3/Navi3x"},
        "I": {'': '(unspecified)', "0.9": "Gen9/Skylake", "0.95": "Gen9.5/KabyLake", "1": "Xe1/Gen12.1", "2": "Xe2"},
    })
    cu = OptIntAttr("#.CU/EU/SM")
    perf = TblAttr("Performance", {"": "Std Perf", "h": "High Perf", "hh": "Very High Perf", "hhh": "Very Very High Perf"})


class IB:
    """Class representing Infiniband"""
    type = "Infiniband"
    component_name = "ib"
    ib = BoolAttr("?IB")


class Flavorname:
    """A flavor name; merely a bunch of components"""
    def __init__(
        self, cpuram: Main = None, disk: Disk = None, hype: Hype = None, hwvirt: HWVirt = None,
        cpubrand: CPUBrand = None, gpu: GPU = None, ib: IB = None
    ):
        self.cpuram = cpuram
        self.disk = disk
        self.hype = hype
        self.hwvirt = hwvirt
        self.cpubrand = cpubrand
        self.gpu = gpu
        self.ib = ib

    def shorten(self):
        """return canonically shortened name as recommended in the standard"""
        if self.hype is None and self.hwvirt is None and self.cpubrand is None:
            return self
        return Flavorname(cpuram=self.cpuram, disk=self.disk, gpu=self.gpu, ib=self.ib)


class Outputter:
    """
    Auxiliary class for serializing `Flavorname` instances.

    Use the global instance `outputter` (defined below) like so: `namestr = outputter(flavorname)`.

    Using templating language similar to % formatting:
       %? outputs attribute's letter if the attribute is True, otherwise nothing
       %f gets converted to %.0f if the number is an integer, otherwise %.1f
       %x gets converted to %ix if the number is not the default, otherwise it's left out
       %0 gets converted to %i if the number is non-null and != 0, otherwise it's left out
       %- gets converted to -%i if number is non-null, otherwise left out
    """

    prefix = "SCS-"
    cpuram = "%i%s%?-%f%?%?"
    disk = "-%x%0%s"
    hype = "_%s"
    hwvirt = "_%?"
    cpubrand = "_%s%0%s"
    gpu = "_%s%s%s%-%s"
    ib = "_%?"

    def output_component(self, pattern, component, parts):
        if component is None:
            return
        attr_iter = iter(Attr.collect(component.__class__))
        i = 0
        while i < len(pattern):
            j = pattern.find("%", i)
            parts.append(pattern[i:j])
            if j == -1:
                break
            i = j + 1  # skip %
            attr = next(attr_iter)
            value = attr.__get__(component)
            if pattern[i] == "?":
                if value:
                    parts.append(attr.letter)
            elif pattern[i] in ("s", "i"):
                parts.append(str(value))
            elif pattern[i] == "0":
                if value is not None and value != 0:
                    parts.append(str(value))
            elif pattern[i] == "-":
                if value:
                    parts.append(f"-{value}")
            elif pattern[i] == "x":
                if value != attr.default:
                    parts.append(f"{value}x")
            elif pattern[i] == "f":
                if value == int(value):
                    parts.append(f"{value:.0f}")
                else:
                    parts.append(f"{value:.1f}")
            else:
                print(pattern, i)
                raise RuntimeError("Pattern problem")
            i += 1

    def __call__(self, flavorname: Flavorname) -> str:
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
    """
    This class bundles the regular expressions that comprise the syntax for v1 of the standard.
    """
    prefix = "SCS-"
    cpuram = re.compile(r"([0-9]*)([LVTC])(i|):([0-9\.]*)(u|)(o|)")
    disk = re.compile(r":(?:([0-9]*)x|)([0-9]*)([nhsp]|)")
    hype = re.compile(r"\-(kvm|xen|vmw|hyv|bms)")
    hwvirt = re.compile(r"\-(hwv)")
    # cpubrand needs final lookahead assertion to exclude confusion with _ib extension
    cpubrand = re.compile(r"\-([izar])([0-9]*)(h*)(?=$|\-)")
    gpu = re.compile(r"\-([gG])([NAI])([^:h]*)(?::([0-9]+)|)(h*)")
    ib = re.compile(r"\-(ib)")

    @staticmethod
    def from_v2(nm: str) -> str:
        """v2 to v1 flavor name transformation"""
        return nm.replace('-', ':').replace('_', '-').replace('SCS:', 'SCS-')


class SyntaxV2:
    """
    This class bundles the regular expressions that comprise the syntax for v2 of the standard.

    The change vs. v1 concerns the delimiters only and is best understood by looking at
    the classmethods `SyntaxV2.from_v1` and `SyntaxV1.from_v2`.

    Note that the syntax hasn't changed since v2, so this class is still valid.
    """
    prefix = "SCS-"
    cpuram = re.compile(r"([0-9]*)([LVTC])(i|)\-([0-9\.]*)(u|)(o|)")
    disk = re.compile(r"\-(?:([0-9]*)x|)([0-9]*)([nhsp]|)")
    hype = re.compile(r"_(kvm|xen|vmw|hyv|bms)")
    hwvirt = re.compile(r"_(hwv)")
    # cpubrand needs final lookahead assertion to exclude confusion with _ib extension
    cpubrand = re.compile(r"_([izar])([0-9]*)(h*)(?=$|_)")
    gpu = re.compile(r"_([gG])([NAI])([^\-h]*)(?:\-([0-9]+)|)(h*)")
    ib = re.compile(r"_(ib)")

    @staticmethod
    def from_v1(nm: str) -> str:
        """v1 to v2 flavor name transformation"""
        return nm.replace('-', '_').replace(':', '-').replace('SCS_', 'SCS-')


class ParseCtx:
    """Auxiliary class used during parsing to hold current position in the string"""
    def __init__(self, s: str, pos=0):
        self.s = s
        self.pos = pos


class ComponentParser:
    """Auxiliary class for parsing a single component of a flavor name"""
    def __init__(self, parsestr: re.Pattern, targetcls):
        self.parsestr = parsestr  # re.Pattern as defined in `SyntaxV1` or `SyntaxV2`
        self.targetcls = targetcls  # component class such as `Main` or `Disk`

    def parse(self, ctx: ParseCtx):
        m = self.parsestr.match(ctx.s, ctx.pos)
        if m is None:
            return
        match_attr = Attr.collect(self.targetcls)
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
        ctx.pos += len(m.group(0))
        return t


class Parser:
    """
    Auxiliary class for parsing flavorname strings.

    Use the global instances `parser_v1` and `parser_v2` (defined below) like so:
    `flavorname = parser_v2(namestr)`.
    """

    def __init__(self, vstr, syntax):
        self.vstr = vstr
        self.prefix = syntax.prefix
        self.cpuram = ComponentParser(syntax.cpuram, Main)
        self.disk = ComponentParser(syntax.disk, Disk)
        self.hype = ComponentParser(syntax.hype, Hype)
        self.hwvirt = ComponentParser(syntax.hwvirt, HWVirt)
        self.cpubrand = ComponentParser(syntax.cpubrand, CPUBrand)
        self.gpu = ComponentParser(syntax.gpu, GPU)
        self.ib = ComponentParser(syntax.ib, IB)

    def __call__(self, s: str, pos=0) -> Flavorname:
        if not s[pos:].startswith(self.prefix):
            return
        ctx = ParseCtx(s, pos + len(self.prefix))
        flavorname = Flavorname()
        flavorname.cpuram = self.cpuram.parse(ctx)
        if flavorname.cpuram is None:
            raise ValueError("Failed to parse main part")
        flavorname.disk = self.disk.parse(ctx)
        flavorname.hype = self.hype.parse(ctx)
        flavorname.hwvirt = self.hwvirt.parse(ctx)
        flavorname.cpubrand = self.cpubrand.parse(ctx)
        flavorname.gpu = self.gpu.parse(ctx)
        flavorname.ib = self.ib.parse(ctx)
        if ctx.pos != len(s):
            raise ValueError(f"Extra characters: {s[ctx.pos:]}")
        return flavorname


def _convert_user_input(idx, attr, target, val):
    """auxiliary function that converts user-input string `val` to the target attribute type"""
    fdesc = attr.name
    tbl = attr.get_tbl(target)
    if not val and idx == 0 and not isinstance(target, (Main, Disk)):
        # BAIL: if you don't want an extension, supply empty first attr
        return val
    if fdesc[0] == "?":
        val = val.upper()
        if val == "" or val == "OFF" or val == "0" or val[0] == "N" or val[0] == "F":
            val = False
        elif val == "1" or val == "ON" or val[0] == "Y" or val[0] == "T":
            val = True
        else:
            raise ValueError
    elif fdesc[0:2] == "##":
        val = float(val)
    elif fdesc[0] == "#":
        if fdesc[1] == "." and not val:
            val = attr.default
        else:
            oval = val
            val = int(val)
            if str(val) != oval:
                raise ValueError(val)
    elif tbl:
        if val in tbl:
            pass
        elif val.upper() in tbl:
            val = val.upper()
        elif val.lower() in tbl:
            val = val.lower()
        else:
            raise ValueError(f"{val!r} not in {tbl}")
    return val


def ask_user_input(idx, attr, target):
    """strategy function for `Inputter` class: ask user for input"""
    fdesc = attr.name
    tbl = attr.get_tbl(target)
    if idx == 0:
        print(target.type)
    if tbl:
        print(f" {fdesc} Options:")
        for key, v in tbl.items():
            print(f"  {'' if key is None else key}: {v}")
    while True:
        print(f" {fdesc}: ", end="")
        val = input()
        try:
            val = _convert_user_input(idx, attr, target, val)
        except BaseException as exc:
            print(" " + str(exc))
            print(" INVALID!")
        else:
            break
    return val


def lookup_user_input(formdata, idx, attr, target):
    """strategy function for `Inputter` class: look up input in `formdata` dict

    Use like so: `form_inputter = Inputter(partial(lookup_user_input, formdata))`
    """
    val = formdata.get(f"{target.component_name}.{attr.attr}")
    if val is None or val == "NN":
        val = ""
    return _convert_user_input(idx, attr, target, val)


class Inputter:
    """Auxiliary class for interactive input of flavor names."""
    def __init__(self, obtain_input=ask_user_input):
        self.ask_user_input = staticmethod(obtain_input)

    def input_component(self, targetcls):
        target = targetcls()
        attrs = [att for att in targetcls.__dict__.values() if isinstance(att, Attr)]
        for idx, attr in enumerate(attrs):
            val = self.ask_user_input(idx, attr, target)
            if not val and idx == 0 and not isinstance(target, (Main, Disk)):
                # BAIL: if you don't want an extension, supply empty first attr
                return
            attr.__set__(target, val)
        return target

    def __call__(self):
        flavorname = Flavorname()
        flavorname.cpuram = self.input_component(Main)
        flavorname.disk = self.input_component(Disk)
        if flavorname.disk and not (flavorname.disk.nrdisks and flavorname.disk.disksize):
            # special case...
            flavorname.disk = None
        flavorname.hype = self.input_component(Hype)
        flavorname.hwvirt = self.input_component(HWVirt)
        flavorname.cpubrand = self.input_component(CPUBrand)
        flavorname.gpu = self.input_component(GPU)
        flavorname.ib = self.input_component(IB)
        return flavorname


parser_v1 = Parser("v1", SyntaxV1)
parser_v2 = Parser("v2", SyntaxV2)
parser_v3 = Parser("v3", SyntaxV2)  # this is the same as parser_v2 except for the vstr
outname = outputter = Outputter()
inputflavor = inputter = Inputter()


def flavorname_to_dict(flavorname: Flavorname) -> dict:
    name_v2 = outputter(flavorname)
    result = {
        'cpus': flavorname.cpuram.cpus,
        'cpu-type': CPUTYPE_KEY[flavorname.cpuram.cputype],
        'ram': flavorname.cpuram.ram,
        'name-v1': SyntaxV1.from_v2(name_v2),
        'name-v2': name_v2,
    }
    if flavorname.disk:
        result['disk'] = flavorname.disk.disksize
        for i in range(flavorname.disk.nrdisks):
            result[f'disk{i}-type'] = DISKTYPE_KEY[flavorname.disk.disktype or 'n']
    return result


def _collectattrs(alist, new):
    "collect list of attitbutes"
    if alist:
        alist += f", {new}"
    else:
        alist = new
    return alist


def _tbl_out(item, kind, check=False):
    """Look up table value (attach space), skip if entry is 0 or empty string and check is set"""
    val = getattr(item, kind)
    if check and not val:
        return ""
    try:
        return getattr(item.__class__, kind).get_tbl(item)[val] + " "
    except KeyError:
        return str(val) + " "


def prettyname(flavorname, prefix=""):
    """Output a human-readable flavor description"""
    # CPU (number, type, attributes)
    stg = f"{prefix}SCS flavor with {flavorname.cpuram.cpus} "
    if flavorname.cpubrand:
        stg += _tbl_out(flavorname.cpubrand, "perf", True)
        stg += _tbl_out(flavorname.cpubrand, "cpuvendor")
        stg += _tbl_out(flavorname.cpubrand, "cpugen", True)
    else:
        stg += "generic x86-64 "
    stg += _tbl_out(flavorname.cpuram, "cputype")
    if flavorname.cpuram.cpuinsecure:
        stg += "(insecure) "
    # RAM (amount, attributes)
    stg += f"with {flavorname.cpuram.ram} GiB RAM "
    alist = ""
    if flavorname.cpuram.raminsecure:
        alist = _collectattrs(alist, "noECC")
    if flavorname.cpuram.ramoversubscribed:
        alist = _collectattrs(alist, "oversubscribed")
    if alist:
        stg += f"({alist}) "
    # Hypervisor, HVirt
    if flavorname.hype:
        stg += f'on {_tbl_out(flavorname.hype, "hype")}'
    if flavorname.hwvirt:
        stg += 'with HW virt '
    # Disk
    if flavorname.disk:
        stg += "and "
        stg += _tbl_out(flavorname.disk, "disktype", True)
        if flavorname.disk.nrdisks != 1:
            stg += f'{flavorname.disk.nrdisks}x'
        stg += f'{flavorname.disk.disksize}GB root volume '
    # GPU
    if flavorname.gpu:
        stg += "and " + _tbl_out(flavorname.gpu, "gputype")
        stg += _tbl_out(flavorname.gpu, "brand")
        stg += _tbl_out(flavorname.gpu, "perf", True)
        stg += _tbl_out(flavorname.gpu, "gen", True)
        if flavorname.gpu.cu is not None:
            stg += f"(w/ {flavorname.gpu.cu} CU/EU/SM) "
    # IB
    if flavorname.ib:
        stg += "and Infiniband "
    return stg[:-1]


class CompatLayer:
    """
    This class provides convenience functions previously found in `flavor-name-check.py`.
    """
    def __init__(self):
        self.verbose = False
        self.debug = False
        self.quiet = False
        self.disallow_old = False
        self.prefer_old = False
        self.v3_flv = False
        self.mandFlavorFile = str(Path(HERE.parent, "SCS-Spec.MandatoryFlavors.yaml"))
        bindir = os.path.basename(sys.argv[0])
        self.searchpath = (bindir, ) if bindir else os.environ['PATH'].split(':')

    def parsename(self, namestr: str) -> Optional[Flavorname]:
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
            # v2 didn't work; try v1, but if that doesn't work either, raise original exception
            try:
                flavorname = parser_v1(namestr)
            except Exception:
                pass
            else:
                is_old = True
            if not is_old:
                raise
        if not self.quiet and flavorname is not None and self.prefer_old != is_old:
            print(f"WARNING: flavor name not v{2 - self.prefer_old}: {namestr}")
        return flavorname

    def outname(self, flavorname):
        return outname(flavorname)

    def old_to_new(self, nm):
        return SyntaxV2.from_v1(nm)

    def new_to_old(self, nm):
        return SyntaxV1.from_v2(nm)

    def findflvfile(self, fnm):
        """Search for flavor file and return found path"""
        if os.path.isfile(fnm):
            return fnm
        raise RuntimeError(f"Flavor yaml file not found: {fnm}")

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
                    name_type[i] = self.new_to_old(name)
        mand = yamldict["SCS-Spec"]["MandatoryFlavors"]
        recd = yamldict["SCS-Spec"]["RecommendedFlavors"]
        if v3mode:
            mand.extend(yamldict["SCS-Spec"].get("MandatoryFlavorsV3", ()))
            recd.extend(yamldict["SCS-Spec"].get("RecommendedFlavorsV3", ()))
            return mand, recd
        else:
            return [*mand, *recd], []


if __name__ == "__main__":
    namestr = "SCS-16T-64-3x10s_bms_hwv_i3h_GNa-64_ib"
    print(outputter(parser_v1("SCS-16T:64:3x10s-GNa:64-ib")) == outputter(parser_v2(namestr).shorten()))
    print(namestr == outputter(parser_v2(namestr)))
