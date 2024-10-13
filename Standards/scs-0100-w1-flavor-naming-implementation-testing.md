---
title: "SCS Flavor Naming Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
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

The [test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming)
comes with a handy
[command-line utility](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/cli.py)
that can be used to validate flavor names, to interactively construct a flavor name
via a questionnaire, and to generate prose descriptions for given flavor names.
See the [README](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/README.md)
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
of a GPU) result in what GPU part of the flavor name.

#### nVidia (`N`)

##### Ampere (`a`)

One Streaming Multiprocessor on Ampere has 64 (A30, A100) or 128 Cuda Cores (A10, A40).

GPUs without MIG (one SM has 128 Cude Cores and 4 Tensor Cores):

| nVidia GPU | Tensor C | Cuda Cores | SMs |    VRAM    | SCS name piece |
|------------|----------|------------|-----|------------|----------------|
|  A10       |    288   |   9216     |  72 |  24G GDDR6 | `GNa-72-24`    |
|  A40       |    336   |  10752     |  84 |  48G GDDR6 | `GNa-84-48`    |

GPUs with Multi-Instance-GPU (MIG), where GPUs can be partitioned and the partitions handed
out as as pass-through PCIe devices to instances. One SM corresponds to 64 Cuda Cores and
4 Tensor Cores.

| nVidia GPU | Fraction | Tensor C |Cuda Cores | SMs |    VRAM    | SCS GPU name   |
|------------|----------|----------|-----------|-----|------------|----------------|
|  A30       |  1/1     |    224   |   3584    |  56 |  24G HBM2  | `GNa-56-24`    |
|  A30       |  1/2     |    112   |   1792    |  28 |  12G HBM2  | `GNa-28-12`    |
|  A30       |  1/4     |     56   |    896    |  14 |   6G HBM2  | `GNa-14-6`     |
|  A30X      |  1/1     |    224   |   3584    |  56 |  24G HBM2e | `GNa-56h-24h`  |
| A100       |  1/1     |    432   |   6912    | 108 |  80G HBM2e | `GNa-108h-80h` |
| A100       |  1/2     |    216   |   3456    |  54 |  40G HBM2e | `GNa-54h-40h`  |
| A100       |  1/4     |    108   |   1728    |  27 |  20G HBM2e | `GNa-27h-20h`  |
| A100       |  1/7     |     60   |    960    |  15 |  10G HBM2e | `GNa-15h-10h`  |
| A100X      |  1/1     |    432   |   6912    | 108 |  80G HBM2e | `GNa-108-80h`  |

##### Ada Lovelave (`l`)

No MIG support, 128 Cuda Cores and 4 Tesnro Cores per SM.

| nVidia GPU | Tensor C | Cuda Cores | SMs |    VRAM    | SCS name piece |
|------------|----------|------------|-----|------------|----------------|
|   L4       |   232    |   7424     |  58 |  24G GDDR6 | `GNl-58-24`    |
|  L40       |   568    |  18176     | 142 |  48G GDDR6 | `GNl-142-48`   |
|  L40G      |   568    |  18176     | 142 |  48G GDDR6 | `GNl-142h-48`  |
|  L40S      |   568    |  18176     | 142 |  48G GDDR6 | `GNl-142hh-48` |

##### Grace Hopper (`g`)

These have MIG support and 128 Cuda Cores and 4 Tensor Cores per SM.

| nVidia GPU | Fraction | Tensor C | Cuda Cores | SMs |    VRAM    | SCS GPU name   |
|------------|----------|----------|------------|-----|------------|----------------|
| H100       |  1/1     |   528    |  16896     | 132 |  80G HBM3  | `GNg-132-80h`  |
| H100       |  1/2     |   264    |   8448     |  66 |  40G HBM3  | `GNg-66-40h`   |
| H100       |  1/4     |   132    |   4224     |  33 |  20G HBM3  | `GNg-33-20h`   |
| H100       |  1/7     |    72    |   2304     |  18 |  10G HBM3  | `GNg-18-10h`   |
| H200       |  1/1     |   528    |  16896     | 132 | 141G HBM3e | `GNg-132-141h` |
| H200       |  1/2     |   264    |  16896     |  66 |  70G HBM3e | `GNg-66-70h`   |

#### AMD Radeon (`A`)

##### CDNA 2 (`2`)

One CU contains 64 Stream Processors.

|   AMD  GPU  | Stream Proc | CUs |    VRAM    | SCS name piece |
|-------------|-------------|-----|------------|----------------|
| Inst MI210  |     6656    | 104 |  64G HBM2e | `GA2-104-64h`  |
| Inst MI250  |    13312    | 208 | 128G HBM2e | `GA2-208-128h` |
| Inst MI250X |    14080    | 229 | 128G HBM2e | `GA2-220-128h` |

##### CDNA 3 (`3`)

SRIOV partitioning is possible, resulting in pass-through for
up to 8 partitions, somewhat similar to nVidia MIG. 4 Tensor
Cores and 64 Stream Processors per CU.

|   AMD  GPU  | Tensor C | Stream Proc | CUs |    VRAM    | SCS name piece |
|-------------|----------|-------------|-----|------------|----------------|
| Inst MI300X |   1216   |    19456    | 304 | 192G HBM3  | `GA3-304-192h` |
| Inst MI325X |   1216   |    19456    | 304 | 288G HBM3  | `GA3-304-288h` |

#### intel Xe (`I`)

##### Xe-HPC (Ponte Vecchio) (`12.7`)

1 EU corresponds to one Tensor Core and contains 128 Shading Units.

| intel DC GPU | Tensor C |  Shading U | EUs |    VRAM    | SCS name piece    |
|--------------|----------|------------|-----|------------|-------------------|
| Max 1100     |   56     |     7168   |  56 |  48G HBM2e | `GI12.7-56-48h`   |
| Max 1550     |  128     |    16384   | 128 | 128G HBM2e | `GI12.7-128-128h` |

## Automated tests

### Errors

The following items MUST be detected and reported as an error:

- any syntax error in a name starting with `SCS-`,
- any mismatch between any immediately discoverable property of a flavor (currently, CPU, RAM and disk size)
  and the meaning of its name (which is usually a lower bound), such as the CPU generation or hypervisor.

In addition, the following items MAY be reported as an error:

- any mismatch between any non-immediately discoverable property of flavor and the meaning of its name.

### Warnings

None so far.

### Implementation

The script [`flavor-names-openstack.py`](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/flavor-names-openstack.py)
talks to the OpenStack API of the cloud specified by the `OS_CLOUD` environment and queries properties and
checks the names for standards compliance.

## Manual tests

To be determined.
