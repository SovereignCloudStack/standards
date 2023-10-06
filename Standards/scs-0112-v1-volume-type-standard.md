---
title: Volume Type Standard
type: Standard
status: Draft
track:  IaaS
---

## Introduction

Volume Types are used to classify volumes and provide a basic decision for what kind of volume should be created. These volume types can sometimes be very backend-specific and it might be hard for a user to choose the most suitable volume type, if there is more than one default type.

### Glossary

The following special terms are used throughout this standard document:
| Term | Meaning |
|---|---|
| volume | OpenStack object, virtual drive which usually resides in a network storage backend |
| AZ | Availability Zone |
| Volume QoS | Quality of Service object for Volumes |

## Motivation

We want to standardize a few varieties of volume types. While a user can choose simple things like size when creating a volume, Volume Types define a few broader aspects of volume. Encryption of volumes for example is solely decided by the volume type. And whether the volume will be replicated is a mix between definiton in the volume type and backend specific configuration, but it's visiblity can only be reached in the volume type. In the following part, we want to state, which varieties of volume types are

## Design Considerations

All Considerations can be looked up in detail in the Decision Record for the Volume Type Standard.

To test whether a deployment has volume types with certain aspects, the discoverability of the parameters in the volume type has to be given. The following table shows, which aspects are considered in this standard and whether it is discoverable, and who can discover this. The comments state what can be done to help with the discoverability and other important restrictions.

| Aspect | Standardize? | Discoverability | comments |
| ---- | ---- | ---- | ------ |
| encryption | **Recommended** | admin only | Upstream work for extra_spec: encrypted=True/False needed |
| Backend name | - | - | - |
| AZs | **Optional** | - | Upstream: setable extra_spec would help |
| multiattach | **Optional** | yes | - |
| Replication | **Recommended** | backend-dependend | Upstream: setable extra_spec would help |
| Number of Replicas, etc | **Optional** | backend-dependend | Upstream: setable extra_spec would help |
| Volume QoS | **Optional** | admin only | depends on the admin only volume qos object |

In addition it is possible to use multiple of those aspects within one volume type. SCS will only ever look, if there is a volume type that has an aspect, but they don't have to be different volume types.
Example: one volume type that uses LUKS-encryption with a ceph storage with inherent replication would fulfill all recommendations of this standard.

## DEFAULT volume types

There is always a default volume type defined in an OpenStack deployment. The SCS does not have any requirements about this volume type at this moment, instead deployers are free to choose what fits best in their environment.

The parameters of volume types described in this standard do not have to be applied to the chosen default volume type. And the SCS will not make any assumptions about parameters being present in the default volume type.

## REQUIRED volume types

Currently the SCS will not require volume types with certain specification. This might change in the future.

## RECOMMENDED volume types

The SCS recommends to have one or more volume types, which have the following specifications:

### Encryption

Encryption for volumes is an option which has to be configured within the volume type. As an admin it is possible to set encryption-provider, key size, cipher and control location. And for admins it is also currently possible to see these configurations in a volume type with both list and show commands.

```text
openstack volume type list --encryption-type
+--------------------------------------+-------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ID                                   | Name        | Is Public | Encryption                                                                                                                                                                         |
+--------------------------------------+-------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| d34b5de0-d7bf-43cf-8a74-3827169d6616 | LUKS        | True      | cipher='aes-xts-plain64', control_location='front-end', encryption_id='217386bc-1e9b-46a3-9e0e-3ad62c07826c', key_size='256', provider='nova.volume.encryptors.luks.LuksEncryptor' |
+--------------------------------------+-------------+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

**TODO**:
Users that don't have admin rights currently cannot see these encryption parameters. We want and need to change this in the OpenStack workflow through adding a property (e.g. "encryption"="true") that is also visible for users. This way we will be able to automatically check whether a volume type with encyrption is present. It should look like this:

```text
openstack volume type show LUKS
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | None                                                                                                                                                         |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | LUKS                                                                                                                                                         |
| properties         | encrypted='true'                                                                                                                                             |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

Until this change happened, it will be necessary that deployer state that the volume type is encrypted in the description of the volume type in the following way:
The description needs to begin with `[encrypted]`, after that any further description is allowed. It should look like this example:

