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
DNS can also be used to publish DNS records for virtual machines that have external connectivity using the integrating the OpenStack Designate service.

### Glossary

| Term | Meaning |
|---|---|
| SCS | Sovereign Cloud Stack |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| network | OpenStack Neutron network resource unless stated otherwise |
| port | OpenStack Neutron port resource unless stated otherwise |
| DNS | Domain Name System |
| DNS recursor | Recursive DNS resolver |
| VM | Virtual Machine, also known as "server" resource in OpenStack Nova |

## Motivation

The behavior and feature set regarding DNS functionalities can differ greatly between OpenStack infrastructures, depending on their individual configuration.

With this standard the SCS project aims to establish a baseline for reliable and consistent DNS features in SCS cloud environments.

## Design Considerations

OpenStack offers a lot of extension choices and even a dedicated service (Designate) for DNS functionality.
The standard should make sure that a specified level of DNS functionality can be reached while taking into account that not all settings and choices might be feasible for CSPs to implement.

### Options considered

#### Making Designate mandatory

To offer a consistent feature set to customers, the SCS project could consider to make Designate mandatory in a sense that SCS clouds would need to integrate the service, make it available to customers and properly configure it for publishing DNS records.
This would offer easy DNS-as-a-Service functionality to customers.

However, this would also require solid DNS expertise at CSP-side to properly set up and integrate Designate and DNS zones as Designate does not act as a full DNS server on its own but instead relies on external DNS providers or self-hosted DNS infrastructures that the CSP needs to integrate into it.

#### Mandating the use of DNSSEC

The DNSSEC extension to DNS ensures authenticity and integrity of the data provided to DNS resolvers.
This protects against attacks like cache poisoning and increases the trustworthiness of the DNS infrastructure.

This is a direct improvement for customers and yields low complexity for the CSP to implement since it is supported by most major DNS implementations natively.

#### Mandating the use of local DNS recursors

A local DNS recursor can be used to cache and serve DNS responses locally. It servers as a proxy between the clients and external DNS servers.
This improves performance and speed of DNS resolution in the infrastructure.
Furthermore, it can be configured to use DNSSEC, DNS over HTTPS and/or DNS over TLS to increase security and privacy of DNS requests it handles for clients.
Even if individual clients do not support these functionalities, they can still benefit from a local recursor's implementation of those and don't have to trust external DNS servers directly.

As such, the implementation of local DNS recursors in the infrastructure can be very beneficial.
This standard should consider mandating or at least recommending the use of local DNS recursors for SCS clouds to be configured as the default DNS servers for Neutron resources.

## Open questions

RECOMMENDED

## Decision

The decisions of this standard will be categorized into three main sections: forwarded DNS, internal DNS and external DNS.

Forwarded DNS refers to the DNS servers communicated to tenant VMs for DNS resolution as well as any local recursors involved.

Internal DNS refers to the DNS resolution that OpenStack Neutron implements internally to make VM instances' addresses resolvable via name within the same tenant network.

External DNS refers to the integration of external or public DNS via OpenStack Designate and its publishing of DNS records for VMs that are externally reachable (DNS-as-a-Service functionality).

### Forwarded DNS

A CSP MUST disable the `dnsmasq_local_resolv` setting for Neutron DHCP agents.
Instead, the setting `dnsmasq_dns_server` MUST be set accordingly:

- One or more local DNS recursors SHOULD be integrated into the infrastructure and the `dnsmasq_dns_server` setting SHOULD point to the local DNS recursor(s) only.
    - Any local DNS recursor referenced by the `dnsmasq_dns_server` setting MUST implement DNSSEC validation.
- If the cloud infrastructure has any provider networks connected to the internet, then the `dnsmasq_dns_server` entries MUST contain DNS servers (recursors or resolvers) that can resolve public DNS records.
- If no local DNS recursor is integrated and one or more public DNS server(s) are referenced in `dnsmasq_dns_server`, public DNS servers that do not offer DNSSEC MUST NOT be included.

### Internal DNS

#### DNS Extensions

In the Neutron configuration, the `dns_domain_ports` extension driver MUST be enabled to offer the full range of DNS settings for both ports and networks.
Due to it being the successor to the old `dns` extension driver, the `dns` driver MUST NOT be enabled and needs to be removed from the `extension_drivers` setting, if that entry exists.

The extension driver setting is part of the ML2 plugin configuration:

```
[ml2]
extension_drivers = ...,dns_domain_ports
```
(the `...` resembles a placeholder for other enabled drivers)

#### Internal DNS Domain

The `dns_domain` setting in the global Neutron configuration will act as the default domain name for any ports created by users unless overridden by explicit network or port settings.
A CSP MAY change this setting freely.

### External DNS

The following section only applies to SCS clouds which include the DNS service Designate and offer its functionality and API to customers.

<!-- TODO -->

## Related Documents

- [OpenStack User Guide for using DNS with Neutron and Nova resources](https://docs.openstack.org/designate/latest/user/neutron-integration.html)

## Conformance Tests

Conformance Tests, OPTIONAL
