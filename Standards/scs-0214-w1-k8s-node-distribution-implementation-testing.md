---
title: "Kubernetes Node Distribution and Availability: Implementation and Testing Notes"
type: Supplement
track: KaaS
status: Proposal
supplements:
  - scs-0214-v1-k8s-node-distribution.md
  - scs-0214-v2-k8s-node-distribution.md
---

## Introduction

The standard [SCS K8s Node Distribution and Availability](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0214-v2-k8s-node-distribution.md)
tries to define requirements for the distribution of Kubernetes nodes in order to provide
a fault-tolerant and (highly) available Kubernetes cluster.

## Implementation notes

A Kubernetes clusters control plane must be distributed over multiple physical machines, as well
as different "failure zones". How these are defined is at the moment up to the CSP.
Worker nodes can also be distributed over "failure zones", but this isn't a requirement.
Distribution must be shown through labelling, so that users can access these information.

Node distribution metadata is provided through the usage of the labels
`topology.kubernetes.io/region`, `topology.kubernetes.io/zone` and
`topology.scs.community/host-id` respectively.

At the moment, not all labels are set automatically by most K8s cluster utilities, which incurs
additional setup and maintenance costs.

## Automated tests

### Notes

The test for the [SCS K8s Node Distribution and Availability](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0214-v2-k8s-node-distribution.md)
checks if control-plane nodes are distributed over different failure zones (distributed into
physical machines, zones and regions) by observing their labels defined by the standard.

### Errors and warnings

The test will return 0 precisely when it could be verified that the standard is satisfied.
If no distribution can be detected, a 2 will be returned instead.
The test mentions if labels are missing, which would hinder the ability to detect node distribution,
if no distribution is available on specific levels or if not enough nodes are available for
a distribution to be feasible.

### Implementation

The script [`k8s_node_distribution_check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-node-distribution/k8s_node_distribution_check.py)
connects to an existing K8s cluster and checks if a distribution can be detected with the labels
set for the nodes of this cluster.

## Manual tests

None.
