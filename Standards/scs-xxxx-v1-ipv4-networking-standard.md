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

#### _Option 1_

Usage of Neutron Routers: Neutron routers are mandated to manage traffic between
internal and external networks. They shall act as the default gateway for VMs
requiring access to external networks and the internet, thereby facilitating the
routing of traffic and enhancing network security.

#### _Option 2_

Security Group Policies: Standardized security group policies shall be applied to all
instances utilizing public IPv4 addresses. These policies must define and enforce access
controls to ensure the security of the cloud environment.

#### _Option 3_
IP Usage Monitoring: SCS clouds must implement monitoring solutions to track the
utilization of IPv4 addresses. This facilitates efficient management of resources and
supports capacity planning efforts.

#### _Option 4_
External Network Naming: All SCS clouds must adopt the naming convention
scs-external-net for external networks. This standardization facilitates easier
identification and management of external network resources.

#### _Option 5_
Floating IPs for Dynamic Allocation: Utilize Floating IPs to allow dynamic reassignment
of public IPv4 addresses to different instances (VMs or Loadbalancers), facilitating
high availability and fault tolerance.

## Open questions

- Naming Convention Flexibility: How rigid should the naming convention for external
networks be across various SCS clouds?
- Security Policy Standardization: To what extent should security group policies be
standardized without impeding individual cloud providers' autonomy?

## Decision

...

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
