---
title: SCS Provider Network Standard
type: Standard
status: Proposal
track: IaaS
---

## Introduction

Connecting a virtual machine to the internet requires a virtual network that is also connected to the non-virtualised network infrastructure outside of the cloud environment.
Because such networks break the isolation of the cloud environment, they must be created and managed by the CSP and made available to projects only in a controlled manner.

In OpenStack, such CSP-managed networks are called _provider networks_, though providing access to the internet is not their only use case.
Depending on the configuration, they may impose different usage restrictions and offer different methods of allocating IP addresses.

External access to and from virtualised resources is a fundamental feature of IaaS, and providing this access is a hard requirement for any cloud provider.
However, OpenStack provider networks offer some design space regarding usage restrictions and IP address allocation.
This document defines a standardized setup for provider networks that offers external access in a way that is portable across SCS clouds.

### Glossary

The following terms are used throughout this document:

| Term | Meaning |
|------|---------|
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure. |
| Server | Server object in the OpenStack Compute API, usually represents a virtual machine, though there are also compute drivers for containers and bare metal servers. |
| Virtual Network | A virtualized network managed by OpenStack, provides connectivity between servers and other network resources, such as virtual routers. |
| Virtual Router | OpenStack resource that can be used to route and bridge between virtual networks and provide other features such as NAT |
| Subnet | Subdivision of available IP address space using address prefixes. In OpenStack also an abstraction for controlling IP address allocation in a virtual network. |
| DHCP | Dynamic Host Configuration Protocol: Used to automatically configure hosts in a network with IP addresses, default routes, and other information such as DNS servers. |
| Prefix | IP address prefix of a given bit-length N, written _/N_. Divides addresses into a network and a host part, a shorter prefix allows more hosts but takes up more address space. |
| NAT | Network Address Translation: mapping (usually public) IPv4 addresses onto a different (usually private) address space. May allows multiple hosts to share a public address by multiplexing TCP/UDP ports. |
| RBAC | Role-based Access Control: A mechanism in the Network API to give projects limited access to resources owned by other projects. Typically used by CSPs to create provider networks. |
| Shared Network | Virtual network that is shared between projects in a way that allows direct attachment of servers. |
| External Network | Virtual network that is shared between projects in a way that only allows virtual routers to use it as external gateway. Typically used by CSPs to provide access to networks outside of the cloud environment. |
| Provider Network | A CSP-managed virtual network made available to projects as either shared or external, typically connected to non-virtualized infrastructure. |

## Motivation

The ability to interface virtualised resources with networks outside of the cloud environment, such as the internet, is an integral part of IaaS.
Providing external access in an OpenStack cloud requires a number of configuration choices from the CSP, some of which have direct implications on how users interact with the cloud.
This standard identifies some of these options and defines a baseline setup that provides flexibility and consistency to users but is also realistic to implement for CSPs.

## Design Considerations

This section will provide some general background on OpenStack provider networks before considering specific options to standardize. 

### Provider Network Access Control

In OpenStack, ownership of resources is generally tracked through projects, and, as per default policy, only members of a project have access to its resources
This is also true for CSP-managed resources, such as provider networks, which have to be created in a CSP-internal project, and are initially only accessible in this project.

The Network API's Role Based Access Control (RBAC) extension can then be used to share it with other projects.
RBAC rules for networks support the two actions `access_as_external` and `access_as_shared`, and can be created automatically on `openstack network create` with the options `--external` and `--share`.
* `access_as_external` allows networks to be used as external gateway for virtual routers in the target projects. Such networks are in the following referred to as _external networks_.
  External networks have some special properties, such as allowing the creation of floating IPs, which will be discussed in the next section.
* `access_as_shared` allows networks to be attached directly to servers in the target projects. Such networks are in the following referred to as _shared networks_.

The rules can be created with either a specific target project ID, or with a wild card (`*`) to target all projects.
They can also overlap, allowing a network to be both external and shared to the same target projects.

### Address Allocation and Routing

CSPs can assign a subnet to a provider network to supply connected servers or virtual routers with public IP addresses, making them externally accessible.
This works well for shared networks, where servers can be attached directly, although there is no quota option to limit the number of allocated addresses per project.

