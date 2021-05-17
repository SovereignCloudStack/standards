---
title: SCS Flavor Naming Proposal
version: 2021-05-17-002
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

| Prefix | CPU |    Suffix   | RAM[GiB] | Disk[GB] |   Disktype | optional: extra features   |
|--------|-----|-------------|----------|----------|------------|----------------------------|
| SCS-   | 1-n | V/T/C [il]  |   :x[u]  | :1-n     | [C/S/L/N]  | [-ARCHn/-h/-IB/-GXn:m/..]  |

#### CPU Suffixes

|Suffix |     Meaning            |
|-------|------------------------|
| V     | vCPU (oversubscribed)  |
| T     | dedicated Thread (SMT) |
| C     | dedicated Core         |

Note that vCPU oversubscription should be no more than 5x per core (3x per thread in SMT scenarios).

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

If both optional suffices are used, `l` needs to preceed `i`.

#### Memory 

No memory oversubscription is done.

If no ECC memory is used, the suffix `u` must indicate this.

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
and bandwidth disk I/O.

#### CPU Architecture Details (optional)

Arch details provide more details on the specific CPU: Vendor and generation (n).

| ARCHn  | Meaning                  |
|--------|--------------------------|
| in     | Intel x86-64 CPU, gen n  |
| zn     | AMD x86-64 CPU, gen n    |
| an     | AArch64 CPU, gen n       |
| rn     | RISC-V CPU, gen n        |

The generation can be left out.
Not specifying ARCH means that we have a generic CPU (x86-64).

The generations are type specific

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

| AArch64 g | Meaning               |
|-----------|-----------------------|
|    0      | pre-Cortex A78        |
|    1      | Cortex A78 class      |

`-h` indicates a high-frequency class (e.g. >3GHz all-core); `-hh`, `-hhh` 
can be used to indicate further increases.

Note that not specifying the -ARCHn suffix is perfectly fine, providing a generic
(x86-64) CPU type.

#### Extra features (optional)

Note that these are optional -- it is recommended for providers to encode this information
into the flavor name, so there is a systematic way of differentiating flavors.
Providers could leave it out however, leaving it to `extra_specs` to make these flavor
capabilities discoverable. Nothing prevents providers from registering the same flavor
under a secondary (or tertiary) name.

`-IB` indicates Inifinband networking.

`-GXn:m` indicates a Pass-Through GPU from vendor X of gen n with m units assigned.
`-gXn:m` indicates a vGPU from vendor X of gen n with m units assigned.

| GPU vendor X | meaning    |
|--------------|------------|
|      N       | nVidia     |
|      A       | AMD        |
|      I       | Intel      |

Generations could be nVidia (T=Tesla, P=Pascal, A=Ampere, ...), AMD (GCN-x=0.x, RDNA1=1, RDNA2=2), ...

(This needs further work.)

We'd also need to differentiate the size of the GPU (cores?), vPU vs. Pass-Through.

### Examples

|         Example    |                 Decoding                                    |
|--------------------|-------------------------------------------------------------|
| SCS-2C:4:10C       | 2 dedicated cores (x86-64), 4GiB RAM, 10GB network disk     |
| SCS-8Ti:32:50N-i1  | 8 dedicated hyperthreads (insecure), Skylake, 32GiB RAM, 50GB local NVMe    |
| SCS-1Vl:1u:10      | 1 vCPU (heavily oversubscribed), 1GiB Ram (no ECC), 10GB disk (unspecific)  |
| SCS-16T:64:200S-IB-GNA:2304 | 16 dedicated threads, 64GiB RAM, 200GB local NVMe, Inifiniband, 2304 Passthrough nVidia Ampere Cores |


### Standard SCS flavors

These are flavors expected to exist on standard SCS clouds.

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

