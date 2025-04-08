---
title: SCS Provider Network Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

Many use-cases of IaaS require virtual servers to be able to connect to network resources outside of the cloud environment, often to the internet.
OpenStack supports this by allowing CSPs to map non-virtualized networks onto specific virtual networks, such that virtual routers and servers can connect to them.

Such networks will usually be created in a provider-managed project and then shared to user projects using access control features of the Networking API.
Because they have to be set up by the cloud provider, networks of this type are generally referred to as _provider networks_, though that term can also be used in a broader sense to refer to other types of CSP-managed virtual networks.

When setting up provider networks for external access, CSPs have a number of different options regarding usage restrictions and the allocation of IP addresses.
This document defines a standardized approach for using provider networks to allocate public IP addresses and provide external access in a way that is portable across SCS clouds.

### Glossary

The following terms are used throughout this document:

| Term | Meaning |
|------|---------|
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure. |
| Server | Server object in the OpenStack Compute API, usually represents a virtual machine, though there are also compute drivers for containers and bare metal servers. |
| Virtual Network | A virtualized network managed by OpenStack, provides connectivity between servers and other network resources, such as virtual routers. |
| Virtual Router | OpenStack resource that can be used to route and bridge between virtual networks and provide other features such as NAT. |
| Subnet | Subdivision of available IP address space using address prefixes. In OpenStack also an abstraction for controlling IP address allocation in a virtual network. |
| DHCP | Dynamic Host Configuration Protocol: Used to automatically configure hosts in a network with IP addresses, default routes, and other information such as DNS servers. |
| Prefix | IP address prefix of a given bit-length N, written as _ADDRESS/N_. Divides addresses into a network and a host part, a shorter prefix allows more hosts but takes up more address space. |
| NAT | Network Address Translation: mapping (usually public) IPv4 addresses onto a different (usually private) address space. May allows multiple hosts to share a public address by multiplexing TCP/UDP ports. |
| Networking RBAC | A mechanism in the Networking API to give projects limited access to resources owned by other projects. Used by CSPs to create provider networks. Not to be confused with the role-based access control of OpenStack's policy mechanism. |
| Shared Network | Virtual network that is shared between projects in a way that allows direct attachment of servers. |
| External Network | Virtual network that is shared between projects in a way that only allows virtual routers to use it as external gateway. Typically used by CSPs to provide access to networks outside of the cloud environment. |
| Provider Network | A CSP-managed virtual network made available to projects as either shared or external, typically connected to non-virtualized infrastructure. |

## Motivation

The ability to interface virtualised resources with networks outside of the cloud environment, such as the internet, is an important part of IaaS.
Providing external access in an OpenStack cloud requires a number of configuration choices from the CSP, some of which have direct implications on how users interact with the cloud.
This standard identifies some of these options and defines a baseline setup that provides flexibility and consistency to users but is also realistic to implement for CSPs.

## Design Considerations

This section will provide some general background on OpenStack provider networks before considering specific options to standardize.

### Provider Network Access Control

In OpenStack, ownership of resources is generally tracked through projects, and, as per default policy, only members of a project have access to its resources
This is also true for CSP-managed resources, such as provider networks, which have to be created in a CSP-internal project, and are initially only accessible in this project.

