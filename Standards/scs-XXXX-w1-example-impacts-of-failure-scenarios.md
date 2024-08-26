---
title: "SCS Taxonomy of Failsafe Levels: Examples of Failure Cases and their impact on IaaS and KaaS resources"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-XXXX-vN-taxonomy-of-failsafe-levels.md
---

# Examples of the impact from certain failure scenarios on Cloud Resources

Failure cases in Cloud deployments can be hardware related, environmental, due to software errors or human interference.
The following table summerizes different failure scenarios, that can occur:

| Failure Scenario | Probability | Consequences | Failsafe Level Coverage |
|----|-----|----|----|
| Disk Failure | High | Permanent data loss in this disk. Impact depends on type of lost data (data base, user data) | L1 |
| Host Failure (without disks) | Medium to High | Permanent loss of functionality and connectivity of host (impact depends on type of host) | L1 |
| Host Failure | Medium to High | Data loss in RAM and temporary loss of functionality and connectivity of host (impact depends on type of host) | L1 |
| Rack Outage | Medium | Outage of all nodes in rack | L2 |
| Network router/switch outage | Medium | Temporary loss of service, loss of connectivity, network partitioning | L2 |
| Loss of network uplink | Medium | Temporary loss of service, loss of connectivity | L3 |
| Power Outage (Data Center supply) | Medium | Temporary outage of all nodes in all racks | L3 |
| Fire | Medium | permanent Disk and Host loss in the affected zone | L3 |
| Flood | Low | permanent Disk and Host loss in the affected region | L4 |
| Earthquake | Very Low | permanent Disk and Host loss in the affected region | L4 |
| Storm/Tornado | Low | permanent Disk and Host loss in the affected region | L4 |
| Software bug (major) | Low | permanent loss or compromise of data that trigger the bug up to data on the whole physical machine | L3 |
| Software bug (minor) | High | temporary or partial loss or compromise of data | L1 |
| Minor operating error | High | Temporary outage | L1 |
| Major operating error | Low | Permanent loss of data | L3 |
| Cyber attack (minor) | High | permanent loss or compromise of data on affected Disk and Host | L1 |
| Cyber attack (major) | Medium | permanent loss or compromise of data on affected Disk and Host | L3 |

Those failure scenarios can result in either only temporary (T) or permanent (P) loss of IaaS / KaaS resources or data.
Additionally, there are a lot of resources in IaaS alone that are more or less affected by these failure scenarios.
The following tables shows the impact **when no redundancy or failure safety measure is in place**, i.e., when
**not even failsafe level 1 is fulfilled**.

## Impact on IaaS Resources (IaaS Layer)

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | Natural Catastrophy | Cyber Threat | Software Bug |
|----|----|----|----|----|----|----|----|
| Image | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | P |
| Volume | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | P |
| User Data on RAM /CPU | | P | P | P | P | T/P | P |
| volume-based VM | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | P |
| ephemeral-based VM | P[^1] | P | P | T | P (T[^4]) | T/P | P |
| Ironic-based VM | P[^2] | P | P | T | P (T[^4]) | T/P | P |
| Secret | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | P |
| network configuration (DB objects) | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | P |
| network connectivity (materialization) | | T[^3] | T/P | T | P (T[^4]) | T/P | T |
| floating IP | P[^1] | T[^3] | T/P | T | P (T[^4]) | T/P | T |

For some cases, this only results in temporary unavailability and cloud infrastructures usually have certain mechanisms in place to avoid data loss, like redundancy in storage backends and databases.
So some of these outages are easier to mitigate than others.

[^1]: If the resource is located on that specific disk.
[^2]: Everything located on that specific disk. If more than one disk is used, some data could be recovered.
[^3]: If the resource is located on that specific node.
[^4]: In case of disks, nodes or racks are not destroyed, some data could be safed. E.g. when a fire just destroyes the power line.

## Impact on Kubernetes Resources (KaaS layer)

:::note

In case the KaaS layer runs on top of IaaS layer, the impacts described in the above table apply for the KaaS layer as well.

:::

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | Natural Catastrophy | Cyber Threat | Software Bug |
|----|----|----|----|----|----|----|----|
|Node|P| | | | | |T/P|
|Kubelet|T| | | | | |T/P|
|Pod|T| | | | | |T/P|
|PVC|P| | | | | |P|
|API Server|T| | | | | |T/P|
