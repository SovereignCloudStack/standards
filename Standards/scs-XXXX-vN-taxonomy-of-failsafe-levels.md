---
title: Taxonomy of Failsafe Levels
type: Decision Record
status: Draft
track: IaaS
---


## Abstract

Talking about redundancy and backups in the context of clouds, the scope under which circumstances these concepts work for various ressources is not clear.
This decision records aims to define different levels of failure-safety.
These levels can then be used in standards to clearly set the scope that certain procedures in e.g. OpenStack offer.

## Terminology

Image
  OpenStack resource, server images usually residing in a network storage backend.
Volume
  OpenStack resource, virtual drive which usually resides in a network storage backend.
Virtual Machine (abbr. VM)
  IaaS resource, also called server, executes workloads from users.
Secret
  OpenStack ressource, could be a key or a passphrase or a certificate in Barbican.
Key Encryption Key (abbr. KEK)
  OpenStack resource, used to encrypt other keys to be able to store them encrypted in a database.
floating IP (abbr. FIP)
  OpenStack resource, an IP that is usually reachable from the internet.
Disk
  A physical disc in a deployment.
Node
  A physical machine in a deployment.
Cyber threat
  Attacks on the cloud.

## Context

Some standards in will talk about or require procedures to backup resources or have redundancy for resources.
This decision record should discuss, which failure threats are CSPs facing and will group them into severel level.
In consequence these levels should be used in standards talking about redundancy or failure-safety.

## Decision

First there needs to be an overview about possible failure cases in deployments:

| Failure Case | Probability | Consequences |
|----|-----|----|
| Disk Failure/Loss | High | Data loss on this disk. Impact depends on type of lost data (data base, user data) |
| Node Outage | Medium to High | Data loss on node / (temporary) loss of functionality and connectivity of node (impact depends on type of node)  |
| Rack Outage | Medium | similar to Disk Failure and Node Outage |
| Power Outage (Data Center supply)  | Medium | potential data loss, temporary loss of functionality and connectivity of node (impact depends on type of node)  |
| Fire | Medium | permanently Disk and Node loss in the affected zone |
| Flood | Low | permanently Disk and Node loss in the affected zone |
| Earthquake | Very Low | permanently Disk and Node loss in the affected zone |
| Storm/Tornado | Low | permanently Disk and Node loss in the affected fire zone |
| Cyber threat  | High | permanently loss of data on affected Disk and Node  |

These failure case can result in temporary (T) or permanent (P) loss of the resource or data within.
Additionally there are a lot of resources in IaaS alone that are more or less affected by these Failure Cases.
The following table shows the affection without considering any redundancy or failure saftey being in use:

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

For some cases there are only temporary unavailabilites and clouds do have certain workflows to avoid data loss, like redundancy in storagy backends and databases.
So some of these outages are more easy to solve than others.
A possible way to group the failure cases into levels considering the matrix of affection would be:

| Level/Class | level of affection | Use Cases |
|---|---|-----|
| 1. Level | single volumes, VMs... | Disk Failure, Node outage, (maybe rack outage) |
| 2. Level | number of resources, most of the time recoverable | Rack outage, (Fire), (Power outage when different power supplies exist) |
| 3. Level | lots of resources / user data + potentially not recoverable | Fire, Earthquake, Storm/Tornado, Power Outage |
| 4. Level | complete deployment, not recoverable | Flood, Fire |

Unfortunately something similar does not seem to exist right now.

## Consequences

Using the definition of Levels throughout all SCS standards would allow readers to know up to which Level certain procedures or aspects of resources (e.g. volume types or a backend requiring redundancy) would protect their data.
