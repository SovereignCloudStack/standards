---
title: Volume Type Standard
type: Standard
status: Draft
track:  IaaS
---

## Introduction

Volume Types are used to classify volumes and provide a basic decision for what kind of volume should be created. These volume types can sometimes be very backend-specific and it might be hard for a user to choose the most suitable volume type, if there is more than one type.

### Glossary

The following special terms are used throughout this standard document:
| Term | Meaning |
|---|---|
| volume | OpenStack ressource, virtual drive which usually resides in a network storage backend |
| AZ | Availability Zone |
| Volume QoS | Quality of Service object for Volumes |

## Motivation

We want to standardize a few varieties of volume types. While a user can choose simple things like size when creating a volume, Volume Types define a few broader aspects of a volume. Encryption of volumes for example is solely decided by the volume type. While the option with which the volume will be replicated is a mix between definition in the volume type and backend specific configuration, but it's visibility can only be reached in the volume type. In the following part, we want to state, which varieties of volume types are REQUIRED, RECOMMENDED or only OPTIONAL within a SCS-compatible deployment.

## Design Considerations

All Considerations can be looked up in detail in the [Decision Record for the Volume Type Standard.](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

### Systematic Description of Volume Types

To test whether a deployment has volume types with certain aspects, the discoverability of the parameters in the volume type has to be given. As for the time this standard is created, there is no way for users to discover all aspects through OpenStack commands. Therefore the aspects, that are fulfilled within a volume type, should be stated in the beginning of the **description** of a volume type in the following manner:

`[scs:aspect1][scs:aspect2]...`

There is no sorting of aspects required. Every aspect should only be mentioned to the maximal amount of one.

### Standardized Aspects

The following table shows, which aspects are considered in this standard. The last column shows how the description of the volume type has to be adjusted, if the aspect is fulfilled:

| Aspect | Part of Standard | standardized description |
| ---- | ---- | ------ |
| Encryption | **Recommended** | **"[scs:encrypted]"** |
| Replication | **Recommended** | **"[scs:replicated]"** |

It is possible to use multiple of those aspects within one volume type. SCS will only ever look, if there is a volume type that has an aspect, but there don't have to be different volume types.
Example: one volume type that uses LUKS-encryption with a ceph storage with inherent replication would fulfill all recommendations of this standard.

## DEFAULT volume type

There is always a default volume type defined in an OpenStack deployment. This volume type is created in the setup of cinder and will always be present in any OpenStack deployments under the name `__default__`. The SCS does not have any requirements about this volume type at this moment, instead deployers are free to choose what fits best in their environment. Conversely, a cloud user can not expect any specific behavior or properties from volume types named `__default__`.

The parameters of volume types described in this standard do not have to be applied to the chosen default volume type. And the SCS will not make any assumptions about parameters being present in the default volume type.

## REQUIRED volume types

Currently the SCS will not require volume types with certain specification. This will change in the future.

## RECOMMENDED volume types

The SCS recommends to have one or more volume types, that satisfy the need for encrpytion and replication.

### Encryption

There SHOULD at least be one volume type with the encryption aspect.

Encryption for volumes is an option which has to be configured within the volume type. As an admin it is possible to set encryption-provider, key size, cipher and control location. Additionally to be discoverable by users an admin has to edit the description and add `[scs:encrypted]` at the beginning or after another scs aspect. It should look like this example:

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

There SHOULD at least be one volume type with the replication aspect.

Replication states, whether or not there are multiple replicas of a volume. Thus answers the question, whether the data could survive a node outage. Unfortunately there are two ways replication can be achieved:

1. In the configuration of a volume type. It then is visible as extra_spec in the properties of a volume type.
2. Via the used backend. Ceph for example provides automatic replication, that does not need to be specified in the volume type. This is currently not visible for users.

To fulfill this recommentation for now, the admin needs to add `[scs:replicated]` at the beginning or after any other scs aspect into the descriotion of the volume type.

### Example

One volume type that is configured as an encrypted volume type in a ceph backend, with automated replication would fit both recommendations and will be enough to comply to this part of the volume type standard.

It should look like the following part:

```text
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field              | Value                                                                                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| access_project_ids | None                                                                                                                                                         |
| description        | [scs:encrypted][scs:replicated] Content will be replicated three times to ensure consistency and availability for your data. LUKS encryption is used.        |
| id                 | d63307fb-167a-4aa0-9066-66595ea9fb21                                                                                                                         |
| is_public          | True                                                                                                                                                         |
| name               | hdd-three-replicas-LUKS                                                                                                                                      |
| properties         |                                                                                                                                                              |
| qos_specs_id       | None                                                                                                                                                         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

## OPTIONAL volume types

Any other aspects of volume types, that can be found in the decision record are OPTIONAL. They SHOULD NOT be referenced in the way this standard describes. Some of them already are natively discoverable by users, while others could be described in the name or description of a volume type. Users should look into the provided volume types of the CSPs, if they want to use some of these other aspects.

## Related Documents

[Here is the decision record document.](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

## Conformance Tests

As there are currently no REQUIRED volume types, we can only look for the RECOMMENDED aspects and thus executing a conformance test is not a must.
Furthermore the recommended aspects currently have to be described in the description by the deployer. In future versions we aim to integrate some extra_specs for them in upstream OpenStack
And it is also possible that a single volume type can currently fulfill all RECOMMENDED aspects.

The current test will check for the presence of `[encrypted]` and `[replicated]` in the description of at least one volume type.
