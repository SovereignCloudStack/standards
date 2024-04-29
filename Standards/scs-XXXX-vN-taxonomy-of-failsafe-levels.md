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

## Terminology

Image
  OpenStack resource, virtual machine images usually residing in a network storage backend.
Volume
  OpenStack resource, virtual drive which usually resides in a network storage backend.
Virtual Machine (abbr. VM)
  IaaS resource, also called server, executes workloads from users.
Secret
  OpenStack ressource, cryptographic asset stored in the Key Manager (e.g. Barbican).
Key Encryption Key (abbr. KEK)
  OpenStack resource, used to encrypt other keys to be able to store them encrypted in a database.
Floating IP (abbr. FIP)
  OpenStack resource, an IP that is usually routed and accessible from external networks.
Disk
  A physical disk drive (e.g. HDD, SSD) in the infrastructure.
Node
  A physical machine in the infrastructure.
Cyber threat
  Attacks on the infrastructure through the means of electronic access.

## Context

Some standards provided by the SCS will talk about or require procedures to backup resources or have redundancy for resources.
This decision record should discuss, which failure threats are CSP-facing and will classify them into several levels.
In consequence these levels should be used in standards concerning redundancy or failure-safety.

## Decision

First there needs to be an overview about possible failure cases in infrastructures:

| Failure Case | Probability | Consequences |
|----|-----|----|
| Disk Failure/Loss | High | Data loss on this disk. Impact depends on type of lost data (data base, user data) |
| Node Outage | Medium to High | Data loss on node / (temporary) loss of functionality and connectivity of node (impact depends on type of node)  |
| Rack Outage | Medium | similar to Disk Failure and Node Outage |
| Power Outage (Data Center supply)  | Medium | potential data loss, temporary loss of functionality and connectivity of node (impact depends on type of node)  |
| Fire | Medium | permanent Disk and Node loss in the affected zone |
| Flood | Low | permanent Disk and Node loss in the affected zone |
| Earthquake | Very Low | permanent Disk and Node loss in the affected zone |
| Storm/Tornado | Low | permanent Disk and Node loss in the affected fire zone |
| Cyber threat  | High | permanent loss or compromise of data on affected Disk and Node  |

These failure cases can result in temporary (T) or permanent (P) loss of the resource or data within.
Additionally there are a lot of resources in IaaS alone that are more or less affected by these Failure Cases.
The following table shows the impact when no redundancy or failure safety measure is in place:

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | natural catastrophy | Cyber threat |
|----|----|----|----|----|----|----|
| Image | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |
| Volume | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |
| User Data on RAM /CPU | | P | P | P | P | T/P |
| volume-based VM | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |
| ephemeral-based VM | P (if on disk) | P | P | T | P (T if lucky) | T/P |
| Secret | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |
| network configuration (DB objects) | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |
| network connectivity (materialization) | | T (if on node) | T/P | T | P (T if lucky) | T/P |
| floating IP | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P |

For some cases, this only results in temporary unavailabilities and cloud infrastructures usually have certain mechanisms in place to avoid data loss, like redundancy in storage backends and databases.
So some of these outages are easier to mitigate than others.
A possible way to classify the failure cases into levels considering the matrix of impact would be:

| Level/Class | level of impact | Use Cases |
|---|---|-----|
| 1. Level | individual volumes, VMs... | Disk Failure, Node outage, (maybe rack outage) |
| 2. Level | limited number of resources, most of the time recoverable | Rack outage, (Fire), (Power outage when different power supplies exist) |
| 3. Level | lots of resources / user data + potentially not recoverable | Fire, Earthquake, Storm/Tornado, Power Outage |
| 4. Level | entire infrastructure, not recoverable | Flood, Fire |

Based on our research, no similar standardized classification scheme seems to exist currently.
Thus, this decision record establishes its own.

## Consequences

Using the definition of levels established in this decision record throughout all SCS standards would allow readers to understand up to which level certain procedures or aspects of resources (e.g. volume types or a backend requiring redundancy) would protect their data and/or resource availability.
