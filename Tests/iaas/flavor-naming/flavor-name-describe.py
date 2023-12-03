#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""Flavor naming describer
https://github.com/SovereignCloudStack/Standards/

Output a human readable flavor description from the SCS names

(c) Kurt Garloff <garloff@osb-alliance.com>, 6/2023
License: CC-BY-SA 4.0
"""


import sys


def collectattrs(alist, new):
    "collect list of attitbutes"
    if alist:
        alist += f", {new}"
    else:
        alist = new
    return alist


def tbl_out(item, kind, check = False):
    "Look up table value (attach space), skip if entry is 0 or empty string and check is set"
    val = item.__getattribute__(kind)
    if check and not val:
        return ""
    try:
        return item.__getattribute__("tbl_"+kind)[val] + " "
    except KeyError:
        return str(val) + " "


def prettyname(item_list, prefix=""):
    "Output a human-readable flavor description"
    cpu, disk, hype, hvirt, cpubrand, gpu, ibd = item_list
    # CPU (number, type, attributes)
    stg = f"{prefix}SCS flavor with {cpu.cpus} "
    if cpubrand.parsed:
        stg += tbl_out(cpubrand, "perf", True)
        stg += tbl_out(cpubrand, "cpuvendor")
        stg += tbl_out(cpubrand, "cpugen", True)
    else:
        stg += "generic x86-64 "
    stg += tbl_out(cpu, "cputype")
    if cpu.cpuinsecure:
        stg += "(insecure) "
    # RAM (amount, attributes)
    stg += f"with {cpu.ram} GiB RAM "
    alist = ""
    if cpu.raminsecure:
        alist = collectattrs(alist, "noECC")
    if cpu.ramoversubscribed:
        alist = collectattrs(alist, "oversubscribed")
    if alist:
        stg += f"({alist}) "
    # Hypervisor, HVirt
    if hype.parsed:
        stg += f'on {tbl_out(hype, "hype")}'
    if hvirt.parsed:
        stg += 'with HW virt '
    # Disk
    if disk.parsed:
        stg += "and "
        stg += tbl_out(disk, "disktype", True)
        if disk.nrdisks != 1:
            stg += f'{disk.nrdisks}x'
        stg += f'{disk.disksize}GB root volume '
    # GPU
    if gpu.parsed:
        stg += "and " + tbl_out(gpu, "gputype")
        stg += tbl_out(gpu, "brand")
        stg += tbl_out(gpu, "perf", True)
        stg += gpu.__getattribute__(f"tbl_brand_{gpu.brand}_gen")[gpu.gen] + " "
        if gpu.cu:
            stg += f"(w/ {gpu.cu} CU/EU/SM) "
    # IB
    if ibd.parsed:
        stg += "and Infiniband "
    return stg[:-1]


def main(argv):
    "Entry point for testing"
    import importlib
    fnmck = importlib.import_module("flavor-name-check")
    for nm in argv:
        ret = fnmck.parsename(nm)
        if ret:
            print(f'{nm}: {prettyname(ret)}')
        else:
            print(f'{nm}: Not an SCS flavor')

if __name__ == "__main__":
    main(sys.argv[1:])
