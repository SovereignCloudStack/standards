---
title: SCS Flavor Naming Proposal
version: 2021-06-02-001
authors: Matthias Hamm, Kurt Garloff
state: Draft
---

Flavor Naming (DRAFT) SCS

Please take note, that this is a DRAFT open for discussion (17.05.2021)

# Motivation

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

# Proposal

## Type of information included

We believe the following characteristics are important in a flavour description:

| Type                 | Description                                                  |
|:---------------------|:-------------------------------------------------------------|
| Generation           | CPU Generation                                               |
| Number of CPU        | Number of vCPUs - suffixed by v,t,c (see below)              |
| Amount of RAM        | Amount of memory available for the VM                        |
| Performance Class    | Ability to lable high-performance CPUs, disks, network       |
| CPU Type             | X86-intel, X86-amd, ARM, RISC-V, Generic                     |
| "metal"              | One instance on one Host                                     |

## Complete Proposal

| Prefix | CPU | Suffix      | RAM[GiB] | optional: Disk[GB] | optional: Disktype   | optional: extra features               |
|--------|-----|-------------|----------|--------------------|----------------------|----------------------------------------|
| SCS-   | 1-n | V/T/C [io]  | :x[u][o] | [:1-n]             | [N/S/L/P]            | [-hyp][-[arch[n][h]/-GXn:m/-IB/..]     |

# Proposal Details

## [REQUIRED] CPU Suffixes

| Suffix | Meaning                |
|--------|------------------------|
| V      | vCPU (oversubscribed)  |
| T      | dedicated Thread (SMT) |
| C      | dedicated Core         |

**Baseline**

Note that vCPU oversubscription should be implemented such, that we can guarantee `at least 20% of a
core in >99% of the time`; this can be achieved by limiting vCPU oversubscription to 5x per core
(or 3x per thread when SMT/HT is enabled) or by more advanced workload management logic.

Note that CPUs must use latest microcode to protect against CPU vulnerabilities (Spectre, Meltdown, L1TF, etc.).
The provider must enable at least all mitigations that are enabled by default in the Linux kernel. CPUs that
are susceptible to L1TF (intel x86 pre Cascade Lake) must switch off hyperthreading OR (in the future)
use core scheduling implementations that are deemed to be secure by the SCS security team.

**Higher oversubscription**

Must be indicated with an additional `o suffix` for oversubscribed (low performance > 5x/core or > 3x/thread).

**Insufficient microcode**

Not using these mitigations must be indicated by an additional `i suffix` for insecure (weak protection against CPU vulns). 

**Examples**

- SCS-**2C**:4:10N
- SCS-**2T**:4:10N
- SCS-**2V**:4:10N
- SCS-**2Co**:4:10N
- SCS-**2Ci**:4:10N
- SCS-**2Coi**:4:10N
- ~~SCS-**2Cio**:4:10N~~ <- This order is forbidden

## [REQUIRED] Memory 

**Baseline**

We expect cloud providers to use ECC memory.
Memory oversubscription is not recommended.
It is allowed to specify half GiBs (e.g. 3.5), though this is discouraged for larger memory sizes (>= 10GiB).

**No ECC**

If no ECC is used, the `u suffix` must indicate this.

**Enabled Oversubscription**

You have to expose this with the `o sufffix`.

**Examples**

- SCS-2C:**4**:10N
- SCS-2C:**3.5**:10N
- SCS-2C:**4u**:10N
- SCS-2C:**4o**:10N
- SCS-2C:**4uo**:10N
- ~~SCS-2C:**4ou**:10N~~ <- This order is forbidden

## [OPTIONAL] Disk types

| Disktype |  Meaning                             |
|----------|--------------------------------------|
|   N      | Network shared storage (ceph/cinder) |
|   H      | Local disk (SATA/SAS class)          |
|   S      | Local SSD disk                       |
|   P      | Local high-perf NVMe                 |

**Baseline**

Note that Disktype might be omitted -- the user then can not take any assumptions
on what storage is provided for the root disk (that the image gets provisioned to).

It does make sense for `N` to be requested explicitly to allow for smooth live migration.
`H` typically provides latency advantages vs `N` (but not necessarily bandwidth and
also is more likely to fail), `S` and `P` are for applications that need high IOPS
and bandwidth disk I/O. `N` storage is expected to survive single-disk and
single-node failure.

If the disk size is left out, the cloud is expected to allocate a disk (network or local)
that is large enough to fit the root file system (`min_disk` in image). This automatic
allocation is indicated with `:` without a disk size.
If the `:` is left out completely, the user must create a boot volume manually and
tell the instance to boot from it or use the block_device_mapping_v2 mechanism explicitly
to create the boot volume from an image.

**Multi-provisioned Disk**

The disk size can be prefixed with `Mx prefix`, where M is an integer specifying that the disk
is provisioned M times.

**FIXME**

With block_device_mapping_v2, can we remove the disks from most flavors?

**Examples**

- SCS-2C:4:**10N**
- SCS-2C:4:**10S**
- SCS-2C:4:**10S**-bms-z3
- SCS-2C:4:**3x10S** <- Cloud creates three 10GB disks
- SCS-2C:4:**3x10S**-bms-z3
- SCS-2C:4:**10** <- Cloud decides disk type
- SCS-2C:4:**10**-bms-z3
- SCS-2C:4:**N** <- Cloud decides disk size
- SCS-2C:4:**N**-bms-3
- SCS-2C:4: <- Cloud decides disk type and size
- SCS-2C:4:-bms-z3
- SCS-2C:4 <- You need to specify a boot volume yourself
- SCS-2C:4-bms-z3
- SCS-2C:4:3x <- Cloud decides disk type and size and creates three of them
- SCS-2C:4:3xS <- Cloud decides size and creates three local SSD volumes
- SCS-2C:4:3x10 <- Cloud decides type and creates three 10GB volumes
- ~~SCS-2C:4:**1.5N**~~ <- You may not specify disk sizes which are not in full GiBs

## [OPTINAL] Hypervisor

The `default Hypervisor` is assumed to be `KVM`. Clouds, that offer different hypervisors
or Bare Metal Systems should indicate the Hypervisor like the following:

| hyp    |   Meaning         |
|--------|-------------------|
| kvm    | KVM               |
| xen    | Xen               |
| vmw    | VMware            |
| hyv    | Hyper-V           |
| bms    | Bare Metal System |

**Examples**

- SCS-2C:4:10N
- SCS-2C:4:10N-**bms**
- SCS-2C:4:10N-**bms**-z3h

## [OPTINAL] CPU Architecture Details

Arch details provide more details on the specific CPU:
 - Vendor
 - Generation
 - Frequency

**Generation and Vendor**

The generations are vendor specific and can be left out.
Not specifying arch means that we have a generic CPU (**x86-64**).

| Generation | i (Intel x86-64) | z (AMD x86-64) | a (AArch64)        | r (RISC-V) |
|------------|------------------|----------------|--------------------|------------|
|  0         | pre Skylake      | pre Zen        | pre Cortex A76     | TBD        |
|  1         | Skylake          | Zen-1 (Naples) | A76/NeoN1 class    | TBD        |
|  2         | Cascade Lake     | Zen-2 (Rome)   | A78/x1/NeoV1 class | TBD        |
|  3         | Ice Lake         | Zen-3 (Milan)  | Anext/NeoN2 class  | TBD        |

**Frequency Suffixes**

| Suffix | Meaning           |
|--------|-------------------|
| h      | >2.75GHz all-core |
| hh     | >3.25GHz all-core |
| hhh    | >3.75GHz all-core |

**Examples**

- SCS-2C:4:10N
- SCS-2C:4:10N-**z**
- SCS-2C:4:10N-**z3**
- SCS-2C:4:10N-**z3h**
- SCS-2C:4:10N-**z3hh**
- SCS-2C:4:10N-bms-**z**
- SCS-2C:4:10N-bms-**z3**
- SCS-2C:4:10N-bms-**z3**
- SCS-2C:4:10N-bms-**z3h**
- SCS-2C:4:10N-bms-**z3hh**

## [OPTINAL] Extra features

Note that these are optional -- it is recommended for providers to encode this information
into the flavor name, so there is a systematic way of differentiating flavors.
Providers could leave it out however, leaving it to `extra_specs` to make these flavor
capabilities discoverable. Nothing prevents providers from registering the same flavor
under a secondary (or tertiary) name.

`-GXn[:m][h]` indicates a Pass-Through GPU from vendor X of gen n with m compute units / SMs / EUs exposed.
`-gXn[:m][h]` indicates a vGPU from vendor X of gen n with m compute units / SMs / EUs assigned.

| GPU | Vendor     |
|-----|------------|
| n   | nVidia     |
| a   | AMD        |
| i   | Intel      |

Generations could be nVidia (f=Fermi, k=Kepler, m=Maxwell, p=Pascal, v=Volta, t=turing, a=Ampere, ...),
AMD (GCN-x=0.x, RDNA1=1, RDNA2=2), intel (Gen9=0.9, Xe(12.1)=1, ...), ...
(This needs further work.)
`h` indicated high-performance (e.g. high freq or special high bandwidth gfx memory such as HBM);
`h` can be duplicated for even higher performance.

`-IB` indicates Inifinband networking.

More extensions will be forthcoming.

Extensions need to be specified in the above mentioned order.

# Proposal Examples

|         Example           |                 Decoding                                                                        |
|---------------------------|-------------------------------------------------------------------------------------------------|
| SCS-2C:4:10N              | 2 dedicated cores (x86-64), 4GiB RAM, 10GB network disk                                         |
| SCS-8Ti:32:50P-i1         | 8 dedicated hyperthreads (insecure), Skylake, 32GiB RAM, 50GB local NVMe                        |
| SCS-1Vo:1u:5              | 1 vCPU (heavily oversubscribed), 1GiB Ram (no ECC), 5GB disk (unspecific)                       |
| SCS-16T:64:200S-IB-Gna:84 | 16 dedicated threads, 64GiB RAM, 200GB local SSD, Inifiniband, 64 Passthrough nVidia Ampere SMs |
| SCS-4C:16:2x200P-a1       | 4 dedicated Arm64 cores (A78 class), 16GiB RAM, 2x200GB local NVMe drives                       |
| SCS-1V:0.5                | 1 vCPU, 0.5GiB RAM, no disk (boot from cinder volume)                                           |

# Standard SCS flavors

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

# Naming policies

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

## Rationale

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

# Validation

There is a script in `tools/flavor_name_check.py` which can be used to decode, validate
and construct flavor names.
This script must stay in sync with the specification text.

# Beyond SCS: Gaia-X

Some providers might offer VM services ("IaaS") without trying to adhere to SCS standards,
yet still finding the flavor naming standards useful. The Gaia-X Technical Committee's
Provider Working Group (WG) would seem like a logical place for such dicussions then.
If so, we could
replace the SCS- prefix with a GX- prefix and transfer the naming scheme governance from
the SCS project to the Gaia-X Provier WG. SCS certification would then reference the
Gaia-X flavor naming standard as a requirement.
