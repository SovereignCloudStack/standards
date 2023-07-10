---
title: Requirements for the Container Network Interface (CNI)
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

What is a CNI?

It's independent of Kubernetes.

## Motivation

Users of SCS-based Kubernetes should have basic features.


## Design considerations

...


### Required and Desirable Features


#### Required Features


* Kubernetes Network Policies



#### Desirable Features

##### HostFirewall for Nodes

By default, Kubernetes Nodes should not be exposed to the public internet.

How the provider of the Kubernetes service implements this is not a part of this SCS standard.

Here are some of several ways to achieve this:

* Nodes don't have public IPs and are only reachable within a VPC (Virtual Private Cloud)
* The CNI implements a HostFirewall. For example, [Cilium HostFirewall (CiliumClusterwideNetworkPolicy)](https://docs.cilium.io/en/v1.13/security/host-firewall/)
* A firewall on the node (iptables/nftables)
* A firewall in front of the nodes.

### Rejected CNIs

As Flannel does not support Kubernetes Network Policies, we recommend against using Flannel.

### Conclusion

The SCS community has decided to leave the choice of a specific CNI up to the Kubernetes service provider.

At the current moment, Cilium seems to be a good choice if the service provider has not yet settled on a particular CNI.

