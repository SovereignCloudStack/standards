---
title: Networking Standard
type: Standard
status: Proposal
track: IaaS
---

## Introduction

[...]

## Motivation

[...]

## Design Considerations

Networking setups can vary between OpenStack clouds in a number of aspects. The focus of this standard are those aspects that have an impact on the cloud user, which can be broadly grouped into two areas:
* API behavior, which includes policy rules and the availability of API extensions,
* and CSP-managed resources, which includes provider networks and their subnets, as well as floating IPs and subnet pools.

### Options considered

#### API Extensions

The OpenStack Networking API is more modular than many other OpenStack APIs, adding new functionality as optional API extensions, rather than a linear sequence of micro-versions. Which of those extensions are available from Neutron depends on the enabled plugins and back-end drivers.

Mandating a minimum set of enabled extensions will ensure that users have a consistent feature-set available across SCS clouds, but should not unnecessarily restrict the choice of back-end drivers for CSPs.

[...]

#### Policies

[...]

#### Provider Networks

Provider networks are CSP-managed networks that are made available to projects, such that project-internal resources can be connected to them. In Openstack, provider networks can be made available as _external_, as _shared_, or both:
* External networks provide the standard way of connecting project-internal resources to networks outside of the cloud environment, such as the internet. They can be connected to project-internal networks with a virtual router, but do not allow VMs to connect directly.
* Shared networks are typically used to connect resources of different projects within the same cloud environment. Unlike external networks, VMs can be directly attached to them.
* Shared external networks are a special case that allows external access, but also direct attachment of VMs.

Networks can be shared or external to either a specified subset of projects or to all projects (the latter is the default for external networks). For the purpose of standardization we primarily care about provider networks that are available to all projects.
Purely shared networks between all projects have very few use-cases in a public cloud. They are more of special case solution to connect a specific set of related projects, so they will not be further considered here.
External networks, on the other hand, are required to make VMs in a project externally accessible, which is an essential functionality, and as such should be mandatory in an SCS compliant cloud.

Connecting a VM to a non-shared external network does at minimum require the creation of a virtual router and a project-internal network and subnet.
Assigning public IPs to VMs in an internal network requires an internal subnet with public IP allocation ranges, that will usually be allocated from a CSP-managed subnet pool.
To allow users the dynamic allocation and deallocation of publicly routable subnets, CSPs need to provide [dynamic routing via BGP](https://docs.openstack.org/neutron/latest/admin/config-bgp-dynamic-routing.html).

Alternatively, at least for IPv4, virtual routers can also act as source NAT, allowing VMs in the internal network to access the internet through the routers external gateway IP.
To make VMs in a NATed subnet externally accessible, OpenStack also supports destination NAT in the form of Floating IPs.
A floating IP represents an address from the external network which can be allocated from a CSP-managed pool and mapped onto an IP within an internal network.

NAT and floating IPs do not require dynamic routing and can greatly reduce the number of required IPv4 addresses, which are an increasingly sparse resource and may be subject to tight project-quotas by the CSP.
Being ultimately a workaround for the limited IPv4 address space, neither are available for IPv6.
It is possible, however, to create a dual-stack setup in which VMs attached to a routed internal network can have both public IPv6 addresses and private, NATed IPv4 addresses.

[...]

A shared external network may provide some usability benefits over a purely external one, as users can make their VMs directly accessible from the internet without creating additional resources.
Beyond that, skipping virtual routers may be important for projects implementing some form of network function virtualisation (NFV) within a VM, but this is more of a niche application, that may also require disabling port security.

[...]

## Decision
### API Extensions

[...]

### Policies

[...]

### Provider Networks

CSPs **MUST** provide a standard external network that gives projects access to the internet.

The external network **MUST** have an IPv6 subnet.
CSPs **MUST** provide a subnet pool for the allocation of at least one public /64 IPv6 prefix per project.

The external network **SHOULD** have an IPv4 subnet.
If CSPs provide an IPv4 subnet, then CSPs **MUST** at least one public Floating IP per project.
They **SHOULD** also provide a subnet pool for the allocation of IPv4 prefixes to project networks.

CSPs **MUST** provide dynamic routing for all project-allocated IP-prefixes.

All subnets of external networks **MUST** be configured with `--no-dhcp`.
