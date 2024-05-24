---
title: Taxonomy of Failsafe Levels
type: Decision Record
status: Draft
track: IaaS
---


## Abstract

When talking about redundancy and backups in the context of cloud infrastructures, the scope under which circumstances these concepts apply to various ressources is neither homogenous nor intuitive.
This decision record aims to define different levels of failure-safety.
These levels can then be used in standards to clearly set the scope that certain procedures in e.g. OpenStack offer.

## Glossary

| Term               | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Virtual Machine    | Equals the `server` resource in Nova.                                                                                                    |
| Ironic Machine     | A physical node managed by Ironic or as a `server` resource in Nova.                                                                     |
| Ephemeral Storage  | Disk storage directly supplied to a virtual machine by Nova. Different from volumes.                                                     |
| (Glance) Image     | IaaS resource usually storing raw disk data. Managed by the Glance service.                                                              |
| (Cinder) Volume    | IaaS resource representing block storage disk that can be attached as a virtual disk to virtual machines. Managed by the Cinder service. |
| (Volume) Snapshot  | Thinly-provisioned copy-on-write snapshots of volumes. Stored in the same Cinder storage backend as volumes.                             |
| Volume Type        | Attribute of volumes determining storage details of a volume such as backend location or whether the volume will be encrypted.           |
| (Barbican) Secret  | IaaS resource storing cryptographic assets such as encryption keys. Managed by the Barbican service.                                     |
| Key Encryption Key | IaaS resource, used to encrypt other keys to be able to store them encrypted in a database.                                              |
| Floating IP        | IaaS resource, an IP that is usually routed and accessible from external networks.                                                       |
| Disk               | A physical disk drive (e.g. HDD, SSD) in the infrastructure.                                                                             |
| Node               | A physical machine in the infrastructure.                                                                                                |
| Cyber threat       | Attacks on the infrastructure through the means of electronic access.                                                                    |

## Context

Some standards provided by the SCS project will talk about or require procedures to backup resources or have redundancy for resources.
This decision record should discuss, which failure threats are CSP-facing and will classify them into several levels.
In consequence these levels should be used in standards concerning redundancy or failure-safety.

## Decision

First there needs to be an overview about possible failure cases in infrastructures as well as their probability of occurance and the damage they may cause:

| Failure Case | Probability | Consequences |
|----|-----|----|
| Disk Failure/Loss | High | Permanent data loss in this disk. Impact depends on type of lost data (data base, user data) |
| Node Failure/Loss (without disks) | Medium to High | Permanent loss of functionality and connectivity of node (impact depends on type of node) |
| Node Outage | Medium to High | Data loss in RAM and temporary loss of functionality and connectivity of node (impact depends on type of node) |
| Rack Outage | Medium | Outage of all nodes in rack |
| Power Outage (Data Center supply) | Medium | temporary outage of all nodes in all racks |
| Fire | Medium | permanent Disk and Node loss in the affected zone |
| Flood | Low | permanent Disk and Node loss in the affected zone |
| Earthquake | Very Low | permanent Disk and Node loss in the affected zone |
| Storm/Tornado | Low | permanent Disk and Node loss in the affected fire zone |
| Cyber threat | High | permanent loss or compromise of data on affected Disk and Node |
| Software Bug | High | permanent loss or compromise of data that trigger the bug up to data on the whole physical machine |

These failure cases can result in temporary (T) or permanent (P) loss of the resource or data within.
Additionally there are a lot of resources in IaaS alone that are more or less affected by these Failure Cases.
The following table shows the impact when no redundancy or failure safety measure is in place:

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | natural catastrophy | Cyber threat | Software Bug |
|----|----|----|----|----|----|----|----|
| Image | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| Volume | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| User Data on RAM /CPU | | P | P | P | P | T/P | P |
| volume-based VM | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| ephemeral-based VM | P (if on disk) | P | P | T | P (T if lucky) | T/P | P |
| Ironic-based VM | P (all data on disk) | P | P | T | P (T if lucky) | T/P | P |
| Secret | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| network configuration (DB objects) | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| network connectivity (materialization) | | T (if on node) | T/P | T | P (T if lucky) | T/P | T |
| floating IP | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | T |

For some cases, this only results in temporary unavailabilities and cloud infrastructures usually have certain mechanisms in place to avoid data loss, like redundancy in storage backends and databases.
So some of these outages are easier to mitigate than others.
A possible way to classify the failure cases into levels considering the matrix of impact would be, to classify the failure cases from small to big ones.
The following table shows such a classification, the occurance probability of a failure case of each class and what resources with user data might be affected.

:::caution

This table only contains examples of failure cases and examples of affected resources.
This should not be used as a replacement for a risk analysis.
The column **user hints** only show examples of standards that may provide this class of failure safety for a certain resource.
Customers should always check, what they can do to protect their data and not rely solely on the CSP.

:::

| Level/Class | Probability | Failure Causes | loss in IaaS | User Hints |
|---|---|---|-----|-----|
| 1. Level | Very High | small Hardware or Software Failures (e.g. Disk/Node Failure, Software Bug,...) | individual volumes, VMs... | [volume replication](https://docs.scs.community/standards/scs-0114-v1-volume-type-standard) |
| 2. Level | High | important Hardware or Software Failures (e.g. Rack outage, small Fire, Power outage, ...) | limited number of resources, sometimes recoverable | [volume backups](https://github.com/SovereignCloudStack/standards/pull/567) |
| 3. Level | Medium | small catastrophes or major Failures (e.g. fire, regional Power Outage, orchestrated cyber attacks,...) | lots of resources / user data + potentially not recoverable | Availability Zones, user responsibility |
| 4. Level | Low | whole deployment loss (e.g. natural desaster,...) | entire infrastructure, not recoverable | user responsibility |

Based on our research, no similar standardized classification scheme seems to exist currently.
Something close but also very detailed can be found in [this (german)](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_3.pdf?__blob=publicationFile&v=2) from the BSI.
As we want to focus on IaaS resources and also have an easily understandable structure that can be applied in standards covering replication, redundancy and backups, this document is too detailed.

## Consequences

Using the definition of levels established in this decision record throughout all SCS standards would allow readers to understand up to which level certain procedures or aspects of resources (e.g. volume types or a backend requiring redundancy) would protect their data and/or resource availability.