Making servers in a project-internal network externally accessible through a virtual router is a bit more complicated, though.
One option is for the user to create a subnet with a public IP range for the internal network, and then ask the CSP to configure a static route to the subnet via the gateway IP of a virtual router.
This is cumbersome to set up manually, but can be automated with the `bgp` extension of the Network API, which is implemented by the `neutron-dynamic-routing` project [^bgp].
For users, this takes the form of a CSP-managed shared subnet pool that they can create externally routable subnets from, limited by a per-project quota.

For IPv6, there is also the option of prefix delegation, where a DHCPv6 server automatically assigns an IPv6 prefix to a subnet when it connects to the external provider network [^pd].
However, this also means that ports in the subnet can lose their addresses and get assigned new ones if the subnet is removed from the external network and later reattached.
The documentation at [^pd] still marks prefix delegation as an experimental feature in Neutron and notes low test coverage.

For IPv4, OpenStack virtual routers support source NAT, allowing all servers in the internal subnet to access the external network with the gateway IP of the virtual router.
They also support destination NAT in the form of floating IPs, addresses from the external network that can be mapped onto specific servers in the internal subnet to make them externally accessible.
Floating IPs are allocated from a CSP-managed pool, and can be controlled by a per-project quota.
There is also a set of API extensions that allow more fine grained port-forwarding, mapping different TCP or UDP ports of a floating IP to different internal IP addresses [^pf].

### Port Security and Spoofing

OpenStack ports have the flag `port_security_enabled`, that is set to true by default and can only be changed by the owner of the corresponding network.
The default value of that flag is controlled by a `port_security_enabled` flag on the network.
Besides enabling security groups for a port, it also enables a number of built-in spoofing protections.

Whether this flag is set is primarily of concern for shared provider networks, as users only have limited control over the gateway ports of virtual routers.
A lack of spoofing protection in a shared network, however, does enable a number of attacks that a malicious user or compromised server could perform against other servers in the network, such as DHCP-spoofing or ARP-Poisoning.

There are legitimate use-cases for networks without port security, such as the implementation of network function virtualisation (NFV) within a server (i.e. having a server perform the function of a virtual router).
This seems to be more of a niche use-case, however, and may warrant the creation of a project-specific provider network, rather than making all other projects vulnerable to spoofing attacks.

### Options considered

#### IPv6

The OpenStack Network API allows the creation of subnets with either IPv4 or IPv6 address ranges, as indicated by the `ip_version` field.
However, to allow external access to either, the CSP needs to provide projects with externally routable addresses for that IP version.

While it is possible (and common) for CSPs to provide both IPv4 and IPv6, the increasing scarcity (and cost) of IPv4 address space may at some point become a barrier to entry for new CSPs.
Mandatory support for IPv6 but not IPv4 addresses this problem, while also providing users with a consistent feature set across SCS clouds.

#### Single Default Provider Network

In principle, CSPs can create multiple provider networks for a number of reasons, for example to make cloud-internal shared services available to projects.
Servers can be connected to multiple networks, and connecting to additional provider networks would not interfere with their ability be externally accessible.

CSPs may also create multiple provider networks with different options for external access, such as separate networks for IPv4 and IPv6, or one external network for use with virtual routers and a separate shared network for direct connection.
This mostly just adds complexity to the setup, though, as a provider network can be both external and shared at the same time, and can even provide both IPv4 and IPv6 subnets in a dual stack setup [^ds].

Another problem with multiple provider networks is, that users may only be able to distinguish their respective function by their name.

A single default provider network leaves no ambiguity by the user in this regard and is thus preferable from a standardisation perspective.

#### Shared Provider Network

A shared provider network has the benefit of being easy to use.
Servers can be attached directly and will be accessible immediately, without the requirement to create virtual routers, project-internal networks, subnets, or floating IPs.

Users do have a higher control over server ports than they have over virtual router ports, so it is important to enable Neutrons port security feature on shared provider networks to prevent spoofing.

The lack of address quota may be a problem if IPv4 is used and the number of available addresses is so limited that fairness between projects needs to be enforced.
In that case, CSPs may restrict the number of servers, routers, or ports to limit the addresses used by individual projects.

#### External Provider Network and Subnet Allocation

Creating a project-internal network to connect to an external provider network with a virtual router does take more effort than just using a shared network, but also offers some additional flexibility and control.
In an internal network, users have greater control over IP allocation and may also choose to disable port security.
With the FWaaS API extensions, they can also assign firewall rules to the virtual router, to control which traffic can pass between internal and provider networks.

