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

In order to achieve compliance, the `topology.scs.community/host-id` tag has to be set manually for now. It should be done after the cluster deployment, when all nodes are ready and IDs of host machines are accessible by the user. The nodes can be labeled using the following command:

```
kubectl label nodes <node-name> "topology.scs.community/host-id"=<hostID>
```

The steps necessary to get hostID of a virtual or baremetal machine running a node can be different for each CSP. For example, using `openstack`, we can list machine names (which should correspond to node names) with their respective hostIDs using the following command:

```
openstack server list -f json | jq -r '.[].ID' | while read id; do openstack server show $id -f json; done | jq '{ (.name): .hostId }'
```

## Automated tests

Currently, automated testing is not readily possible because we cannot access information about
the underlying host of a node (as opposed to its region and zone). Therefore, the test will only output
a tentative result.

The current implementation can be found in the script [`k8s_node_distribution_check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-node-distribution/k8s_node_distribution_check.py).

## Manual tests

None.
