---
title: IPv4 Networking Standard
type: Standard
status: Proposal
track: IaaS
---

## Introduction

This document outlines the standardized approach for the management and allocation of
public IPv4 addresses within Sovereign Cloud Stack (SCS) environments. Its aim is to
ensure a consistent, secure, and efficient methodology for IP address provisioning
across all SCS cloud services.

## Motivation

The motivation behind establishing this standard is to enhance interoperability, improve
security measures, and streamline the operational processes across different SCS clouds.
It addresses the need for a unified procedure in handling IPv4 networking to facilitate
ease of use for IaaS users and DevOps teams.

## Design Considerations

### Options considered

#### _Neutron Routers_

Usage of Neutron Routers: To manage traffic between internal and external networks Neutron Routers **MUST** be used as the default gateway for VMs requiring access to external networks and the internet, thereby facilitating the routing of traffic and enhancing network security. 

CSPs **SHOULD** use OVN or L3agent as High Availability (HA) service deployments.
Standard external networks **MUST NOT** be made accessible as _shared networks_. It is advised that external networks are only reachable by the usage of routing and floating IPs.
However, for special use cases like certain storage or VPN solutions it could be useful to allow _direct access networks_.

External networks and subnets **SHOULD** (very strong should) be configured with _--no-dhcp_ (DHCP - Dynamic Host Configuration Protocol). It is more secure to configure it like this, since it gives less space for reflection attacks, e.g. _Denial of Service_ (DOS) attacks. If _dhcp_ is configured, certain firewall configurations **MUST** be made to catch IPs from the _Neutron dhcp agent_ in the public network. 

#### _Neutron Plugins_

Neutron Plugins: A SCS conform CSP **MAY** use RBAC and VPNaaS plugins.
(Neutron RBAC needs to be configured explicitly to be able to use it. If configured, Neutron configurations can be shared across OpenStack projects. It also can be beneficial for admins, since an admin could bind external networks only to certain projects.)

#### _Security Groups_

Security Group Policies: Standardized security group policies **SHOULD** be applied to all instances utilizing public IPv4 addresses. These policies must define and enforce access
controls to ensure the security of the cloud environment.
Security Groups **SHOULD** be enabled by default but **MUST** be capable of being switched off.

#### _Quota & Monitoring_

Quota: The standard quota of floating IPs and routers **SHOULD** be rather small, e.g. 3-5 floating IPs. This ensures a more fair distribution of these resources for all cloud users. If a user wants to use more of these resources, the user **SHOULD** be able to pay for more.

IP Usage Monitoring: SCS CSPs **SHOULD** implement monitoring solutions to track the utilization of IPv4 addresses. This facilitates efficient management of resources and supports capacity planning efforts.

#### _External Network Naming_

All SCS clouds **SHOULD** adopt the naming convention
scs-external-net for external networks. This standardization facilitates easier identification and management of external network resources.

#### _Floating IPs_

Floating IPs for Dynamic Allocation: Utilization of Floating IPs to allow dynamic reassignment of public IPv4 addresses to different instances (VMs or Loadbalancers), facilitating high availability and fault tolerance.
Floating IPs **MUST** be enabled.

## Open questions

- Naming Convention Flexibility: How rigid should the naming convention for external
networks be across various SCS clouds?
- Load Balancing: Do we want to dictate a Load Balancer or a set of Load Balancers or nothing at all? E.g. Octavia, Yawol

## Decision

...

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
