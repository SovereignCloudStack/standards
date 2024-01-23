#!/usr/bin/env python3


def collectattrs(alist, new):
    "collect list of attitbutes"
    if alist:
        alist += f", {new}"
    else:
        alist = new
    return alist


def tbl_out(item, kind, check=False):
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
        stg += tbl_out(flavorname.cpubrand, "perf", True)
        stg += tbl_out(flavorname.cpubrand, "cpuvendor")
        stg += tbl_out(flavorname.cpubrand, "cpugen", True)
    else:
        stg += "generic x86-64 "
    stg += tbl_out(flavorname.cpuram, "cputype")
    if flavorname.cpuram.cpuinsecure:
        stg += "(insecure) "
    # RAM (amount, attributes)
    stg += f"with {flavorname.cpuram.ram} GiB RAM "
    alist = ""
    if flavorname.cpuram.raminsecure:
        alist = collectattrs(alist, "noECC")
    if flavorname.cpuram.ramoversubscribed:
        alist = collectattrs(alist, "oversubscribed")
    if alist:
        stg += f"({alist}) "
    # Hypervisor, HVirt
    if flavorname.hype:
        stg += f'on {tbl_out(flavorname.hype, "hype")}'
    if flavorname.hwvirt:
        stg += 'with HW virt '
    # Disk
    if flavorname.disk:
        stg += "and "
        stg += tbl_out(flavorname.disk, "disktype", True)
        if flavorname.disk.nrdisks != 1:
            stg += f'{flavorname.disk.nrdisks}x'
        stg += f'{flavorname.disk.disksize}GB root volume '
    # GPU
    if flavorname.gpu:
        stg += "and " + tbl_out(flavorname.gpu, "gputype")
        stg += tbl_out(flavorname.gpu, "brand")
        stg += tbl_out(flavorname.gpu, "perf", True)
        stg += tbl_out(flavorname.gpu, "gen", True)
        if flavorname.gpu.cu is not None:
            stg += f"(w/ {flavorname.gpu.cu} CU/EU/SM) "
    # IB
    if flavorname.ib:
        stg += "and Infiniband "
    return stg[:-1]
