---
title: Kubernetes High Availability (HA)
type: Standard
status: Draft
track: KaaS
---

## Introduction 

High availability (HA) is a critical design principle in Kubernetes clusters to ensure operational continuity and 
minimize downtime during failures. The control plane is the central component of a Kubernetes cluster, managing the state
and operations of the entire system. Ensuring HA involves distributing the control plane across multiple physical or
logical failure zones to reduce risks from localized failures.

## Glossary

| Term          | Meaning                                                                                                                                                                     |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| Control Plane | Virtual or bare-metal machine, which hosts the container orchestration layer that exposes the API and interfaces to define, deploy, and manage the lifecycle of containers. |
| Failure Zone  | A logical grouping of machines with shared dependencies, such as network infrastructure, power supply, or physical proximity, that may fail as a unit.                      |

## Motivation 

High availability (HA) is essential for ensuring the reliable operation of Kubernetes clusters, especially in production
environments where downtime can lead to significant operational and financial impacts.

Failures in single hosts are far more common than the outage of an entire room, zone, or availability zone (AZ).
Hosts can fail due to a variety of reasons, including:
* Hardware Failures: Broken RAM, PSU (power supply unit), or network ports.
* Operational Issues: Regular maintenance activities, such as hypervisor or firmware upgrades.

Distributing the control plane across multiple failure zones provides fault tolerance by ensuring that the cluster can
continue functioning even if one or more zones become unavailable. This setup enhances resilience by allowing the system
to recover from failures with minimal disruption. For example, in the event of a hardware failure, a network outage,
or a power disruption in one zone, the other zones can seamlessly take over control plane responsibilities.

Moreover, HA setups improve data consistency and cluster stability by ensuring quorum for distributed systems like etcd.
This prevents scenarios where the cluster state becomes inaccessible or inconsistent due to partial outages. By adhering
to HA principles, organizations can achieve greater uptime, maintain service-level agreements (SLAs), and ensure a
seamless user experience even in the face of unexpected disruptions.

## Decision

Control plane nodes MUST be distributed across at least three distinct physical hosts. This setup ensures resilience to
individual host-level failures caused by issues such as broken RAM, power supply unit (PSU) failures, network interface
card (NIC) malfunctions, or planned maintenance operations like firmware updates or hypervisor upgrades.
These events occur significantly more often in data centers than the complete failure of a room, rack, or
availability zone (AZ). As such, prioritizing distribution across physical hosts provides a practical and robust
baseline for HA, even in environments where multi-AZ configurations are not feasible.