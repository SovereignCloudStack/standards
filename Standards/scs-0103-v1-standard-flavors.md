---
title: SCS Standard Flavors and Properties
type: Standard
status: Stable
stabilized_at: 2024-02-08
track: IaaS
description: |
  The SCS-0103 standard outlines mandatory and recommended specifications for flavors and properties in OpenStack
  environments to ensure uniformity across SCS clouds. Mandatory and recommended flavors are defined with specific
  configurations of vCPUs, vCPU types, RAM, and root disk sizes, alongside extra specs like scs:name-vN, scs:cpu-type,
  and scs:diskN-type to detail the flavor's specifications. This standard facilitates guaranteed availability and
  consistency of flavors, simplifying the deployment process for DevOps teams.
---

## Introduction

This is v1.1 of the standard, which lifts the following restriction regarding the property `scs:name-vN`:
this property may now be used on any flavor, rather than standard flavors only. In addition, the "vN" is
now interpreted as "name variant N" instead of "version N of the naming standard". Note that this change
indeed preserves compliance, i.e., compliance with v1.0 implies compliance with v1.1.

## Terminology

extra_specs
  Additional properties on an OpenStack flavor, see
  [OpenStack Nova user documentation](https://docs.openstack.org/nova/2024.1/user/flavors.html#extra-specs)
  and
  [OpenStack Nova configuration documentation](https://docs.openstack.org/nova/2024.1/configuration/extra-specs.html).

## Motivation

In OpenStack environments there is a need to define different flavors for instances.
The flavors are pre-defined by the operator, the customer can not change these.
OpenStack providers thus typically offer a large selection of flavors.

While flavors can be discovered (`openstack flavor list`), it is helpful for users (DevOps teams),
to have a guaranteed set of flavors available on all SCS clouds, so these need not be discovered.

## Properties (extra_specs)

The following extra_specs are recognized, together with the respective semantics:

- `scs:name-vN=NAME` (where `N` is a positive integer, and `NAME` is some string) means that
  `NAME` is a valid name for this flavor according to any major version of the [SCS standard on
  flavor naming](https://docs.scs.community/standards/iaas/scs-0100).
- `scs:cpu-type=shared-core` means that _at least 20% of a core in >99% of the time_,
  measured over the course of one month (1% is 7,2 h/month). The `cpu-type=shared-core`
  corresponds to the `V` cpu modifier in the [flavor-naming spec](./scs-0100-v3-flavor-naming.md),
  other options are `crowded-core` (`L`), `dedicated-thread` (`T`) and `dedicated-core` (`C`).
- `scs:diskN-type=ssd` (where `N` is a non-negative integer, usually `0`) means that the
  root disk `N` must support 1000 _sequential_ IOPS per VM, and it must be equipped with
  power-loss protection; see [scs-0110-v1-ssd-flavors](./scs-0110-v1-ssd-flavors.md).
  The `disk`N`-type=ssd` setting corresponds to the `s` disk modifier, other options
  are `nvme` (`p`), `hdd` (`h`) and `network` (`n`). Only flavors without disk and
  those with `diskN-type=network` can be expected to support live-migration.

Whenever ANY of these are present on ANY flavor, the corresponding semantics must be satisfied.

The extra_spec `scs:name-vN` is to be interpreted as "name variant N". This name scheme is designed to be
backwards compatible with v1.0 of this standard, where `scs:name-vN` is interpreted as
"name according to naming standard vN". We abandon this former interpretation for two reasons:

1. the naming standards admit multiple (even many) names for the same flavor, and we want to provide a means
   of advertising more than one of them (said standards recommend using two: a short one and a long one),
2. the same flavor name may be valid according to multiple versions at the same time, which would lead to
   a pollution of the extra_specs with redundant properties; for instance, the name
   `SCS-4V-16` is valid for both [scs-0100-v2](scs-0100-v2-flavor-naming.md) and
   [scs-0100-v3](scs-0100-v3-flavor-naming.md), and, since it does not use any extension, it will be valid
   for any future version that only changes the extensions, such as the GPU vendor and architecture.

Note that it is not required to use consecutive numbers to number the name variants.
This way, it becomes easier to remove a single variant (no "closing the gap" required).

If extra_specs of the form `scs:name-vN` are used to specify SCS flavor names, it is RECOMMENDED to include
names for the latest stable major version of the standard on flavor naming.

## Standard SCS flavors

Following are flavors that must exist on standard SCS clouds (x86-64).
Note that this statement does not preclude the existence of additional flavors.

### Mandatory

| Recommended name | vCPUs  | vCPU type     | RAM [GiB]  | Root disk [GB]  | Disk type  |
| ---------------- | ------ | ------------- | ---------- | --------------- | ---------- |
| SCS-1V-4         |      1 | shared-core   |          4 |                 |            |
| SCS-2V-8         |      2 | shared-core   |          8 |                 |            |
| SCS-4V-16        |      4 | shared-core   |         16 |                 |            |
| SCS-4V-16-100s   |      4 | shared-core   |         16 |             100 | ssd        |
| SCS-8V-32        |      8 | shared-core   |         32 |                 |            |
| SCS-1V-2         |      1 | shared-core   |          2 |                 |            |
| SCS-2V-4         |      2 | shared-core   |          4 |                 |            |
| SCS-2V-4-20s     |      2 | shared-core   |          4 |              20 | ssd        |
| SCS-4V-8         |      4 | shared-core   |          8 |                 |            |
| SCS-8V-16        |      8 | shared-core   |         16 |                 |            |
| SCS-16V-32       |     16 | shared-core   |         32 |                 |            |
| SCS-1V-8         |      1 | shared-core   |          8 |                 |            |
| SCS-2V-16        |      2 | shared-core   |         16 |                 |            |
| SCS-4V-32        |      4 | shared-core   |         32 |                 |            |
| SCS-1L-1         |      1 | crowded-core  |          1 |                 |            |

### Recommended

| Recommended name | vCPUs  | vCPU type     | RAM [GiB]  | Root disk [GB]  | Disk type  |
| ---------------- | ------ | ------------- | ---------- | --------------- | ---------- |
| SCS-1V-4-10      |      1 | shared-core   |          4 |              10 | (any)      |
| SCS-2V-8-20      |      2 | shared-core   |          8 |              20 | (any)      |
| SCS-4V-16-50     |      4 | shared-core   |         16 |              50 | (any)      |
| SCS-8V-32-100    |      8 | shared-core   |         32 |             100 | (any)      |
| SCS-1V-2-5       |      1 | shared-core   |          2 |               5 | (any)      |
| SCS-2V-4-10      |      2 | shared-core   |          4 |              10 | (any)      |
| SCS-4V-8-20      |      4 | shared-core   |          8 |              20 | (any)      |
| SCS-8V-16-50     |      8 | shared-core   |         16 |              50 | (any)      |
| SCS-16V-32-100   |     16 | shared-core   |         32 |             100 | (any)      |
| SCS-1V-8-20      |      1 | shared-core   |          8 |              20 | (any)      |
| SCS-2V-16-50     |      2 | shared-core   |         16 |              50 | (any)      |
| SCS-4V-32-100    |      4 | shared-core   |         32 |             100 | (any)      |
| SCS-1L-1-5       |      1 | crowded-core  |          1 |               5 | (any)      |

### Guarantees and properties

The figures given in the table (number of CPUs, amount of RAM, root disk size) must match
precisely the corresponding figures in the flavor.

In addition, the following properties must be set (in the `extra_specs`):

- `scs:name-v1` to the recommended name, but with each dash AFTER the first one replaced by a colon,
- `scs:name-v2` to the recommended name,
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

The script [`flavors-openstack.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/standard-flavors/flavors-openstack.py)
will read the lists of mandatory and recommended flavors
from a yaml file provided as command-line argument, connect to an OpenStack installation,
and check whether the flavors are present and their extra_specs are correct.

Missing flavors will be reported on various logging channels: error for mandatory, warning for
recommended flavors. Incorrect extra_specs will be reported as error in any case.
The return code will be non-zero if the test could not be performed or if any error was
reported.

The script does not check whether a name given via the extra_spec `scs:name-vN` is indeed valid according
to any major version of the SCS standard on flavor naming.

## Operational tooling

The [openstack-flavor-manager](https://github.com/osism/openstack-flavor-manager) is able to
create all standard, mandatory SCS flavors for you. It takes input that can be generated by
`flavor-manager-input.py`.

## Previous standard versions

The list of standard flavors used to be part of the flavor naming standard up until
[version 3](scs-0100-v3-flavor-naming.md). The following changes have been made to
the list in comparison with said standard:

- the flavor names have been turned into recommendations, and
- the properties have been introduced in order to help discoverability.

Note that the flavors with fixed size root disks have all moved to Recommended
with [scs-0100-v3](scs-0100-v3-flavor-naming.md).
This means that they are not a certification requirement any longer,
but we still recommend implementing these for backwards compatibility reasons.
Also in that standard, two flavors with SSD+ root disks have been added, as defined in
[scs-0110-v1-ssd-flavors.md](scs-0110-v1-ssd-flavors.md)
