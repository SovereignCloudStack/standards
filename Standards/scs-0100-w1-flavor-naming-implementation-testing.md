---
title: "SCS Flavor Naming Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0100-v1-flavor-naming.md
  - scs-0100-v2-flavor-naming.md
  - scs-0100-v3-flavor-naming.md
---

## Introduction

The three major versions of the standard that exist so far are very similar, and deliberately so.
Therefore, the procedures needed to implement or test them are very similar as well. Yet, this document
will only cover v3, because v1 and v2 are already obsolete by the time of writing.

## Implementation notes

Every flavor whose name starts with `SCS-` must conform with the naming scheme laid down in the standard.

### Operational tooling

#### Syntax check

The [test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/scs_0100_flavor_naming)
comes with a handy
[command-line utility](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/scs_0100_flavor_naming/cli.py)
that can be used to validate flavor names, to interactively construct a flavor name
via a questionnaire, and to generate prose descriptions for given flavor names.
See the [README](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/scs_0100_flavor_naming/README.md)
for more details.

The functionality of this script is also (partially) exposed via the web page
[https://flavors.scs.community/](https://flavors.scs.community/), which can both
parse SCS flavors names as well as generate them.

With the OpenStack tooling (`python3-openstackclient`, `OS_CLOUD`) in place, you can call
`cli.py -v parse v3 $(openstack flavor list -f value -c Name)` to get a report
on the syntax compliance of the flavor names of the cloud environment.

#### Flavor creation

The [OpenStack Flavor Manager from OSISM](https://github.com/osism/openstack-flavor-manager)
will create a whole set of flavors in one go.
To that end, it provides different options: either the standard mandatory and
possibly recommended flavors can be created, or the user can set a file containing his flavors.

### GPU table

The most commonly used datacenter GPUs are listed here, showing what GPUs (or partitions
of a GPU) result in what GPU part of the flavor name. We provide these for convenience; most
values are from data sheets and not based on own testing. Providers must look up the values
(SMs/CUs/EUs and VRAM) really provided to users and correctly fill these into the SCS names.
This is in particular true for the MIG configurations.

#### Nvidia (`N`)

We show the most popular recent generations here. Older one are of course possible as well.

##### Ampere (`a`)

One Streaming Multiprocessor on Ampere has 64 (A30, A100) or 128 Cuda Cores (A10, A40).

GPUs without MIG (one SM has 128 Cuda Cores and 4 Tensor Cores):

| Nvidia GPU | Tensor C | Cuda Cores | SMs | VRAM      | SCS name piece |
|------------|----------|------------|-----|-----------|----------------|
|  A10       |  288     |  9216      |  72 | 24G GDDR6 | `GNa-72-24`    |
|  A40       |  336     | 10752      |  84 | 48G GDDR6 | `GNa-84-48`    |

GPUs with Multi-Instance-GPU (MIG), where GPUs can be partitioned and the partitions handed
out as as pass-through PCIe devices to instances. One SM corresponds to 64 Cuda Cores and
4 Tensor Cores.

| Nvidia GPU | Fraction | Tensor C | Cuda Cores | SMs | VRAM      | SCS GPU name   |
|------------|----------|----------|------------|-----|-----------|----------------|
|  A30       | 1/1      | 224      | 3584       |  56 | 24G HBM2  | `GNa-56-24`    |
|  A30       | 1/2      | 112      | 1792       |  28 | 12G HBM2  | `GNa-28-12`    |
|  A30       | 1/4      |  56      |  896       |  14 |  6G HBM2  | `GNa-14-6`     |
|  A30X      | 1/1      | 224      | 3584       |  56 | 24G HBM2e | `GNa-56h-24h`  |
| A100       | 1/1      | 432      | 6912       | 108 | 80G HBM2e | `GNa-108h-80h` |
| A100       | 1/2      | 216      | 3456       |  54 | 40G HBM2e | `GNa-54h-40h`  |
| A100       | 1/4      | 108      | 1728       |  27 | 20G HBM2e | `GNa-27h-20h`  |
| A100       | 1/7      |  60+     |  960+      |  15+| 10G HBM2e | `GNa-15h-10h`+ |
| A100X      | 1/1      | 432      | 6912       | 108 | 80G HBM2e | `GNa-108-80h`  |

[+] The precise numbers for the 1/7 MIG configurations are not known by the author of
this document and need validation.

##### Ada Lovelave (`l`)

No MIG support, 128 Cuda Cores and 4 Tensor Cores per SM.

| Nvidia GPU | Tensor C | Cuda Cores | SMs | VRAM      | SCS name piece |
|------------|----------|------------|-----|-----------|----------------|
|  L4        | 232      |  7424      |  58 | 24G GDDR6 | `GNl-58-24`    |
| L40        | 568      | 18176      | 142 | 48G GDDR6 | `GNl-142-48`   |
| L40G       | 568      | 18176      | 142 | 48G GDDR6 | `GNl-142h-48`  |
| L40S       | 568      | 18176      | 142 | 48G GDDR6 | `GNl-142hh-48` |

| Nvidia GPU   | Tensor C | Cuda Cores | SMs | VRAM      | SCS name piece |
|--------------|----------|------------|-----|-----------|----------------|
| RTX2000  Ada |   88     |  2816      |  22 | 16G GDDR6 | `GNl-22-16`    |
| RTX4000  Ada |  192     |  6144      |  48 | 20G GDDR6 | `GNl-48-20`    |
| RTX4500  Ada |  240     |  7680      |  60 | 24G GDDR6 | `GNl-60-24`    |
| RTX5000  Ada |  400     | 12800      | 100 | 32G GDDR6 | `GNl-100-32`   |
| RTX5880  Ada |  440     | 14080      | 110 | 48G GDDR6 | `GNl-110-48`   |
| RTX6000  Ada |  568     | 18176      | 142 | 48G GDDR6 | `GNl-142-48`   |

##### Grace Hopper (`g`)

These have MIG support and 128 Cuda Cores and 4 Tensor Cores per SM.

| Nvidia GPU | Fraction | Tensor C | Cuda Cores | SMs | VRAM       | SCS GPU name   |
|------------|----------|----------|------------|-----|------------|----------------|
| H100       | 1/1      | 528      | 16896      | 132 |  80G HBM3  | `GNg-132-80h`  |
| H100       | 1/2      | 264      |  8448      |  66 |  40G HBM3  | `GNg-66-40h`   |
| H100       | 1/4      | 132      |  4224      |  33 |  20G HBM3  | `GNg-33-20h`   |
| H100       | 1/7      |  72+     |  2304+     |  18+|  10G HBM3  | `GNg-18-10h`+  |
| H200       | 1/1      | 528      | 16896      | 132 | 141G HBM3e | `GNg-132-141h` |
| H200       | 1/2      | 264      | 16896      |  66 |  70G HBM3e | `GNg-66-70h`   |
| ... |

[+] The precise numbers for the 1/7 MIG configurations are not known by the author of
this document and need validation.

##### Blackwell (`b`)

These have MIG support and 128 Cuda Cores and 4 Tensor Cores per SM.

| Nvidia GPU | Fraction | Tensor C | Cuda Cores | SMs | VRAM       | SCS GPU name   |
|------------|----------|----------|------------|-----|------------|----------------|
| GB200      | 1/1      |  640     | 20480      | 160 | 192G HBM3e | `GNb-160-192h` |
| GB200      | 1/2      |  320     | 10240      |  80 |  96G HBM3e | `GNb-80-96h`   |
| GB200      | 2/7      |   88+    |  5632+     |  44+|  45G HBM3e+| `GNb-44-45h`+  |
| GB200      | 1/7      |   44+    |  2816+     |  22+|  23G HBM3e+| `GNb-22-23h`+  |
| GB300      | 1/1      |  640     | 20480      | 160 | 288G HBM3e | `GNb-160-288h` |
| GB300      | 1/2      |  320     | 10240      |  80 | 144G HBM3e | `GNb-80-144h`  |
| ... |

[+] The precise numbers for the 1/7 MIG configurations are not known by the author of
this document and need validation.

| Nvidia GPU            | Fraction | Tensor C | Cuda Cores | SMs | VRAM       | SCS GPU name   |
|-----------------------|----------|----------|------------|-----|------------|----------------|
| RTX Pro2000 Blackwell |  1/1     |  136     |  4352      |  34 |  16G GDDR7 | `GNb-34-16`    |
| RTX Pro4000 Blackwell |  1/1     |  280     |  8960      |  70 |  24G GDDR7 | `GNb-70-24`    |
| RTX Pro4500 Blackwell |  1/1     |  328     | 10496      |  82 |  32G GDDR7 | `GNb-82-32`    |
| RTX Pro5000 Blackwell |  1/1     |  440     | 14080      | 110 |  72G GDDR7 | `GNb-110-72`   |
| RTX Pro5000 Blackwell |  1/2     |  220     |  7040      |  55 |  36G GDDR7 | `GNb-55-36`    |
| RTX Pro6000 Blackwell |  1/1     |  752     | 26064      | 188 |  96G GDDR7 | `GNb-188-96`   |
| RTX Pro6000 Blackwell |  1/2     |  376     | 13032      |  94 |  48G GDDR7 | `GNb-94-48`    |
| RTX Pro6000 Blackwell |  1/4     |  188     |  6516      |  47 |  24G GDDR7 | `GNb-47-24`    |


#### AMD Radeon (`A`)

##### CDNA 2 (`2`)

One CU contains 64 Stream Processors.

| AMD Instinct| Stream Proc | CUs | VRAM       | SCS name piece |
|-------------|-------------|-----|------------|----------------|
| Inst MI210  |     6656    | 104 |  64G HBM2e | `GA2-104-64h`  |
| Inst MI250  |    13312    | 208 | 128G HBM2e | `GA2-208-128h` |
| Inst MI250X |    14080    | 229 | 128G HBM2e | `GA2-220-128h` |

##### CDNA 3 (`3`)

SRIOV partitioning is possible, resulting in pass-through for
up to 8 partitions, somewhat similar to Nvidia MIG. 4 Tensor
Cores and 64 Stream Processors per CU.

| AMD GPU     | Tensor C | Stream Proc | CUs | VRAM       | SCS name piece  |
|-------------|----------|-------------|-----|------------|-----------------|
| Inst MI300X | 1216     | 19456       | 304 | 192G HBM3  | `GA3-304-192h`  |
| Inst MI325X | 1216     | 19456       | 304 | 288G HBM3  | `GA3-304-288h`  |

##### CDNA 4 (`4`)

SRIOV partitioning is possible, resulting in pass-through for
up to 8 partitions, somewhat similar to Nvidia MIG. 4 Tensor
Cores and 64 Stream Processors per CU.

| AMD GPU     | Tensor C | Stream Proc | CUs | VRAM       | SCS name piece  |
|-------------|----------|-------------|-----|------------|-----------------|
| Inst MI350X | 1024     | 16384       | 256 | 288G HBM3e | `GA4-256-288h`  |
| Inst MI355X | 1024     | 16384       | 256 | 288G HBM3e | `GA4-256h-288h` |

The Instinct MI355X has a higher watttage and thus slightly higher clocks
than the MI350X but is otherwise identical -- we can thus use the `h` modifier
to identify the higher performance version.

##### Workstation RDNA 3 (`3.1`) and 4 (`4.1`)

2 Tensor Cores and 64 Stream Processors per CU.

| AMD Radeon   | Tensor C | Stream Proc | CUs | VRAM       | SCS name piece  |
|--------------|----------|-------------|-----|------------|-----------------|
|    Pro W7900 |  196     |  6144       |  96 |  48G GDDR6 | `GA3.1-96-48`   |
| AI Pro R9700 |  128     |  4096       |  64 |  32G GDDR6 | `GA4.1-64-32`   |

Note that we previously assumed more similarity of consumer RDNA-x with
server CDNA-x than actually is the case; the RDNA-x cards now use `x.1`
(since v3.3 as of Oct 2025) to be able to differentiate them. We will
tolerate potential rare cases of old installations calling RDNA-x as
generation `x` for the time being. If AMD executes on the merging with
UDNA-5, we will avoid this split in the future.

#### intel Xe (`I`)

##### Xe-HPC (Ponte Vecchio) (`3`)

One EU corresponds to one Tensor Core and contains 128 Shading Units.

| intel DC GPU | Tensor C | Shading U | EUs | VRAM       | SCS name part  |
|--------------|----------|-----------|-----|------------|----------------|
| Max 1100     |  56      |  7168     |  56 |  48G HBM2e | `GI3-56-48h`   |
| Max 1550     | 128      | 16384     | 128 | 128G HBM2e | `GI3-128-128h` |

##### Workstation cards Arc B (`4`)

One EU has one tensor core and 16 shading units.

| intel GPU   | Tensor C | Shading U | EUs | VRAM       | SCS name part  |
|-------------|----------|-----------|-----|------------|----------------|
| Arc Pro B50 |   128    |  2048     | 128 | 16G GDDR6  | `GI4-128-16`   |
| Arc Pro B60 |   160    |  2560     | 160 | 24G GDDR6  | `GI4-160-24`   |
| Arc Pro B65 |   160    |  2560     | 160 | 32G GDDR6  | `GI4-160-32`   |
| Arc Pro B70 |   256    |  4096     | 256 | 32G GDDR6  | `GI4-256-32`   |

#### Consumer cards

Note that we don't recommend using consumer cards. 
That said, the schema allows to specify them and for example do PCI pass-through
of Nvidia RTX4080S (`GNl-80-16`), RTX4090 (`GNl-128-24`), RTX5080S (`GNb-84-24`), 
RTX5090 (`GNb-170-32`), or AMD Radeon RX7900XTX (`GA3.1-96-24`).


## Automated tests

The following testcases [are implemented](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/openstack_test.py):

- `scs-0100-syntax-check` ensures that any name starting with `SCS-` adheres to the standard;
- `scs-0100-semantics-check` ensures that any such name is telling the truth as specified in the standard;
  specifically: any immediately discoverable property of a flavor (currently, CPU, RAM and disk size)
  matches the meaning of its name (which is usually a lower bound), such as the CPU generation or hypervisor.

## Manual tests

To be determined.
