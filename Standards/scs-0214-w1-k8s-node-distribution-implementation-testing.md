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
`topology.kubernetes.io/region`, `topology.kubernetes.io/zone` and
`topology.scs.community/host-id` respectively.

At the moment, not all labels are set automatically by most K8s cluster utilities, which incurs
additional setup and maintenance costs.

In order to achieve compliance, the `topology.scs.community/host-id` tag has to be set manually for now. It should be done after the cluster deployment, when all nodes are ready and IDs of host machines are accessible by the user. The nodes can be labeled using the following command:

```
kubectl label nodes <node-name> "topology.scs.community/host-id"=<hostID>
```

The steps necessary to get hostID of a virtual or baremetal machine running a node can be different for each CSP, but using `openstack` as an example:

```
openstack server list -f json | jq -r '.[].ID'
```

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
