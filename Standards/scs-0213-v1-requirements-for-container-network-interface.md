---
title: Requirements for container network interface (CNI)
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

What is a CNI?

Indipendent from Kubernetes.

## Motivation

Users of SCS based Kubernetes should have basic features.


## Design considerations

...


### Required and desirable features



#### Required features


* Kubernetes Network Policies



#### Desirable features

##### HostFirewall for Nodes

Kubernetes Nodes should not be exposed to the public internet by default.

How the provider of the Kubernetes service implements this is not part
of this SCS standard.

Here are some of several ways to achieve this:

* Nodes don't have public IPs and are only reachable within a VPC (Virtual Private Cloud)
* The CNI implements a HostFirewall. For example [Cilium HostFirewall (CiliumClusterwideNetworkPolicy)](https://docs.cilium.io/en/v1.13/security/host-firewall/)
* A firewall on the node (iptables/nftables)
* A firewall in front of the nodes.

### Rejected CNIs

Since Flannel does not support Kubernetes Network Policies, we recommend against using Flannel.

### Conclusion

The SCS community decided to leave it up to the Kubernetes service provider which particular CNI to choose.

At the current moment Cilium seems to be a good choice, if the service provider has not settled on
a particular CNI yet.

## Decision

Based on the research and conclusion above we've decided to use the **Harbor** project
as a container registry implementation for the SCS ecosystem.