As described above, there are multiple methods for allocating public IP addresses to project-internal networks.
For IPv6, the currently best option seems to be subnet allocation from a CSP-managed subnet pool, because support for Prefix Delegation is still experimental.
For IPv4, NAT and floating IPs are generally preferred over subnet allocation because of scarcity of IPv4 address space.

#### NAT and Floating IPs

Subnets can only have a size that is a power of two, and will thus usually be oversized for the project.
They also need to reserve one address for the gateway and, if DHCP is used, one or more addresses for DHCP service ports.
Each subnet also has a broadcast and a network address, which for small subnets make up a noticeable part of the address space.

Source NAT, combined with selective use of floating IPs can significantly reduce the number of required addresses over a public IPv4 subnet.
The floating IP quota also offers a finer granularity for distributing IPs among projects, though it is important to note that the routers external gateway IP which is used for the source NAT is not subject to any quotas.

IPv4 NAT can also be used in a dual stack setup alongside a routed IPv6 subnet (source?).

#### Disable RBAC for Users

Per default policy, Neutron allows any user the creation RBAC rules to share resources of their projects with other projects.
Only the use of the `*` wildcard target is limited to admin users.

However, how a network was shared, and who shared it, is not immediately obvious from the perspective of the target project.
The `openstack network list` command will by default not even show the project IDs of the networks.
And even though users can determine the project ID of networks by using `network list --long` or `network show`, they are by default forbidden from accessing any details of other projects, including the project name.

Under these conditions, a malicious user could create a network with a misleading name, share it with target projects to trick them into using it like a provider network, and then intercept their traffic.

For this attack to work, the attacker has to find out the target's project ID, and the target has to be sufficiently oblivious to the CSP's provider network setup.
CSPs can try to educate users on the correct provider networks to use, and can avoid leaking project IDs, but the best protection is to disable the creation of RBAC rules for non-admin users.

#### Required API extensions

The OpenStack Network API has a more modular design than other OpenStack APIs.
New features are added as optional API extensions rather than a linear sequence of micro-version, and different Neutron core-plugins, service plugins, and mechanism drivers may provide different extensions.

In practice, the great majority of OpenStack deployments will use Neutron with the ML2 core plugin and either the `router` or the `ovn-router` service plugins, which should cover all requirements of this standard.
As this standard tries to target the OpenStack API rather than it's specific implementation, we could consider standardizing a minimal set of API extensions.

On the other hand, the mandatory set of API extensions follows directly from the mandated features, e.g. the `external-net`, `provider`, and `router` extensions, which must all be available if an external provider network is required.
So, just specifying mandatory features rather than a certain set of extensions may actually be preferable, as it removes redundancy and thus the potential for inconsistency.

## Standard

CSPs **MUST** provide a provider network to every project to access to the internet.
This provider network will in the following be referred to as the _standard provider network_.
To avoid ambiguity, the standard provider network **SHOULD** be the only provider networks available to projects by default.

The standard provider network **MUST** be an external network, allowing it to be used as external gateway by virtual routers.
The standard provider network **MAY** be a shared network, allowing direct attachment of servers.
If the standard provider network is a shared network, it **MUST** enable port security to prevent projects from interfering with each other.

The standard provider network **MUST** have an IPv6 subnet.
CSPs **MUST** provide a subnet pool for the allocation of at least one public /64 IPv6 prefix per project.

The standard provider network **SHOULD** have an IPv4 subnet.
If CSPs provide an IPv4 subnet, then CSPs **MUST** provide at least one public Floating IP per project.
They **MAY** also provide a subnet pool for the allocation of public IPv4 prefixes to project networks.

CSPs **MUST** provide dynamic routing for all project-allocated public IP-prefixes.

By default, users **SHOULD** be prohibited by policy from creating RBAC rules for networks in their projects, to prevent the creation of faux provider networks.

## Conformance Tests

(TBD, current requirements should all be testable by API, though dynamic routing might be a bit tricky)

## References

[^bgp]: https://docs.openstack.org/neutron/2024.1/admin/config-bgp-dynamic-routing.html
[^pd]: https://docs.openstack.org/neutron/2024.1/admin/config-ipv6.html#prefix-delegation
[^pf]: https://docs.openstack.org/api-ref/network/v2/index.html#floating-ips-port-forwarding
[^ds]: https://docs.openstack.org/neutron/2024.1/admin/config-ipv6.html