---
title: Flavor Naming SCS Proposal
version: 2021-05-09-001
author: Matthias Hamm
state: Draft
---

Flavor Naming (DRAFT) SCS

Please take note, that this is a DRAFT open for discussion (09.05.2021)


## Motivation

 In OpenStack environments there is a need to define different flavors for instances. A running instance cannot be customized by a user, so a number of pre defined flavors are necessary.
 To give a provider or operator of a SCS the possibility to define flavors by himself, the pre defined SCS flavors should be recognisable by all customers.
 Also some key features of a flavor should be recognisable at first glance by the user.
 In the future some points are important: there will be GPU support, fast disks for databases, memory-heavy applications, and other useful aspects of an instance.
It may also be important to make the CPU generation clearly recognisable, as this is always a topic in discussions with customers.

## First Proposal


### Type of information included

We believe the following characteristics are important in a flavour description:


| Type                 | Description                                                 |
|:---------------------|:-------------------------------------------------------------|
|Generation            | CPU Generation                                              |
|Number of CPU         | Number of CPUs as the basis of a performance class. Normal split is 1:4 (CPU:RAM)|
| Highmem              | Different CPU to RAM ratio for high RAM demand               |
| Performance Class    | Labelling for Normal, HighCPU, GPU, NVMe, LokalDisk etc. If necessary, also mix |
| CPU Type             | X86, ARM, RiSC, Generic  |
| "metal"              | One VM on one Host |


### Complete Proposal

| Prefix | Type (Performance) | CPU | RAM | CPUType | Generation |
|--------|--------------------|-----|-----|---------|------------|
| SCS    | N - Normal (4xCPU) | 1-16| :x  | X -x86| v1 - Intel until Cascade Lake(2019)  |
|         | H - HighCPU(>x GHZ)| 1-32 | :x | A -ARM    |v1 -  Scalable Intel® Xeon® processors of the 2nd generation |
|    | M - Memory (8xCPU) | 1-16 | :x | G - Generic    |v1 -  AMD CPU until Epyc Rome (2019)  Zen2  |
|        | G - GPU        | 1-16 | :x | R - RISC           |                                            |
|        | L - LocalDisk  | 1-16 | :x |             |                                            |

### Examples:

SCS-N4:16-X-v1  (4CPU, 16GB RAM, X86, v1)

SCS-M8:64-X-v1 (8CPU, 64GB RAM, X86, v1)

SCS-G4:16-G-v1 (4CPU, 16GB RAM, Generic, v1, GPU)

SCS-MG4:32-A-v1 (4CPU, 32GB RAM, ARM, v1, GPU)

SCS-LH8:32-G-v1 (8CPU, 32GM RAM, Generic, v1, HighCPU>2,8GHZ, LokalDisk)
