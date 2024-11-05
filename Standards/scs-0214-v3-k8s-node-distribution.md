---
title: Kubernetes Node Distribution and Availability
type: Standard
status: Draft
replaces: scs-0214-v1-k8s-node-distribution.md and scs-0214-v1-k8s-node-distribution.md
track: KaaS
---

## Introduction

A Kubernetes instance is provided as a cluster, which consists of a set of machines,
so-called nodes. A cluster is composed of a control plane and at least one worker node.
The control plane manages the worker nodes and therefore the pods in the cluster by making
decisions about scheduling, event detection and rights management. Inside the control plane,
multiple components exist, which can be duplicated and distributed over multiple nodes
inside the cluster. Typically, no user workloads are run on these nodes in order to
separate the controller component from user workloads, which could pose a security risk.

The Kubernetes project maintains multiple release versions, with the three most recent minor
versions actively supported, along with a fourth version in development.
Each new minor version replaces the oldest version at the end of its support period,
which typically spans approximately 14 months, comprising a 12-month standard support period
followed by a 2-month end-of-life (EOL) phase for critical updates.

### Glossary

The following terms are used throughout this document:

| Term          | Meaning                                                                                                                                                                     |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Worker        | Virtual or bare-metal machine, which hosts workloads of customers                                                                                                           |
| Control Plane | Virtual or bare-metal machine, which hosts the container orchestration layer that exposes the API and interfaces to define, deploy, and manage the lifecycle of containers. |
| Machine       | Virtual or bare-metal entity with computational capabilities                                                                                                                |
| Failure Zone  | A logical entity representing a group of physical machines that share a risk of failure due to their proximity or dependency on common resources.                           |

## Motivation

In normal day-to-day operation, it is not unusual for some operational failures, either
due to wear and tear of hardware, software misconfigurations, external problems or
user errors. Whichever was the source of such an outage, it always means down-time for
operations and users and possible even data loss.
Therefore, a Kubernetes cluster in a productive environment should be distributed over
multiple "failure zones" in order to provide fault-tolerance and high availability.
This is especially important for the control plane of the cluster, since it contains the
state of the whole cluster. A failure of this component could mean an unrecoverable failure
of the whole cluster.

## Design Considerations

Most design considerations of this standard follow the previously written Decision Record
[Kubernetes Nodes Anti Affinity][scs-0213-v1] as well as the Kubernetes documents on
[High Availability][k8s-ha] and [Best practices for large clusters][k8s-large-clusters].

The SCS prefers distributed, highly available systems due to advantages such as fault tolerance and 
data redundancy. It also acknowledges the costs and overhead for providers associated with this effort,
given that hardware and infrastructure may be dedicated to fail-over safety and duplication.

The [Best practices for large clusters][k8s-large-clusters] documentation describes the concept
of a failure zone. This term is context-dependent and describes a group of physical machines that are close
enough—physically or logically—that a specific issue could affect all machines in the zone.
To mitigate this, critical data and services should not be confined to one failure zone.
How a failure zone is defined depends on the risk model and infrastructure capabilities of the provider,
ranging from single machines or racks to entire datacenters or regions. Failure zones are therefore logical
entities that should not be strictly defined in this document.


## Decision

This standard formulates the requirements for the distribution of Kubernetes nodes to provide a fault-tolerant
and available Kubernetes cluster infrastructure. Since some providers only have small environments to work
with and therefore couldn't comply with this standard, it will be treated as a RECOMMENDED standard,
where providers can OPT OUT.

### Control Plane Requirements

1. **Distribution Across Physical Machines**: Control plane nodes MUST be distributed over multiple physical
    machines to avoid single points of failure, aligning with Kubernetes best practices.
2. **Failure Zone Placement**: At least one control plane instance MUST be run in each defined failure zone.
    More instances in each failure zone are RECOMMENDED to enhance fault tolerance within each zone.

### Worker Node Requirements

- The control plane nodes MUST be distributed over multiple physical machines. Kubernetes
  provides best-practices on this topic, which are also RECOMMENDED by SCS.
- At least one control plane instance MUST be run in each "failure zone", more are
  RECOMMENDED in each "failure zone" to provide fault-tolerance for each zone.
- Worker nodes are RECOMMENDED to be distributed over multiple zones. This policy makes
  it OPTIONAL to provide a worker node in each "failure zone", meaning that worker nodes
  can also be scaled vertically first before scaling horizontally.
- Worker node distribution MUST be indicated to the user through some kind of labeling
  in order to enable (anti)-affinity for workloads over "failure zones".
- To provide metadata about the node distribution, which also enables testing of this standard,
  providers MUST label their K8s nodes with the labels listed below.


To provide metadata about node distribution and enable efficient workload scheduling and testing of this standard,
providers MUST label their Kubernetes nodes with the following labels. These labels MUST remain current with the
deployment’s state.

- `topology.kubernetes.io/zone`
  - Corresponds with the label described in [K8s labels documentation][k8s-labels-docs].
    This label provides a logical failure zone identifier on the provider side, 
    such as a server rack in the same electrical circuit. It is typically autopopulated by either
    the kubelet or external mechanisms like the cloud controller.

- `topology.kubernetes.io/region`
  - This label groups multiple failure zones into a region, such as a building with multiple racks.
    It is typically autopopulated by the kubelet or a cloud controller.

- `topology.scs.community/host-id`
  - This SCS-specific label MUST contain the unique hostID of the physical machine running the hypervisor,
    helping identify the physical machine’s distribution. 

## Conformance Tests

The `k8s-node-distribution-check.py` script assesses node distribution using a user-provided kubeconfig file.
It verifies compliance based on the `topology.scs.community/host-id`, `topology.kubernetes.io/zone`,
`topology.kubernetes.io/region`, and `node-role.kubernetes.io/control-plane` labels.
The script produces errors if node distribution does not meet the standard’s requirements and generates
warnings if labels appear incomplete.

## Previous Standard Versions

This version extends [version 1](scs-0214-v1-k8s-node-distribution.md) by enhancing node labeling requirements.

[k8s-ha]: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/
[k8s-large-clusters]: https://kubernetes.io/docs/setup/best-practices/cluster-large/
[scs-0213-v1]: https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0213-v1-k8s-nodes-anti-affinity.md
[k8s-labels-docs]: https://kubernetes.io/docs/reference/labels-annotations-taints/#topologykubernetesiozone

