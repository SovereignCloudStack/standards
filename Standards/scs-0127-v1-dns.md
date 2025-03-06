---
title: DNS Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

The Domain Name System (DNS) is used to resolve name records to addresses in Internet Protocol (IP) based networks, primarily but not limited to the public Internet.

DNS has a variety of use cases in OpenStack infrastructures.
For basic egress traffic, it is used to enable proper connectivity for customer virtual machines to the outside world by offering DNS servers to them.
For internal connectivity and discoverability between cloud resources, DNS is used to make virtual machines addressable via their name within tenant networks.
DNS can also be used to publish DNS records for virtual machines that have external connectivity by integrating and using the OpenStack DNS v2 API, e.g. by integrating the Designate service.

## Terminology

| Term | Meaning |
|---|---|
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| DNS | Domain Name System |
| DNS recursor | Recursive DNS resolver, see "Recursive resolver" as per [RFC 9499](https://datatracker.ietf.org/doc/html/rfc9499#dns-servers-and-clients) |
| network | OpenStack Neutron network resource unless stated otherwise |
| OVN | Virtual networking component of the Open vSwitch project and a mechanism driver choice for OpenStack Neutron as an alternative to the OVS driver |
| OVS | Abbreviation for Open vSwitch, a virtualized switch solution and mechanism driver choice for OpenStack Neutron |
| port | OpenStack Neutron port resource unless stated otherwise |
| SCS | Sovereign Cloud Stack |
| VM | Virtual Machine, also known as "server" resource in OpenStack Nova |

## Motivation

The behavior and feature set regarding DNS functionalities can differ greatly between OpenStack infrastructures, depending on their individual configuration.

With this standard the SCS project aims to establish a baseline for reliable and consistent DNS features in SCS cloud environments.

## Design Considerations

OpenStack offers a lot of extension choices and even a dedicated service (Designate) for DNS functionality.
The standard should make sure that a specified level of DNS functionality can be reached while taking into account that not all settings and choices might be feasible for CSPs to implement.

### Options considered

#### Making Designate mandatory

To offer a consistent feature set to customers, the SCS project could consider to make Designate mandatory in a sense that SCS-compliant clouds would need to integrate the service, make it available to customers and properly configure it for publishing DNS records.
This would offer easy DNS-as-a-Service (DNSaaS) functionality to customers.

However, this would also require solid DNS expertise at CSP-side to properly set up and integrate Designate and DNS zones as Designate does not act as a full DNS server on its own but instead relies on external DNS providers or self-hosted DNS infrastructures that the CSP needs to integrate into it.

Furthermore, the CSP will need to be aware of threats like [DNS Zone Squatting](https://docs.openstack.org/designate/2024.1/admin/production-guidelines.html#dns-zone-squatting) and [DNS Cache Poisoning](https://docs.openstack.org/designate/2024.1/admin/production-guidelines.html#dns-cache-poisoning) when offering DNSaaS via Designate and mitigate them, further increasing the burden on the CSP.

#### Mandating the use of DNSSEC

The DNSSEC extension to DNS ensures authenticity and integrity of the data provided to DNS resolvers.
This protects against attacks like cache poisoning and increases the trustworthiness of the DNS infrastructure.

This is a direct improvement for customers and yields low complexity for the CSP to implement since it is supported by most major DNS implementations natively.

#### Mandating the use of local DNS recursors

A local DNS recursor can be used to cache and serve DNS responses locally. It servers as a proxy between the clients and external DNS servers.
This improves performance and speed of DNS resolution in the infrastructure.
Furthermore, it can be configured to use DNSSEC and DNS over TLS to increase security and privacy of DNS requests it handles for clients.
Regardless of whether clients within the cloud infrastructure individually support those features or not, they all benefit from a local recursor implementing it as their DNS traffic is then properly protected outside of the infrastructure.

As such, the implementation of local DNS recursors in the infrastructure can be very beneficial.
This standard should consider mandating or at least recommending the use of local DNS recursors for SCS clouds to be configured as the default DNS servers for Neutron resources.

#### Extension and driver choices

There is a hierarchy of DNS extensions in the Networking API in which they supersede one another in terms of functionality:

- dns-integration
- dns-domain-ports (includes functionality of dns-integration)
- subnet-dns-publish-fixed-ip (includes functionality of dns-integration and dns-domain-ports)
- dns-integration-domain-keywords (includes functionality of all of the above)

For example, to get the "subnet-dns-publish-fixed-ip" functionality, either "subnet-dns-publish-fixed-ip" or "dns-integration-domain-keywords" (which includes the former) must be activated.

Note that each API extension has a corresponding backend driver functionality associated to it.
The availability of each API extension depends on the backend configuration and implementation.

As a result, the DNS functionalities and behaviors available to the customer vary depending on the individual backend configuration of the Networking API.
Mandating or recommending the integration of specific drivers/extensions can therefore be crucial to establish specific DNS functionality baselines for both internal DNS and DNS-as-a-Service:

The "dns-integration" extension provides the basic feature set for internal DNS resolution and should be the minimum requirement.

The "dns-domain-ports" extension adds port-specific DNS domain name override capabilities but those are only important for DNS-as-a-Service scenarios mostly.

Starting with the "subnet-dns-publish-fixed-ip" API extension, the largest flexibility is provided in regards to self-service publishing DNS records for fixed IPs from externally reachable tenant networks (e.g. for IPv6 subnet pools).
In cases where DNS-as-a-Service is offered (e.g. via Designate), this extension should be recommended as opposed to its predecessors.

The "dns-integration-domain-keywords" extension allows dynamically resolving placeholders for user or project id/name in the DNS domain name attribute for port and network metadata.
Its use case seems pretty niche and will most likely be considered entirely optional by the standard.

## Standard

The decisions of this standard will be categorized into three main sections: default DNS servers, internal DNS and external DNS.

Default DNS servers refer to the DNS servers communicated to tenant VMs for DNS resolution as well as any local recursors involved.

Internal DNS refers to the DNS resolution that OpenStack Neutron implements internally to make VM instances' addresses resolvable via name within the same tenant network.

DNS-as-a-Service refers to the integration of external or public DNS via the OpenStack DNS v2 API and its publishing of DNS records for VMs that are externally reachable.
This is an optional feature of OpenStack clouds and can be implemented by integrating the Designate service for example.

### Default DNS servers

- In OVS-based setups, the `dnsmasq_local_resolv` setting for Neutron DHCP agents MUST be disabled.
- One or more local DNS recursors SHOULD be integrated into the infrastructure.
  - In case one or more local DNS recursors are provided, the *DNS server setting* MUST point to the local DNS recursor(s) only.
  - Any local DNS recursor referenced by the *DNS server setting* MUST implement DNSSEC validation and offer DNSSEC itself.
- If the cloud infrastructure has any provider networks connected to the internet, then the *DNS server setting* entries MUST contain DNS servers (recursors or resolvers) that are able to resolve public DNS records.
- If no local DNS recursor is integrated and one or more public DNS server(s) are referenced in the *DNS server setting*, all referenced public DNS servers MUST offer DNSSEC as well as validate DNSSEC themselves and discard invalid responses.

The *DNS server setting* refers to the following:

- In OVS-based setups, the `dnsmasq_dns_servers` setting in the `[DEFAULT]` section of the `dhcp_agent.ini` for all Neutron DHCP agents.
- In OVN-based setups, the `dns_servers` setting in the `[ovn]` section of `ml2_conf.ini`.

### Internal DNS

#### DNS Extensions

In the Networking API, the "dns-integration" extension SHOULD be enabled to offer internal DNS resolution.

For Neutron, this can implemented by enabling one of the following extension drivers:

- `dns`
- `dns_domain_ports` (includes `dns`)
- `subnet_dns_publish_fixed_ip` (includes `dns` and `dns_domain_ports`)
- `dns_domain_keywords` (includes all of the above)

The extension driver setting is part of the ML2 plugin configuration (example for `dns_domain_ports`):

```ini
[ml2]
extension_drivers = ...,dns_domain_ports
```

(the `...` resembles a placeholder for other enabled drivers)

#### Internal DNS Domain

The `dns_domain` setting in the global Neutron configuration will act as the default domain name for any ports created by users unless overridden by explicit network or port settings.
A CSP MAY choose this setting freely but SHOULD NOT change it after the initial deployment of the cloud.

### DNS-as-a-Service

The following section only applies to SCS clouds which include the DNS-as-a-Service functionality for customers via the [OpenStack DNS v2 API](https://docs.openstack.org/api-ref/dns/dns-api-v2-index.html), e.g., through Designate.
All guidelines above still apply.

When providing a service like Designate, it MUST be ensured that threats like [DNS Zone Squatting](https://docs.openstack.org/designate/2024.1/admin/production-guidelines.html#dns-zone-squatting) and [DNS Cache Poisoning](https://docs.openstack.org/designate/2024.1/admin/production-guidelines.html#dns-cache-poisoning) are considered and mitigated where possible.

In the Networking API, the "dns-domain-ports" extension SHOULD be enabled to offer the full range of DNS record settings for both ports and networks.
This is implemented by the `dns_domain_ports` Neutron extension driver for the ML2 plugin.
See the Internal DNS section above for an example on how to enable an extension driver.

However, is RECOMMENDED to provide the "subnet-dns-publish-fixed-ip" API extension for the Networking API in addition to "dns-domain-ports".
In Neutron, this can be done by activating either the `subnet_dns_publish_fixed_ip` or `dns_domain_keywords` extension driver instead of `dns_domain_ports`.

## Related Documents

- [OpenStack Designate Production Guidelines](https://docs.openstack.org/designate/latest/admin/production-guidelines.html)
- [OpenStack User Guide for basic usage of DNS-as-a-Service with Neutron and Nova resources](https://docs.openstack.org/designate/latest/user/neutron-integration.html)
- [OpenStack Configuration and User Guide for various DNS-as-a-Service scenarios in Neutron](https://docs.openstack.org/neutron/latest/admin/config-dns-int-ext-serv.html)

## Conformance Tests

Most of the guidelines in this standard are not mandatory.
The only hard requirement for any SCS cloud is that `dnsmasq_local_resolv` must be disabled in Neutron, which cannot be tested from outside of the infrastructure.

As such, there are currently no applicable conformance tests for this standard that can be executed via public interfaces of an SCS cloud.
