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

## Design Considerations

In OpenStack, ownership of resources is generally tracked through projects, and, as per default policy, only members of a project have access to its resources
This is also true for CSP-managed resources, such as provider networks, which have to be created in a designated internal projec, and are initially only accessible in this project.

The Network API's Role Based Access Control (RBAC) extension can then be used to share it with other projects.
RBAC rules for networks support the two actions `access_as_external` and `access_as_shared`, and can be created automatically on `openstack network create` with the options `--external` and `--share`.
* `access_as_external` allows networks to be used as external gateway for virtual routers in the target projects. Such networks are in the following referred to as _external networks_.
* `access_as_shared` allows networks to be attached directly to VMs in the target projects. Such networks are in the following referred to as _shared networks_.

Rules can be created with either a specific target project ID or with a wild card (`*`) to target all projects.
They can also overlap, allowing a network to be both external and shared to the same target projects.

CSPs can assign a subnet to a provider network to supply connected VMs or routers with public IP addresses, making them externally accessible.
This works well for a shared provider network, but connecting VMs behind a virtual router to the internet is a bit more complicated.

* subnet pools
* NAS

### Options considered

#### Single Default Provider Network

* multiple provider networks may confusing, user has to figure out the "right" one
* dual stack possible with multiple subnets in a single networks

#### Shared Provider Network

* simplicity of use, no extra resources
* port security is essential
* no quota for address use

#### External Provider Network and subnet allocation

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

## Decision

CSPs **MUST** provide a standard external network that gives projects access to the internet.

The external network **MUST** have an IPv6 subnet.
CSPs **MUST** provide a subnet pool for the allocation of at least one public /64 IPv6 prefix per project.

The external network **SHOULD** have an IPv4 subnet.
If CSPs provide an IPv4 subnet, then CSPs **MUST** at least one public Floating IP per project.
They **SHOULD** also provide a subnet pool for the allocation of IPv4 prefixes to project networks.

CSPs **MUST** provide dynamic routing for all project-allocated IP-prefixes.

All subnets of external networks **MUST** be configured with `--no-dhcp`.
