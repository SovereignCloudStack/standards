---
title: SCS Standard Flavors
type: Standard
status: Draft
track: IaaS
---

## Introduction

## Motivation

In OpenStack environments there is a need to define different flavors for instances.
The flavors are pre-defined by the operator, the customer can not change these.
OpenStack providers thus typically offer a large selection of flavors.

While flavors can be discovered (`openstack flavor list`), it is helpful for users (DevOps teams),
to have a guaranteed set of flavors available on all SCS clouds, so these need not be discovered.

## Standard SCS flavors

These are flavors that must exist on standard SCS clouds (x86-64).

### Mandatory

| Recommended name | vCPUs  | vCPU type     | RAM [GiB]  | Root disk [GB]  | Disk type  |
| ---------------- | ------ | ------------- | ---------- | --------------- | ---------- |
| SCS-1V-4         |      1 | shared core   |          4 |                 |            |
| SCS-2V-8         |      2 | shared core   |          8 |                 |            |
| SCS-4V-16        |      4 | shared core   |         16 |                 |            |
| SCS-8V-32        |      8 | shared core   |         32 |                 |            |
| SCS-1V-2         |      1 | shared core   |          2 |                 |            |
| SCS-2V-4         |      2 | shared core   |          4 |                 |            |
| SCS-4V-8         |      4 | shared core   |          8 |                 |            |
| SCS-8V-16        |      8 | shared core   |         16 |                 |            |
| SCS-16V-32       |     16 | shared core   |         32 |                 |            |
| SCS-1V-8         |      1 | shared core   |          8 |                 |            |
| SCS-2V-16        |      2 | shared core   |         16 |                 |            |
| SCS-4V-32        |      4 | shared core   |         32 |                 |            |
| SCS-1L-1         |      1 | crowded core  |          1 |                 |            |

### Recommended

| Recommended name | vCPUs  | vCPU type     | RAM [GiB]  | Root disk [GB]  | Disk type  |
| ---------------- | ------ | ------------- | ---------- | --------------- | ---------- |
| SCS-1V-4-10      |      1 | shared core   |          4 |              10 | (any)      |
| SCS-2V-8-20      |      2 | shared core   |          8 |              20 | (any)      |
| SCS-4V-16-50     |      4 | shared core   |         16 |              50 | (any)      |
| SCS-4V-16-100s   |      4 | shared core   |         16 |             100 | ssd        |
| SCS-8V-32-100    |      8 | shared core   |         32 |             100 | (any)      |
| SCS-1V-2-5       |      1 | shared core   |          2 |               5 | (any)      |
| SCS-2V-4-10      |      2 | shared core   |          4 |              10 | (any)      |
| SCS-2V-4-20s     |      2 | shared core   |          4 |              20 | ssd        |
| SCS-4V-8-20      |      4 | shared core   |          8 |              20 | (any)      |
| SCS-8V-16-50     |      8 | shared core   |         16 |              50 | (any)      |
| SCS-16V-32-100   |     16 | shared core   |         32 |             100 | (any)      |
| SCS-1V-8-20      |      1 | shared core   |          8 |              20 | (any)      |
| SCS-2V-16-50     |      2 | shared core   |         16 |              50 | (any)      |
| SCS-4V-32-100    |      4 | shared core   |         32 |             100 | (any)      |
| SCS-1L-1-5       |      1 | crowded core  |          1 |               5 | (any)      |

### Guarantees and properties

The following guarantees must be met:

- A "shared core" means _at least 20% of a core in >99% of the time_, measured over the
  course of one month (1% is 7,2 h/month).
- A disk of type "ssd" must support 1000 _sequential_ IOPS per VM and it must be equipped
  with power-loss protection; see [scs-0110-v1-ssd-flavors](./scs-0110-v1-ssd-flavors.md).

The following properties must be set (in the `extra_specs`):

- `scs:name-v4` to the recommended name,
- `scs:cpu-type` to `shared-core` or `crowded-core`, reflecting the vCPU type,
- `scs:disk0-type` not set if no disk is provided, otherwise set to `ssd` or some other
  value, reflecting the disk type.

### Remarks

We expect the most used vCPU:RAM[GiB] ratio to be 1:4.

Note that all vCPUs of SCS standard flavors are oversubscribed — the smallest `1L-1`
flavor allows for heavy oversubscription (note the `L`), and thus can be offered very
cheaply — imagine jump hosts ...

The design allows for small clouds (with CPUs with 16 Threads, 64GiB RAM
compute hosts) to offer all flavors.

Except for the two flavors with SSD root volume, disks types are not specified
(and expected to be network disks (Ceph/Cinder) or local SATA/SAS disks typically).

We only included a limited variation of disk sizes — this reflects that
for the standard networked cinder
disks, you can pass `block_device_mapping_v2` on server (VM) creation to
allocate a boot disk of any size you desire. We have scaled the few
recommended disk sizes with the amount of RAM. For each flavor there is
also one _without_ a pre-attached disk — these are meant to be used
to boot from a volume (either created beforehand or allocated on-the-fly
with `block_device_mapping_v2`, e.g.
`openstack server create --flavor SCS-1V-2 --block-device-mapping sda=IMGUUID:image:12:true`
to create a bootable 12G cinder volume from image `IMGUUID` that gets tied to the VM
instance life cycle.)

## Conformance Tests

The script `flavors-openstack.py` will read the lists of mandatory and recommended flavors
from a yaml file provided as command-line argument, connect to an OpenStack installation,
and check whether the flavors are present and their extra specs are correct. Missing
flavors will be reported on various logging channels: error for mandatory, info for
recommended flavors. Incorrect extra specs will be reported as error in any case.
The return code will be non-zero if the test could not be performed or if any error was
reported.

## Operational tooling

The [openstack-flavor-manager](https://github.com/osism/openstack-flavor-manager) is able to
create all standard, mandatory SCS flavors for you. It takes input that can be generated by
`flavor-manager-input.py`.

## Previous standard versions

The list of standard flavors used to be part of the flavor naming standard up until
[version 3](scs-0100-v3-flavor-naming.md). The following changes have been made to
the list in comparison with said standard:

- two flavors with ssds have been relegated to recommended status,
- the flavor names have been turned into recommendations, and
- the properties have been introduced in order to help discoverability.

Note that the flavors with fixed size root disks have all moved to Recommended
with [scs-0100-v3](scs-0100-v3-flavor-naming.md).
This means that they are not a certification requirement any longer,
but we still recommend implementing these for backwards compatibility reasons.
Also in that standard, two flavors with SSD+ root disks have been added, as defined in
[scs-0110-v1-ssd-flavors.md](scs-0110-v1-ssd-flavors.md)
