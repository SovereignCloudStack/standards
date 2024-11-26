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

Currently, automated testing is not readily possible because we cannot access information about
the underlying host of a node (as opposed to its region and zone). Therefore, the test will only output
a tentative result.

The current implementation can be found in the script [`k8s_node_distribution_check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-node-distribution/k8s_node_distribution_check.py).

## Manual tests

None.
