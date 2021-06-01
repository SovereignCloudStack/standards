---
title: SCS Flavor Naming Proposal
version: 2021-05-31-003
authors: Matthias Hamm, Kurt Garloff
state: Draft
---

Flavor Naming (DRAFT) SCS

Please take note, that this is a DRAFT open for discussion (17.05.2021)


## Motivation

 In OpenStack environments there is a need to define different flavors for instances.
 The flavors are pre-defined by the operator, the customer can not change these.
 OpenStack providers thus typically offer a large selection of flavors.
 
 While flavors can be discovered (`openstack flavor list`), it is helpful for users (DevOps teams),
 to have
 
 * A naming scheme that is used across all SCS flavors, so flavor names have the same meaning everywhere.
 * Have a guaranteed set of flavors available on all SCS clouds, so these do not need to be discovered.

 While not all details will be encoded in the name, the key features should be obvious:
 Number of vCPUs, RAM, Root Disk.
 Extra features are important as well: There will be flavors with GPU support, fast disks for databases,
 memory-heavy applications, and other useful aspects of an instance.

 It may also be important to make the CPU generation clearly recognisable, as this is always a topic in
 discussions with customers.

## Proposal


### Type of information included

We believe the following characteristics are important in a flavour description:


| Type                 | Description                                                  |
|:---------------------|:-------------------------------------------------------------|
|Generation            | CPU Generation                                               |
|Number of CPU         | Number of vCPUs - suffixed by v,t,c (see below)              |
|Amount of RAM         | Amount of memory available for the VM                        |
| Performance Class    | Ability to lable high-performance CPUs, disks, network       |
| CPU Type             | X86-intel, X86-amd, ARM, RISC-V, Generic  |
| "metal"              | One instance on one Host |


### Complete Proposal

