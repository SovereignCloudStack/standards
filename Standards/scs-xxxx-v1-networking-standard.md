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

(discuss required API extensions?)

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
In Neutron, besides enabling security groups for ports in this network, it also enables a number of built-in spoofing protections.

Whether this flag is set is primarily of concern for shared provider networks, as users only have limited control over the gateway ports of virtual routers.
A lack of spoofing protection in a shared network, however, does enable a number of attacks that a malicious user or compromised VM could perform against other VMs in the network, such as DHCP-spoofing or ARP-Poisoning.

There are legitimate use-cases for networks without port security, such as the implementation of network function virtualisation (NFV) within a VM.
However, this seems to be more of a niche use-case and may warrant the creation of a project-specific provider network, rather than making all other projects vulnerable to spoofing attacks.

### Options considered

#### IPv6

The OpenStack Network API allows the creation of subnets with either IPv4 or IPv6 address ranges, as indicated by the `ip_version` field.
However, to allow external access to either, the CSP needs to provide projects with externally routable addresses for that IP version.

While it is possible (and common) for CSPs to provide both IPv4 and IPv6, the increasing scarcity (and cost) of IPv4 address space may at some point become a barrier to entry for new CSPs.
Mandatory support for IPv6 but not IPv4 addresses this problem while providing users with a consistent feature set across SCS clouds.

#### Single Default Provider Network

In principle, CSPs can create multiple provider networks for a number of reasons, for example to make cloud-internal shared services available to projects.
VMs can be connected to multiple networks, and connecting to additional provider networks would not interfere with their ability be externally accessible.

CSPs may also create multiple provider networks with different options for external access, such as separate networks for IPv4 and IPv6, or one external network for use with virtual routers and a separate shared network for direct connection.
This mostly just adds complexity to the setup, though, as a provider network can be both external and shared at the same time, and can even provide both IPv4 and IPv6 subnets in a dual stack setup [^ds].

Another problem with multiple provider networks is that user may only be able to distinguish their respective function by their name.
A single default provider network leaves no ambiguity by the user in this regard and is thus preferable from a standardisation perspective.

#### Shared Provider Network

A shared provider network has the benefit of being easy to 
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

#### RBAC for Users

* disallow creation of rbac rules for users to prevent creation of faux provider networks

## Decision

CSPs **MUST** provide a standard provider network to every project to access to the internet.
There **SHOULD** be no other provider networks available to projects by default.

The standard provider network **MUST** be an external network, allowing it to be used as external gateway by virtual routers.
The standard provider network **MAY** be a shared network, allowing direct attachment of VMs.
If the standard provider network is a shared network, it **MUST** enable port security.

The external network **MUST** have an IPv6 subnet.
CSPs **MUST** provide a subnet pool for the allocation of at least one public /64 IPv6 prefix per project.

The external network **SHOULD** have an IPv4 subnet.
If CSPs provide an IPv4 subnet, then CSPs **MUST** provide at least one public Floating IP per project.
They **MAY** also provide a subnet pool for the allocation of public IPv4 prefixes to project networks.

CSPs **MUST** provide dynamic routing for all project-allocated public IP-prefixes.

Users **SHOULD** by default be prohibited by policy from creating RBAC rules for networks in their projects, to prevent the creation of faux provider networks.

## References

[^bgp]: https://docs.openstack.org/neutron/latest/admin/config-bgp-dynamic-routing.html
[^pd]: https://docs.openstack.org/neutron/latest/admin/config-ipv6.html#prefix-delegation
[^pf]: https://docs.openstack.org/api-ref/network/v2/index.html#floating-ips-port-forwarding
