---
title: Mandatory and Supported IaaS Services
type: Standard
status: Draft
track: IaaS
---

## Introduction

To be SCS-compliant a CSP has to fulfill all SCS standards.
Some of those standards are broad and consider ALL services on the IaaS-Layer.
There exist many services on that layer and they need to be limited to have a clear scope for the standards and the Cloud Service Providers following them.
For this purpose, this standard will establish lists for mandatory services that have to be present in a SCS cloud as well as supported services, which are considered by some standards and may be tested or even implemented in the reference implementation but are optional in a sense that their omission will not violate SCS conformance.

## Motivation

There are many OpenStack APIs and their corresponding services that can be deployed on the IaaS level.
These services have differences in the quality of their implementation and liveness and some of them may be easily omitted when creating an IaaS deployment.
To fulfill all SCS-provided standards only a subset of these APIs are required.
Some more but not all remaining OpenStack APIs are also supported additionally by the SCS project and may be part of its reference implementation.
This results in different levels of support for specific services.
This document will give readers insight about how the SCS classifies the OpenStack services accordingly.
If a cloud provides all mandatory and any number of supported OpenStack APIs, it can be tested for SCS-compliance.
Any unsupported services will not be tested.

## Mandatory OpenStack services

The following OpenStack services MUST be present in SCS-compliant IaaS deployments:

| OpenStack Service | description |
|-----|-----|
| **Cinder** | Block Storage service |
| **Glance** | Image service |
| **Keystone** | Identity service |
| **Neutron** | Networking service |
| **Nova** | Compute service |
| **Octavia** | Load-balancer service |
| **Placement** | Hardware Describing Service for Nova |
| **S3 API object storage** | No formal standard exists, many implementations: Swift, RadosGW, minio... |

:::caution

S3 API implementations may differ in certain offered features.
CSPs must publicly describe, which implementation they use in their deployment.
Users should always research whether a needed feature is supported in the offered implementation.

:::

## Supported OpenStack services

The following services MAY be present in SCS-compliant IaaS deployment and are considered in the SCS standards.

| OpenStack Service | description |
|-----|-----|
| **Barbican** | Key Manager service |
| **Cloudkitty** | Rating/Billing service |
| **Ceilometer** | Telemetry service |
| **Designate** | DNS service |
| **Gnocchi** | Time Series Database service |
| **Heat** | Orchestration service |
| **Horizon** | Dashboard |
| **Ironic** | Bare Metal provisioning service |
| **Manila** | Shared File Systems service |
| **Masakari** | Instances High Availability service |
| **Skyline** | Dashboard |

## Unsupported OpenStack services

All other OpenStack services that are not mentioned in the mandatory or supported lists are not tested for their compatibility and behavior in SCS clouds by the SCS community.
Those services MAY be integrated into IaaS deployments by a CSP on their own responsibility but the SCS will not assume they are present and potential issues that occur during deployment or usage have to be handled by the CSP on their own accord.
The SCS standard offers no guarantees for compatibility or reliability of services categorized as unsupported in conjunction with an SCS-conformant infrastructure.

## Related Documents

[The OpenStack Services](https://www.openstack.org/software/)

## Conformance Tests

The presence of the mandatory OpenStack services (except the S3) will be tested in a test-script.
As the S3 interface is a moving target, it may be integrated into the test suite but the test result will not be taken into account to determine conformance.
