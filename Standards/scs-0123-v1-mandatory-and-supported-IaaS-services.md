---
title: Mandatory and Supported IaaS Services
type: Standard
status: Stable
stabilized_at: 2024-11-18
track: IaaS
---

## Introduction

To be SCS-compliant a Cloud Service Provider (CSP) has to fulfill all SCS standards.
Some of those standards are broad and consider all APIs of all services on the IaaS-Layer like the consideration of a [role standard](https://github.com/SovereignCloudStack/issues/issues/396).
There exist many services on that layer and for a first step they need to be limited to have a clear scope for the standards and the Cloud Service Providers following them.
For this purpose, this standard will establish lists for mandatory services whose APIs have to be present in a SCS cloud as well as supported services, which APIs are considered by some standards and may even be tested for their integration but are optional in a sense that their omission will not violate SCS conformance.

## Motivation

There are many OpenStack APIs and their corresponding services that can be deployed on the IaaS level.
These services have differences in the quality of their implementation and liveness and some of them may be easily omitted when creating an IaaS deployment.
To fulfill all SCS-provided standards only a subset of these APIs are required.
Some more but not all remaining OpenStack APIs are also supported additionally by the SCS project and may be part of its reference implementation.
This results in different levels of support for specific services.
This document will give readers insight about how the SCS classifies the OpenStack APIs accordingly.
If a cloud provides all mandatory and any number of supported OpenStack APIs, it can be tested for SCS-compliance.
Any unsupported APIs will not be tested.

## Mandatory IaaS APIs

The following IaaS APIs MUST be present in SCS-compliant IaaS deployments and could be implemented with the corresponding OpenStack services:

| Mandatory API | corresponding OpenStack Service | description |
|-----|-----|-----|
| **block-storage** | Cinder | Block Storage service |
| **compute** | Nova | Compute service |
| **identity** | Keystone | Identity service |
| **image** | Glance | Image service |
| **load-balancer** | Octavia | Load-balancer service |
| **network** | Neutron | Networking service |
| **s3** | S3 API object storage | Object Storage service |

:::caution

S3 API implementations may differ in certain offered features.
CSPs must publicly describe the endpoints of their S3 solutions and which implementations they use in their deployment.
Users should always research whether a needed feature is supported in the offered implementation.

:::

The endpoints of services MUST be findable through the `catalog list` of the identity API[^1].

[^1]: [Integrate into the service catalog of Keystone](https://docs.openstack.org/keystone/latest/contributor/service-catalog.html)

## Supported IaaS APIs

The following IaaS APIs MAY be present in SCS-compliant IaaS deployment, e.g. implemented thorugh the corresponding OpenStack services, and are considered in the SCS standards.

| Supported API | corresponding OpenStack Service | description |
|-----|-----|-----|
| **bare-metal** | Ironic | Bare Metal provisioning service |
| **billing** | CloudKitty | Rating/Billing service |
| **dns** | Designate | DNS service |
| **ha** | Masakari | Instances High Availability service |
| **key-manager** | Barbican | Key Manager service |
| **object-store** | Swift | Object Store with different possible backends |
| **orchestration** | Heat | Orchestration service |
| **shared-file-systems** | Manila | Shared File Systems service |
| **telemetry** | Ceilometer | Telemetry service |
| **time-series-database** | Gnocchi | Time Series Database service |

## Unsupported IaaS APIs

All other OpenStack services, whose APIs are not mentioned in the mandatory or supported lists will not be tested for their compatibility and conformance in SCS clouds by the SCS community.
Those services MAY be integrated into IaaS deployments by a Cloud Service Provider on their own responsibility but the SCS will not assume they are present and potential issues that occur during deployment or usage have to be handled by the CSP on their own accord.
The SCS standard offers no guarantees for compatibility or reliability of services categorized as unsupported.

## Related Documents

[The OpenStack Services](https://www.openstack.org/software/)

## Conformance Tests

The presence of the mandatory OpenStack APIs will be tested in [this test-script](https://github.com/SovereignCloudStack/standards/blob/mandatory-and-supported-IaaS-services/Tests/iaas/mandatory-services/mandatory-iaas-services.py).
The test will further check, whether the object store endpoint is compatible to s3.
