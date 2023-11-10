---
title: Kubernetes Node Distribution and Availability
type: Standard
status: Draft
track: KaaS
---

## Introduction

A Kubernetes instance is provided as a cluster, which consists of a set of machines,
so called nodes. A cluster is composed of a control plane and at least one worker node.
The control plane manages the worker nodes and therefore the pods in the cluster by making
decisions about scheduling, event detection and rights management. Inside the control plane,
multiple components exist, which can be duplicated and distributed over multiple nodes
inside the cluster. Typically, no user workloads are run on these nodes in order to
separate the controller component from user workloads, which could pose a security risk.

### Glossary

The following terms are used throughout this document:

| Term | Meaning |
|---|---|
| Worker | Virtual or bare-metal machine, which hosts workloads of customers |
| Control Plane | Virtual or bare-metal machine, which hosts the container orchestration layer that exposes the API and interfaces to define, deploy, and manage the lifecycle of containers. |
| Machine | Virtual or bare-metal entity with computational capabilities |

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
[Kubernetes Nodes Anti Affinity] as well as the Kubernetes documents about [High Availability]
and [Best practices for large clusters].

SCS wishes to prefer distributed, highly-available systems due to their obvious advantages
like fault-tolerance and data redundancy. But it also understands the costs and overhead
for the providers associated with this effort, since the infrastructure needs to have
hardware which will just be used to provide fail-over safety or duplication.

The document [Best practices for large clusters] describes the concept of a failure zone.
This term isn't defined any further, but can in this context be described as a number of
physical (computing) machines in such a vicinity to each other (either through physical
or logical interconnection in some way), that specific problems inside this zone would put
all these machines at risk of failure/shutdown. It is therefore necessary for important
data or services to not be present just on one failure zone.
How such a failure zone should be defined is dependent on the risk model of the service/data
and its owner as well as the capabilities of the provider. Zones could be set from things
like single machines or racks up to whole datacenters or even regions, which could be
coupled by things like electrical grids. They're therefore purely logical entities, which
shouldn't be defined further in this document.

## Decision

This standard formulates the requirement for the distribution of Kubernetes nodes in order
to provide a fault-tolerant and available Kubernetes cluster infrastructure.
Since some providers only have small environments to work with and therefore couldn't
comply with this standard, it will be treated as a RECOMMENDED standard, where providers
can OPT-OUT.

If the standard is used by a provider, the following decisions are binding and valid:

- The control plane nodes MUST be distributed over multiple physical machines. Kubernetes
  provides best-practices on this topic, which are also RECOMMENDED by SCS.
- At least one control plane instance MUST be run in each "failure zone", more are
  RECOMMENDED in each "failure zone" to provide fault-tolerance for each zone.

- Worker nodes are RECOMMENDED to be distributed over multiple zones. This policy makes
  it OPTIONAL to provide a worker node in each "failure zone", meaning that worker nodes
  can also be scaled vertically first before scaling horizontally.
- Worker node distribution MUST be indicated to the user through some kind of labeling
  in order to enable (anti)-affinity for workloads over "failure zones".

## Related Documents

[High Availability](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
[Best practices for large clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/)
[Kubernetes Nodes Anti Affinity](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0213-v1-k8s-nodes-anti-affinity.md)

## Conformance Tests

Conformance Tests will be written in another issue
