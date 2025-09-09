---
title: "KaaS Networking Standard: Implementation Notes"
type: Supplement
track: KaaS
supplements:
  - scs-0219-v1-kaas-networking.md
---
## List of compliant CNI Plugins

The Kubernetes Network Policy API working group maintains a [list of work-in-progress implementations](https://network-policy-api.sigs.k8s.io/implementations/) of the AdminNetworkPolicy and BaselineAdminNetworkPolicy resources.
Besides their own proof-of-concept implementation of [kube-network-policies](https://github.com/kubernetes-sigs/kube-network-policies), at the time of writing they list the following CNI plugins:

- [OVN-Kubernetes](https://github.com/ovn-org/ovn-kubernetes/)
- [Antrea](https://github.com/antrea-io/antrea/)
- [KubeOVN](https://github.com/kubeovn/kube-ovn)
- [Calico](https://github.com/projectcalico/calico)
- [Cilium](https://github.com/cilium/cilium)

All of these plugins also implement the basic NetworkPolicy API, and are therefore compliant both with the standard's requirements and recommendations.

The CNI plugin [Flannel](https://github.com/flannel-io/flannel) does not support network policies by itself, but can be combined with Calico for policy enforcement.
This configuration is known as [Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/install-for-flannel) and will likely profit from Calico's support for AdminNetworkPolicy.

There are more CNI plugins that support the NetworkPolicy API, but are not known to work on support of the AdminNetworkPolicy extensions.
As such they are still compliant with the current version of the Standard.
However, these seem to be either vendor-specific, like the [Azure CNI](https://learn.microsoft.com/de-de/azure/aks/configure-azure-cni), or unmaintained, like [Weave](https://github.com/weaveworks/weave).
