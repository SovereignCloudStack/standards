---
title: "Kubernetes Node Distribution and Availability: Implementation and Testing Notes"
type: Supplement
track: KaaS
status: Draft
supplements:
  - scs-0214-v1-k8s-node-distribution.md
  - scs-0214-v2-k8s-node-distribution.md
---

## Implementation notes

A Kubernetes clusters control plane must be distributed over multiple physical machines, as well
as different "failure zones". How these are defined is at the moment up to the CSP.
Worker nodes can also be distributed over "failure zones", but this isn't a requirement.
Distribution must be shown through labelling, so that users can access these information.

Node distribution metadata is provided through the usage of the labels
`topology.kubernetes.io/region` and `topology.kubernetes.io/zone`.

## Automated tests

### Notes

The test for the [SCS K8s Node Distribution and Availability](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0214-v2-k8s-node-distribution.md)
checks if control-plane nodes are distributed over different failure zones (distributed into
physical machines, zones and regions) by observing their labels defined by the standard.

### Implementation

The script [`k8s_node_distribution_check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-node-distribution/k8s_node_distribution_check.py)
connects to an existing K8s cluster and checks if a distribution can be detected with the labels
set for the nodes of this cluster.

## Manual tests

None.