They can then be made available to other projects by using the Networking API's Role-based Access Control (_RBAC_) extension.
(This is it's official name in the documentation, even though it isn't technically role-based. To avoid confusion with the actual RBAC of OpenStack's API authorization, it will in the following referred to as _Networking RBAC_.)

Networking RBAC rules for virtual networks support the two actions `access_as_external` and `access_as_shared`, and can be created automatically on `openstack network create` with the options `--external` and `--share`.

* `access_as_external` allows networks to be used as external gateway for virtual routers in the target projects. Such networks are in the following referred to as _external networks_.
  External networks have some special properties, such as allowing the creation of floating IPs, which will be discussed in the next section.
* `access_as_shared` allows networks to be attached directly to servers in the target projects. Such networks are in the following referred to as _shared networks_.

The rules can be created with either a specific target project ID, or with a wild card (`*`) to target all projects.
They can also overlap, allowing a network to be both external and shared to the same target projects.

### Address Allocation and Routing

CSPs can assign a subnet to a provider network to supply connected servers or virtual routers with externally routable (e.g. public) IP addresses.
This works well for shared networks, where servers can be attached directly, but there is no quota option to limit the number of allocated addresses per project.

Making servers in a project-internal network externally accessible through a virtual router is a bit more complicated, though.
One option is for the user to create a subnet with an external IP range for the internal network, and then ask the CSP to configure a static route to the subnet via the gateway IP of a virtual router.
This is cumbersome to set up manually, but can be automated using the `bgp` extension of the Networking API, which is currently implemented both by the `neutron-dynamic-routing` project [^bgp] and by the `ovn` mechanism driver when used with the `ovn-bgp-agent` [^ovn-bgp].
For users, this takes the form of a CSP-managed shared subnet pool, which they can use to create externally routable subnets, limited by a per-project quota.

For IPv6, there is also the option of prefix delegation, where a DHCPv6 server automatically assigns an IPv6 prefix to a subnet when it connects to the external provider network [^pd].
This means that ports in the subnet can lose their addresses and get assigned new ones if the subnet is removed from the external network and later reattached.
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

#### Public IP Address Allocation

For public clouds, external access generally means access to (and from) the internet, with allocation of public IP addresses.
Providing a standardized approach for the allocation of public IP addresses is the main motivation for this standard.

However, the SCS Standards are intended to be applicable not just to public clouds, but also to private or even air-gapped cloud environments which have different requirements for IP address allocation.
One way to reconcile these requirements would be to limit the scope the requirements of this standard to only apply to cloud environment that support the allocation of public IP addresses.

There are common networking use-cases between public and private clouds, however, like the very common requirement to connect to virtual servers via SSH.
For users (or any automated tooling that users might deploy) to have a standardized way of connecting to virtual servers in their projects is very valuable, regardless of whether this access happens across the Internet or within an isolated internal network or VPN.

So instead of standardizing allocation of public IP addresses for some clouds, it might be more useful to require the allocation of IP addresses that are reachable for API users in all clouds.
Public clouds can then have the additional requirement that those allocated addresses must also be public.

#### IPv6

The OpenStack Networking API allows the creation of subnets with either IPv4 or IPv6 address ranges, as indicated by the `ip_version` field.
However, to allow external access to either, the CSP needs to provide projects with externally routable addresses for that IP version.

While it is possible (and common) for CSPs to provide both IPv4 and IPv6, the increasing scarcity (and cost) of IPv4 address space may at some point become a barrier to entry for new CSPs.
Mandatory support for IPv6 but not IPv4 addresses this problem, while also providing users with a consistent feature set across SCS clouds.

#### Single Default Provider Network

In principle, CSPs can create multiple provider networks for a number of reasons, for example to make cloud-internal shared services available to projects.
Servers can be connected to multiple networks, and connecting to additional provider networks would not interfere with their ability be externally accessible.

CSPs may also create multiple provider networks with different options for external access, such as separate networks for IPv4 and IPv6, or one external network for use with virtual routers and a separate shared network for direct connection.
This mostly just adds complexity to the setup, however, as a provider network can be both external and shared at the same time, and can even provide both IPv4 and IPv6 subnets in a dual stack setup [^ds].

Another problem with multiple provider networks is that users may only be able to distinguish their respective function by their name.

A single default provider network leaves no ambiguity by the user in this regard and is thus preferable from a standardization perspective.

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

As described above, there are multiple methods for allocating external IP addresses to project-internal networks.
For IPv6, the currently best option seems to be subnet allocation from a CSP-managed subnet pool, because support for Prefix Delegation is still experimental.
For IPv4, NAT and floating IPs are generally preferred over subnet allocation because of scarcity of IPv4 address space.

#### NAT and Floating IPs

Subnets can only have a size that is a power of two, and will thus usually be oversized for the project.
They also need to reserve one address for the gateway and, if DHCP is used, one or more addresses for DHCP service ports.
Each subnet also has a broadcast and a network address, which for small subnets make up a noticeable part of the address space.

Source NAT, combined with selective use of floating IPs can significantly reduce the number of required addresses over a public IPv4 subnet.
The floating IP quota also offers a finer granularity for distributing IPs among projects, though it is important to note that the routers external gateway IP which is used for the source NAT is not subject to any quotas.

IPv4 NAT can also be used in a dual stack setup alongside a routed IPv6 subnet.

#### Support for Auto-Allocation

The `auto-allocated-topology` extension of the Networking API can be used to create a default network setup in a project with a single API call [^aa].
It will create a project network with a subnet from either an IPv4 or IPv6 subnet pool (or one of each, if configured that way), as well as a router connecting it to a provider network.
The OpenStack Compute API also has support for this feature, allowing automatic network allocation on server creation.

To function for a project, auto-allocation requires one external provider network and one shared subnet pool to be available, both with the `is_default` flag set to True.
It is possible to have both an IPv4 and an IPv6 subnet pool where `is_default` is set, in which case a dual-stack setup will be allocated.
The behavior is undefined when more than one network in the project is marked as default, or more than one subnet pool per address family.

So, it is strongly advisable to only have one default defined for each.
It seems sensible to standardize on using SCS-mandated resources as auto-allocation defaults, as this is likely to be the behavior expected by users.
It can also be useful for both users and automated compliance tests to determine the defaults in the presence of multiple provider networks.

#### Disable Networking RBAC for Users

Per default policy, Neutron allows any user the creation of Networking RBAC rules to share resources of their projects with other projects.
Only the use of the `*` wildcard target is limited to admin users.

However, how a network was shared, and who shared it, is not immediately obvious from the perspective of the target project.
The `openstack network list` command will by default not even show the project IDs of the networks.
And even though users can determine the project ID of networks by using `network list --long` or `network show`, they are by default forbidden from accessing any details of other projects, including the project name.

Under these conditions, a malicious user could create a network with a misleading name, share it with target projects to trick them into using it like a provider network, and then intercept their traffic.

For this attack to work, the attacker has to find out the target's project ID, and the target has to be sufficiently oblivious to the CSPs provider network setup.
CSPs can try to educate users on the correct provider networks to use, and can avoid leaking project IDs, but the best protection is to disable the creation of Networking RBAC rules for non-admin users.

#### Required API extensions

The OpenStack Networking API has a more modular design than other OpenStack APIs.
New features are added as optional API extensions rather than a linear sequence of micro-version, and different Neutron core-plugins, service plugins, and mechanism drivers may provide different extensions.

In practice, the great majority of OpenStack deployments will use Neutron with the ML2 core plugin and either the `router` or the `ovn-router` service plugins, which should support all extensions required by this standard.
Because this standard tries to target the OpenStack API, rather than it's specific implementation, we might consider standardizing a minimal set of Networking API extensions that CSPs must provide.

On the other hand, the mandatory set of API extensions follows directly from the mandated features, e.g. the `external-net`, `provider`, and `router` extensions, which must all be available if an external provider network is required.
So, just specifying mandatory features rather than a certain set of extensions may actually be preferable, as it removes redundancy and thus the potential for inconsistency.

## Standard

### External Addresses

We define an _external_ address as an IPv4 or IPv6 address that is accessible to a user of the SCS-compliant OpenStack API.
For public clouds, external addresses **MUST** be either IPv4 public addresses or IPv6 global unicast addresses (GUA).

The CSP **MUST** offer allocation of external IPv6 addresses to user projects.
The CSP **SHOULD** offer allocation of external IPv4 addresses to user projects.

### Standard Provider Network

The CSP **MUST** provide every user project with a provider network that can route any external addresses that are allocated to the project.
For external addresses from pool-allocated subnets, this requires support for dynamic routing.
This provider network in the following will be referred to as the _standard provider network_.

The standard provider network **MUST** have the `is_default` flag set to `True`, and it **MUST** be the only provider network in the project with `is_default` set to `True`.
To avoid ambiguity, the standard provider network **SHOULD** be the only provider network available to projects by default.

The standard provider network **MUST** be an external network, allowing it to be used as external gateway by virtual routers.
It **MAY** also be a shared network, allowing direct attachment of virtual servers.
If the standard provider network is a shared network, then it **MUST** be configured allocate external addresses for directly attached servers and ports, and it **MUST** enable port security to prevent projects from interfering with each other.

### IPv6 Allocation

The CSP **MUST** provide a shared subnet pool for the allocation of at least one /64 prefix for external IPv6 addresses per project.
This subnet pool **MUST** have the `is_default` flag set to `True`, and it **MUST** be the only shared IPv6 subnet pool in the project with `is_default` set to `True`.

### IPv4 Allocation

If the CSP offers external IPv4 addresses, they **MUST** provide at least one external Floating IP per project that can be allocated from the standard provider network.
The CSP **MAY** also provide a shared subnet pool for the allocation of prefixes for external IPv4 addresses to project networks.
If such a subnet pool is provided, it **MUST** have the `is_default` flag set to `True`, and it **MUST** be the only shared IPv4 subnet pool in the project with `is_default` set to `True`.

### RBAC Restrictions

By default, users **SHOULD** be prohibited by policy from creating Networking RBAC rules, to prevent the creation of faux provider networks.
The necessary policy change is described in the implementation notes to this standard.

## Conformance Tests

(TBD, current requirements should mostly be testable by API. Testing external routing is more tricky and will require external testing infrastructure of some sort)

## References

[^bgp]: <https://docs.openstack.org/neutron/2024.1/admin/config-bgp-dynamic-routing.html>
[^ovn-bgp]: <https://docs.openstack.org/ovn-bgp-agent/2024.1/readme.html>
[^pd]: <https://docs.openstack.org/neutron/2024.1/admin/config-ipv6.html#prefix-delegation>
[^pf]: <https://docs.openstack.org/api-ref/network/v2/index.html#floating-ips-port-forwarding>
[^ds]: <https://docs.openstack.org/neutron/2024.1/admin/config-ipv6.html>
[^aa]: <https://docs.openstack.org/neutron/2024.1/admin/config-auto-allocation.html>
