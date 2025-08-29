---
title: SCS Volume Types
type: Standard
status: Stable
stabilized_at: 2024-11-13
track: IaaS
---

## Introduction

A volume is a virtual drive that is to be used by an instance (i.e., a virtual machine). With OpenStack,
each volume is created per a type that determines basic features of the volume as provided by the backend,
such as encryption, replication, or quality of service. As of the writing of this document, presence or absence of these
features can not be discovered with full certainty by non-privileged users via the OpenStack API.

### Glossary

The following special terms are used throughout this standard document:
| Term | Meaning |
|---|---|
| volume | OpenStack resource, virtual drive which usually resides in a network storage backend |
| volume feature | A certain feature a volume can possess |
| aspect | Part of a volume type that will activate a corresponding feature in a created volume |
| AZ | Availability Zone |
| Volume QoS | Quality of Service object for Volumes |

## Motivation

As an SCS user, I want to be able to create volumes with certain common features, such as encryption or
replication, and to do so in a standardized manner as well as programmatically.
This standard outlines a way of formally advertising these common aspects for a volume type to
non-privileged users, so that the most suitable volume type can be discovered and selected easily — both by
the human user and by a program.

## Design Considerations

All considerations can be looked up in detail in the [Decision Record for the Volume Type Standard.](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

### Systematic Description of Volume Types

To test whether a deployment has volume types with certain aspects, the discoverability of the parameters in the volume type has to be given. As for the time this standard is created, there is no way for users to discover all aspects through OpenStack commands. Therefore, the aspects, that are fulfilled within a volume type, should be stated in the beginning of the **description** of a volume type in the following manner:

`[scs:aspect1, aspect2, ..., aspectN]...`

The mentioned aspects MUST be sorted alphabetically and every aspect should only be mentioned to the maximal amount of one.

### Standardized Aspects

The following table shows which aspects are considered in this standard. The third column shows how the description of the volume type has to be adjusted, if the aspect is fulfilled:

| Aspect | Requirement | standardized description | comment |
| ---- | ---- | ------ | ------ |
| Encryption | **Recommended** | **"[scs:encrypted]"** | volume is encrypted |
| Replication | **Recommended** | **"[scs:replicated]"** | volume is replicated to avoid data loss in a case of hardware failure |

It is possible to use multiple of those aspects within one volume type. There don't have to be different volume types for each aspect.
For instance, one volume type that uses LUKS-encryption with a ceph storage with inherent replication would fulfill all recommendations of this standard.

## DEFAULT volume type

There is always a default volume type defined in an OpenStack deployment. This volume type is created in the setup of cinder and will always be present in any OpenStack deployments under the name `__default__`. This standard does not have any requirements about this volume type at this moment, instead deployers are free to choose what fits best in their environment. Conversely, a cloud user can not expect any specific behavior or properties from volume types named `__default__`.

## REQUIRED volume types

Currently, this standard will not require volume types with certain specification.

## RECOMMENDED volume types

This standard recommends to have one or more volume types, that feature encryption and replication.

## OPTIONAL volume types

Any other aspects of volume types, that can be found in the decision record are OPTIONAL. They SHOULD NOT be referenced in the way this standard describes. Some of them already are natively discoverable by users, while others could be described in the name or description of a volume type. Users should look into the provided volume types of the Cloud Service Providers, if they want to use some of these other aspects.

## Implementation Details

### Encryption

Encryption for volumes is an option which has to be configured within the volume type. As an admin it is possible to set encryption-provider, key size, cipher and control location. Additionally to be discoverable by users, the description should start with an aspect list such as `[scs:encrypted]` (potentially with additional aspects). It should look like this example:

```text
openstack volume type show LUKS
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [scs:encrypted] This volume uses LUKS-encryption                                                                                                             |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | LUKS                                                                                                                                                         |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

### Replication

Replication states whether or not there are multiple replicas of a volume, i.e., whether the data could survive a node outage. Unfortunately, there are two ways replication can be achieved:

1. In the configuration of a volume type. It then is visible as extra_spec in the properties of a volume type.
2. Via the used backend. Ceph for example provides automatic replication, that does not need to be specified in the volume type. This is currently not visible for users.

To fulfill this recommendation, the description should start with an aspect list such as `[scs:replicated]` (potentially with additional aspects).

### Example

One volume type that is configured as an encrypted volume type in a ceph backend, with automated replication would fit both recommendations and will be enough to comply to this part of the volume type standard.

It should look like the following part:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [scs:encrypted, replicated] Content will be replicated three times to ensure consistency and availability for your data. LUKS encryption is used.        |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-LUKS                                                                                                                                      |
| properties         |                                                                                                                                                              |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

## Related Documents

- corresponding [decision record document](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)