```text
openstack volume type show LUKS
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [encrypted] This volume uses LUKS-encryption                                                                                                                 |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | LUKS                                                                                                                                                         |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

### Replication

Replication states, whether or not there are multiple replicas of a volume. Thus answers the question, whether the data could survive a node outage. Unfortunately there are two ways replication can be achieved:

1. In the configuration of a volume type. It then is visible as extra_spec in the properties of a volume type.
2. Via the used backend. Ceph for example provides automatic replication, that does not need to be specified in the volume type. This is currently not visible for users.

To fulfill this recommentation for now, the deployer needs to state the replication in the description of a volume type in the following way:
The description needs to begin with `[replicated]`, after that any further description is allowed.

**TODO:**
We want to find a way to also use the internal extra_spec for replication, when the replication is automatically done by the backend. If this is not possible, we would like to introduce another property, which has to be set by the admin, when setting the volume type. Only after that we will have the possibility to automatically check for a volume type with replication.

#### OPTIONAL addition: Number of Replicas

Additionally to the fact, that a volume type is replicated, it OPTIONALLY can be stated in the description or name, how many times the provisioned volume will be replicated.

### Example

One volume type that is configured as an encrypted volume type in a ceph backend, with automated replication would fit both recommendations and will be enough to comply to this part of the volume type standard.

It should look like the following part:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [encrypted][replicated] Content will be replicated three times to ensure consistency and availability for your data. LUKS encryption is used.                |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-LUKS                                                                                                                                      |
| properties         |                                                                                                                                                              |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

It is OPTIONAL to give more information to users like this:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [encrypted:cipher=aes,key_size=256][replicated] Content will be replicated three times and LUKS encryption is used.                                          |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-LUKS                                                                                                                                      |
| properties         |                                                                                                                                                              |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

## OPTIONAL volume types

In this section volume types are described, that we do not want to explicitly recommend, but find them worth listing as optional for deployers.

### Availability Zones

Availability Zones are not necessarily used by every deployer of a cloud. The SCS does not want do make it necessary to have AZs for a compatible deployment. But we want to encourage deployer who use multiple AZs to read the following:

While there can be multiple Compute AZs, there can also be multiple Storage AZs for Volumes. And it might be quite confusing for users, which volumes can be used in which AZs. To make it even further complicated, there are backends like ceph, which can provide volumes for multiple compute AZs just with some Nova configuration. Therefore we would encourage to use either the property of volume types OR the description of the volume types to describe, in which AZs the volumes based on this type can be used.

A description for a ceph volume type might look like this:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | Content will be replicated three times on spinning disks to ensure consistency and availability for your data. The volumes can be used in AZ 1,3,4.          |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-AZ134                                                                                                                                     |
| properties         |                                                                                                                                                              |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

### Multiattach

A few backends enable providers to allow volumes to be attached to mulitple VMs simultaneously. The OpenStack API can be used to enable the usage of multiattach through the volume type. The property is also automatically shown to users. If a deployer want to use this feature they have to do it in this way. So users will always see whether a volume type can be used for mulitattach volumes or not. Nevertheless due to other problems, that might occur when using the multiattach feature, the SCS will only have this as OPTIONAL.

### Volume QoS

Quality of Service for volumes can be defined in volume qos objects. While admins can use these directly on volumes, a user is not able to see these object. Instead there can be ONE volume qos object associated to a volume type, which is then be used on all volumes created from that volume type. Through this indirection, functioning volume types without these associated qos objects and this feature not being heavily used, the SCS will currently only state this as an OPTIONAL volume type feature.

To make users aware that a volume type includes specific qos options, we recommend to write it into the description of a volume type, as any association to a volume qos object cannot be seen by normal users:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | Content will be replicated three times on spinning disks to ensure consistency and availability for your data. Iops: read:20k, write:10k               |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-AZ134                                                                                                                                     |
| properties         |
                                  |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

## Related Documents

[Here is the decision record document.](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

## Conformance Tests

As there are currently no REQUIRED volume types, we can only look for the RECOMMENDED aspects and thus executing a conformance test is not a must.
Furthermore the recommended aspects currently have to be described in the description by the deployer. In future versions we aim to integrate some extra_specs for them in upstream OpenStack
And it is also possible that a single volume type can currently fulfill all RECOMMENDED aspects.

**TODO:** The current test will check for the presence of `[encrypted]` and `[replicated]` in the description of at least one volume type.
