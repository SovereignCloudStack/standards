---
title: Provider Networks
type: Standard
status: Proposal
track: IaaS
---

## Introduction

Connecting a virtual machine to the internet requires a virtual networks that is also connected to the non-virtualised network infrastructure outside of the cloud environment.
Because such networks break the isolation of the cloud environment, they must be created and managed by the CSP and made available to projects only in a controlled manner.

In OpenStack, such CSP-managed networks are called _provider networks_, though not all provider networks have to provide access to the Internet.
And those who do may impose different restrictions and use different methods of allocating IP addresses.

External access to and from virtualised resources is a fundamental property of IaaS, and providing this access is a hard requirement for any cloud provider.
This document outlines a standardized setup of provider networks to ensure a consistent, secure, and efficient methodology for managing public IP addresses and providing external access in SCS clouds.

## Motivation

The ability to interface virtualised resources with networks outside of the cloud environment, such as the internet, is an integral part of IaaS.
Providing external access in an OpenStack cloud requires a number of configuration choices from the CSP, some of which have direct implications on how users interact with the cloud.
This standard identifies some of these options and defines a baseline setup that provides flexibility and consistency to users but is also realistic to implement for CSPs.

## Design Considerations

### Provider Network Access Control

In OpenStack, ownership of resources is generally tracked through projects, and, as per default policy, only members of a project have access to its resources
This is also true for CSP-managed resources, such as provider networks, which have to be created in a designated internal projec, and are initially only accessible in this project.

The Network API's Role Based Access Control (RBAC) extension can then be used to share it with other projects.
RBAC rules for networks support the two actions `access_as_external` and `access_as_shared`, and can be created automatically on `openstack network create` with the options `--external` and `--share`.
* `access_as_external` allows networks to be used as external gateway for virtual routers in the target projects. Such networks are in the following referred to as _external networks_.
* `access_as_shared` allows networks to be attached directly to VMs in the target projects. Such networks are in the following referred to as _shared networks_.

The rules can be created with either a specific target project ID, or with a wild card (`*`) to target all projects.
They can also overlap, allowing a network to be both external and shared to the same target projects.

### Address Allocation and Routing

CSPs can assign a subnet to a provider network to supply connected VMs or virtual routers with public IP addresses, making them externally accessible.
This works well for shared networks where VMs can be attached directly, although there is no quota option to limit the number of allocated addresses per project.

Making VMs in a project-internal network externally accessible through a virtual router is a bit more complicated, though.
One option is for the user to create a subnet with a public IP range for the internal network, and then ask the CSP to configure a static route to the subnet via the gateway IP of a virtual router.
This is cumbersome to set up manually, but can be automated with the `bgp` extension of the Network API, which is implemented by the `neutron-dynamic-routing` project [^bgp].
For users, this takes the form of a CSP-managed shared subnet pool that they can create externally routable subnets from, limited by a per-project quota.

For IPv6, there is also the option of prefix delegation, where a DHCPv6 server automatically assigns an IPv6 prefix to a subnet whenever it is connected to the external provider network [^pd].
This also means that ports in the subnet can lose their addresses and get new ones if the subnet is removed from the external network and later reattached.
With prefix delegation there is no quota on the number of prefixes per project.

For IPv4, OpenStack virtual routers support source NAT, allowing all VMs in the internal subnet to access the external network with the gateway IP of the virtual router.
They also support destination NAT in the form of floating IPs, addresses from the external network that can be mapped onto specific VMs in the internal subnet to make them externally accessible.
Floating IPs are allocated from a CSP-managed pool, and can be controlled by a per-project quota.
There is also a set of API extensions that allow more fine grained port-forwarding, mapping different TCP or UDP ports of a floating IP to different internal IP addresses [^pf].

### Port Security and Spoofing

OpenStack networks have the flag `port_security_enabled`, that is set to true by default and can only be changed by it's owner.
In Neutron, besides enabling security groups for ports in this network, it also enables a set of built-in spoofing protections.

Whether this flag is set is primarily of concern for shared provider networks, as users only have limited control over the gateway ports of virtual routers.
A lack of spoofing protection in a shared network, however, does enable a number of attacks that a malicious user or compromised VM could perform against other VMs in the network, such as DHCP-spoofing or ARP-Poisoning.

There are legitimate use-cases for networks without port security, such as the implementations of network function virtualisation (NFV) within a VM.
However, this seems to be more of a niche use-case and may warrant the creation of a project-specific provider network, rather than making all other projects vulnerable to spoofing attacks.

### Options considered

#### Single Default Provider Network

* multiple provider networks may confusing, user has to figure out the "right" one
* dual stack possible with multiple subnets in a single networks

#### Shared Provider Network

* simplicity of use, no extra resources
* port security is essential
* no quota for address use

#### External Provider Network

* requires virtual router
* requires dynamic routing
* IPv4+IPv6
* prefer over shared network because: FWaaS, Quota

#### NAT and Floating IPs

* requires virtual router
* IPv4 only
* dual stack use with IPv6 from subnetpool
* IPv4: prefer NAT/FIP over subnet pool to discourage wasting addresses

#### Dual Stack

#### Security Considerations

* disallow creation of rbac rules for users to prevent creation of faux provider networks
* require port security in shared provider networks

## Decision

CSPs **MUST** provide a standard external network that gives projects access to the internet.

The external network **MUST** have an IPv6 subnet.
CSPs **MUST** provide a subnet pool for the allocation of at least one public /64 IPv6 prefix per project.

The external network **SHOULD** have an IPv4 subnet.
If CSPs provide an IPv4 subnet, then CSPs **MUST** at least one public Floating IP per project.
They **SHOULD** also provide a subnet pool for the allocation of IPv4 prefixes to project networks.

CSPs **MUST** provide dynamic routing for all project-allocated IP-prefixes.

## References

[^bgp]: https://docs.openstack.org/neutron/latest/admin/config-bgp-dynamic-routing.html
[^pd]: https://docs.openstack.org/neutron/latest/admin/config-ipv6.html#prefix-delegation
[^pf]: https://docs.openstack.org/api-ref/network/v2/index.html#floating-ips-port-forwarding