| Prefix | CPU |    Suffix   | RAM[GiB] | Disk[GB] |   Disktype | optional: extra features               |
|--------|-----|-------------|----------|----------|------------|----------------------------------------|
| SCS-   | 1-n | V/T/C [il]  | :x[u][o] | :1-n     | [C/S/L/N]  | [-hyp][-[arch[n][h]/-GXn:m/-IB/..]     |

#### CPU Suffixes

|Suffix |     Meaning            |
|-------|------------------------|
| V     | vCPU (oversubscribed)  |
| T     | dedicated Thread (SMT) |
| C     | dedicated Core         |

Note that vCPU oversubscription should be implemented such, that we can guarantee at least 20% of a
core in >99% of the time; this can be achieved by limiting vCPU oversubscription to 5x per core
(or 3x per thread when SMT/HT is enabled) or by more advanced workload management logic.

Higher oversubscription must be indicated with an additional `l` suffix.

Note that CPUs must use latest microcode to protect against CPU vulnerabilities (Spectre, Meltdown, L1TF, etc.).
The provider must enable at least all mitigations that are enabled by default in the Linux kernel. CPUs that
are susceptible to L1TF (intel x86 pre Cascade Lake) must switch off hyperthreading OR (in the future)
use core scheduling implementations that are deemed to be secure by the SCS security team.
Not using these mitigations must be indicated by an additional `i` suffix. 

| Suffix | Meaning                                               |
|--------|-------------------------------------------------------|
|   l    | low performance (oversubscr > 5x/core or > 3x/thread) |
|   i    | insecure (weak protection against CPU vulns)          |

If both optional suffices are used, `l` needs to precede `i`.

#### Memory 

We expect cloud providers to use ECC memory.
If no ECC is used, the suffix `u` must indicate this.

No memory oversubscription is recommended. If you really want to do it, you
must expose this with the `o` sufffix.

It is allowed to specify half GiBs (e.g. 3.5), though this is discouraged
for larger memory sizes (>= 10GiB).

#### Disk types

| Disktype |  Meaning                             |
|----------|--------------------------------------|
|   C      | Network shared storage (ceph/cinder) |
|   L      | Local disk (SATA/SAS class)          |
|   S      | Local SSD disk                       |
|   N      | Local high-perf NVMe                 |

Note that Disktype might be omitted -- the user then can not take any assumptions
on what storage is provided for the root disk (that the image gets provisioned to).

It does make sense for `C` to be requested explicitly to allow for smooth live migration.
`L` typically provides latency advantages vs `C` (but not necessarily bandwidth and
also is more likely to fail), `S` and `N` are for applications that need high IOPS
and bandwidth disk I/O. `C` storage is expected to survive single-disk and
single-node failure.

The disk size can be prefixed with Mx, where M is an integer specifying that the disk
is provisioned M times.

If the disk size is left out, the cloud is expected to allocate a disk (network or local)
that is large enough to fit the root file system (`min_disk` in image). This automatic
allocation is indicated with `:` without a disk size.
If the `:` is left out completely, the user must create a boot volume manually and
tell the instance to boot from it or use the block_device_mapping_v2 mechanism explicitly
to create the boot volume from an image.

FIXME: With block_device_mapping_v2, can we remove the disks from most flavors?

#### Hypervisor (optional)

Clouds that offer hypervisors (or Bare Metal Systems) other than KVM should indicate
the Hypervisor here.

| hyp    |   Meaning                |
|--------|--------------------------|
| kvm    | KVM [can be left out]    |
| xen    | Xen                      |
| vmw    | VMware                   |
| hyv    | Hyper-V                  |
| bms    | Bare Metal System        |

#### CPU Architecture Details (optional)

Arch details provide more details on the specific CPU: Vendor and generation (n).

| arch[n] | Meaning                  |
|---------|--------------------------|
| i[n][h] | Intel x86-64 CPU, gen n  |
| z[n][h] | AMD x86-64 CPU, gen n    |
| a[n][h] | AArch64 CPU, gen n       |
| r[n][h] | RISC-V CPU, gen n        |

The generation can be left out.
Not specifying arch means that we have a generic CPU (x86-64).

The generations are vendor specific

| Intel gen | Meaning               |
|-----------|-----------------------|
|    0      | Pre Skylake           |
|    1      | Skylake               |
|    2      | Cascade Lake          |
|    3      | Ice Lake              |

|  AMD  gen | Meaning               |
|-----------|-----------------------|
|    0      | pre-Zen               |
|    1      | Zen-1 (Naples)        |
|    2      | Zen-2 (Rome)          |
|    3      | Zen-3 (Milan)         |

| AArch64 gen | Meaning               |
|-------------|-----------------------|
|    0        | pre-Cortex A76        |
|    1        | A76/NeoN1 class       |
|    2        | A78/x1/NeoV1 class    |
|    3        | Anext/NeoN2 class     |

`h` indicates a high-frequency class (e.g. >2.75GHz all-core); `hh`(>3.25G), `hhh` (>3.75G)
can be used to indicate further increases. `-z3h` thus means a Zen3
CPU (Milan), such as EPYC 75F3.

Note that not specifying the -ARCH[n] suffix is perfectly fine, providing a generic
(x86-64) CPU type.

If it is specified, it needs to be first after disk.

#### Extra features (optional)

Note that these are optional -- it is recommended for providers to encode this information
into the flavor name, so there is a systematic way of differentiating flavors.
Providers could leave it out however, leaving it to `extra_specs` to make these flavor
capabilities discoverable. Nothing prevents providers from registering the same flavor
under a secondary (or tertiary) name.

`-GXn[:m][h]` indicates a Pass-Through GPU from vendor X of gen n with m compute units / SMs / EUs exposed.
`-gXn[:m][h]` indicates a vGPU from vendor X of gen n with m compute units / SMs / EUs assigned.

| GPU vendor X | meaning    |
|--------------|------------|
|      n       | nVidia     |
|      a       | AMD        |
|      i       | Intel      |

Generations could be nVidia (f=Fermi, k=Kepler, m=Maxwell, p=Pascal, v=Volta, t=turing, a=Ampere, ...),
AMD (GCN-x=0.x, RDNA1=1, RDNA2=2), intel (Gen9=0.9, Xe(12.1)=1, ...), ...
(This needs further work.)
`h` indicated high-performance (e.g. high freq or special high bandwidth gfx memory such as HBM);
`h` can be duplicated for even higher performance.

`-IB` indicates Inifinband networking.

More extensions will be forthcoming.

Extensions need to be specified in the above mentioned order.

### Examples

|         Example     |                 Decoding                                    |
|---------------------|-------------------------------------------------------------|
| SCS-2C:4:10C        | 2 dedicated cores (x86-64), 4GiB RAM, 10GB network disk     |
| SCS-8Ti:32:50N-i1   | 8 dedicated hyperthreads (insecure), Skylake, 32GiB RAM, 50GB local NVMe   |
| SCS-1Vl:1u:5        | 1 vCPU (heavily oversubscribed), 1GiB Ram (no ECC), 5GB disk (unspecific)  |
| SCS-16T:64:200S-IB-Gna:84 | 16 dedicated threads, 64GiB RAM, 200GB local SSD, Inifiniband, 64 Passthrough nVidia Ampere SMs |
| SCS-4C:16:2x200N-a1 | 4 dedicated Arm64 cores (A78 class), 16GiB RAM, 2x200GB local NVMe drives |
| SCS-1V:0.5          | 1 vCPU, 0.5GiB RAM, no disk (boot from cinder volume)       |

### Standard SCS flavors

These are flavors expected to exist on standard SCS clouds (x86-64).

We expect disk sizes to be 5, 10, 20, 50, 100, 200, 500, 1000GB, 2000GB.
We expect an average CPU:Mem[GiB] ratio of 1:4.

| vCPU:RAM ratio | Mandatory Flavors                             |
|----------------|-----------------------------------------------|
|  1:4           |  SCS-1V:4:10,   SCS-1V:4:20,   SCS-1V:4:20    |
|  2:8           |  SCS-2V:8:20,   SCS-2V:8:50,   SCS-2V:8:100   |
|  4:16          |  SCS-4V:16:50,  SCS-4V:16:100, SCS-4V:16:200  |
|  8:32          |  SCS-8V:32:100, SCS-8V:32:200                 |
|  1:2           |  SCS-1V:2:5,    SCS-1V:2:10,   SCS-1V:2:20    |
|  2:4           |  SCS-2V:4:10,   SCS-2V:4:20,   SCS-2V:4:50    |
|  4:8           |  SCS-4V:8:20,   SCS-4V:8:50,   SCS-4V:8:100   |
|  8:16          |  SCS-8V:16:50,  SCS-8V:16:100, SCS-8V:16:200  |
| 16:32          |  SCS-16V:32:100, SCS-16V:32:200               |
|  1:8           |  SCS-1V:8:20,   SCS-1V:8:50,   SCS-1V:8:100   |
|  2:16          |  SCS-2V:16:50,  SCS-2V:16:100, SCS-2V:16:200  |
|  4:32          |  SCS-4V:32:100, SCS-4V:32:200                 |
|  1:1           |  SCS-1Vl:1:5  , SCS-1V:1:10                   |

Note that all vCPUs are oversubscribed -- the smallest flavor allows
for heavy oversubscription (note the `l`, and thus can be offered very 
cheap -- imagine jump hosts ...). There are two tiny 1:1 flavors.
Disks types are not specified (and expected to be C or L typically).

The design allows for small clouds (with CPUs with 16 Threads, 64GiB RAM
compute hosts) to offer all flavors.

FIXME: With block_device_mapping_v2, can we remove the disks from most flavors?

## Naming policies

To be certified as an SCS compliant x86-64 IaaS platform, you must offer all standard SCS flavors
according to the previous section. (We may define a mechanism that allows exceptions to be
granted in a way that makes this very transparent and visible to clients.)

You are allowed to understate your performance; you may implement a SCS-1Vl:1:5 flavor with
a flavor that actually implements SCS-1T:1:5C (i.e. you dedicate a secured hyperthread instead
of high oversubscription) or even SCS-1D:1.5:8S (1 dedicated core, 50% more RAM and a 8GiB SSD).

We expect all cloud providers to offer the short, less specific flavor names (such as SCS-8V:32:100).
Larger providers that offer more details are expected to still also offer the short variants
for usability and easier portability, even beyond the mandated flavors.

You must be very careful to expose low vCPU guarantees `l`, insecure hyperthreading `i`,
non-ECC-RAM `u`, memory oversubscription `o`. Note that omitting these qualifiers is
overstating your security, reliability or performance iproperties and may be reason for
clients to feel betrayed or claim damages. It may also cause SCS to withdraw certification
along with public statements.

You may offer additional SCS- flavors, following the naming scheme outlined here.

You may offer additional flavors, not following above scheme.

You must not offer flavors with the SCS- prefix which do not follow this naming scheme.
You must not extend the SCS naming scheme with your own suffices; you are encouraged however
to suggest extensions that we can discuss and add to the official scheme.

### Rationale

Note that we expect most clouds to prefer short flavor names,
not indicating CPU details or hypervisor types. See above list
of standard flavors to get a feeling.

However, more successful providers will often need to differentiate their
offerings in response to customer demand and allow customers to request
flavors with specific detailed properties. The goal of this proposal is to avoid
providers to invent their own names and then refer customers to `extra_specs`
or worse a non-machine-readable service description to find out the details.

So a cloud provider might well evolve from offering `SCS-8C:16:50` to offering
`SCS-8T:16:50C`, `SCS-8T:16:50C-i2` and `SCS-8T:16:50C-a2` to specify that he
is using network disks and offer a choice b/w intel Cascade-Lake and AMD Rome.
We would expect the cloud provider to still offer the generic flavor
`SCS-8C:16:50` and allow the scheduler (placement service) to pick both more
specific types (or just one if e.g. capacity management considerations suggest
so).

## Validation

There is a script in `tools/flavor_name_check.py` which can be used to decode, validate
and construct flavor names.
This script must stay in sync with the specification text.

## Beyond SCS: Gaia-X

Some providers might offer VM services ("IaaS") without trying to adhere to SCS standards,
yet still finding the flavor naming standards useful. The Gaia-X Technical Committee's
Provider Working Group (WG) would seem like a logical place for such dicussions then.
If so, we could
replace the SCS- prefix with a GX- prefix and transfer the naming scheme governance from
the SCS project to the Gaia-X Provier WG. SCS certification would then reference the
Gaia-X flavor naming standard as a requirement.
