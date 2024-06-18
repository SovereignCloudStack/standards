---
title: Availability Zones Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

On the IaaS-Level especially in OpenStack it is possible to group resources in Availability Zones.
Such Zones often are mapped to the physical layer of a deployment, such as e.g. physical separation of hardware or redundancy of power circuits or fire zones.
But how CSPs apply Availability Zones to the IaaS Layer in one deplyoment may differ widely.
Therefore this standard will address the minimal requirements that need to be met, when creating Avaiability Zones.

## Terminology

| Term               | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Availability Zone  | (also: AZ) internal representation of physical grouping of service hosts, which also lead to internal grouping of resources.             |
| Fire Zone          | A physical separation in a data center that will contain fire within it. Effectively stopping spreading of fire.                         |
| PDU                | Power Distribution Unit, used to distribute the power to all physical machines of a single server rack.                                  |
| Compute            | A generic name for the IaaS service, that manages virtual machines (e.g. Nova in OpenStack).                                             |
| Network            | A generic name for the IaaS service, that manages network resources (e.g. Neutron in OpenStack).                                         |
| Storage            | A generic name for the IaaS service, that manages the storage backends and virtual devices (e.g. Cinder in OpenStack).                   |

## Motivation

Redundancy is a non-trivial but relevant issue for a cloud deployment.
The IaaS layer especially as the first virtualization from the hardware has an important role in this topic, because it is possible to provide failure safety through redundancy from failures on the physical layer.
The grouping of physical resources into Availability Zones on the IaaS level, gives customers the option to distribute their workload to different AZs which will result in a better failure safety.
While CSPs already have some similarities in their grouping of physical resources to AZs, there are also differences.
Availability Zones can be set up for Compute, Network and Storage while all refering to the same physical separation in a deployment.
This standard elaborates the necessity of having Availability Zones for each of these classes.
It will also check the requirement customers may have, when thinking about Availability Zones in regarding of the taxonomy of failure safety levels [^1].
The result should enable CSPs to know when to create AZs to be SCS-compliant.

## Design Considerations


    AZs should represent parts of the same deployment, that have an independency of each other
    AZs should be able to take workload from another AZ in a Failure Case of Level 3 (in other words: the destruction of one AZ will not automatically include destruction of the other AZs)

    Compute: resources are bound to one AZ, replication cannot be guaranteed, downtime or loss of resources is most likely
    Storage: highly depended on storage configuration, replication even over different AZs is part of some storage backends
    Network: network resources are also stored as configuration pattern in the DB and could be materialized in other parts of a deployment easily as long as the DB is still available.

    We should not require AZs to be present (== allow small deployments and edge use cases)


- Availability Zones are available for Compute, Storage and Network. They behave differently there

### Options considered

#### AZs in Compute



#### AZs in Storage



#### AZs in Network



### Open questions

RECOMMENDED

## Standard


    AZs should only occur within the same deployment and have an interconnection that represents that (we should not require specific numbers in bandwidth and latency.)
    We should separate between AZs for different resources (Compute, Storage, Network)

Compute needs AZs (because VMs may be single point of failure) if failure case 3 may occur (part of the deployment is destroyed, if the deployment is small there will be no failure case three, as the whole deployment will be destroyed)
Storage should either be replicated over different zones (e.g. fire zones) that are equivalent to compute AZs or also use AZs
Network do not need AZs

    Power supply may be confused with power line in. Maybe a PDU is what we should talk about - those need to exist for each AZ independently.
    When we define fire zone == compute AZ, then every AZ of course has to fulfill the guidelines for a single fire zone. Maybe this should be stated implicitly rather than explicitly.
    internet uplinks: after the destruction of one AZ, uplink to the internet must still be possible (that can be done without requiring a separate uplinks for each AZ.)
    each AZ should be designed with minimal single point of failures (e.g. single core router) to avoid a situation where a failure of class 2 will disable a whole AZ and so lead to a failure of class 3.


## Related Documents

The taxonomy of failsafe levels (TODO: link after DR is merged.)

## Conformance Tests

As this standard will not require Availability Zones to be present, we cannot automatically test the conformance.
The other parts of the standard are physical or internal and could only be tested through an audit.
Whether there are fire zones physically available is a criteria that will never change for a single deployment - this only needs to be audited once.
