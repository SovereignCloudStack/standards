---
title: Ceph deployment tool decision
type: Decision Record
status: Draft
track: IaaS
---

## Introduction

This decision record evaluates the choice for a future-proof deployment tool for the networked storage solution (Ceph in the SCS reference implementation). It considers the current and future needs of the reference implementation (OSISM) itself. The decision is based on a detailed comparison of the capabilities and limitations of each tool.

Such deployment tools are designed to roll out and configure the ceph cluster on the systems, offering the ability to manage the cluster through its whole lifetime. This includes adding or removing OSD's, upgrading of Ceph services and managing of crush maps, as outlined in the [Feature-Decision-Table](#feature-decision-table).

## Motivation

As the OSISM reference implementation currently ([Release 6.0.2](https://github.com/osism/release/releases/tag/6.0.2)) relies on ceph-ansible, [which is now deprecated](https://github.com/ceph/ceph-ansible/commit/a9d1ec844d24fcc3ddea7c030eff4cd6c414d23d), a transition to a more modern, sustainable and supported deployment method is necessary.

Furthermore the new deployment tool COULD add new possibilities for deeper and native ceph configuration. This MIGHT give the user the ability to manage the cluster with less effort.

## Design Considerations

The tool selected in this decision MUST ensure:

* ease of migration
  * zero-downtime
  * not doubling hardware costs
* future-proofness
* feature-completeness and feature-maturity
* effective management of Ceph clusters

The tool selected in this decision OPTIONALLY ensures:

* deployment on kubernetes platform
  * this is currently not mandatory in the OSISM reference implementation

## Options considered

### Cephadm

**Purpose**: Cephadm is primarily designed to deploy and manage a Ceph cluster using a minimalistic approach. It is part of the Ceph orchestration ecosystem, directly integrated into Ceph itself.

**Environment**: Best suited for environments where administrators prefer a more traditional approach to manage clusters, usually via command line interfaces.

**Deployment**: It uses containers (primarily Docker or Podman) for deploying Ceph components. The cephadm cli tool and orchestrator streamlines the deployment process.

**Configuration and Management**: Cephadm simplifies the configuration and management of Ceph services. It automates the management of Ceph daemons and services, making it easier to scale and maintain the Ceph storage cluster.

**Integration**: It offers direct integration with Ceph, providing a more seamless experience for Ceph-specific operations.

### Rook

**Purpose**: Rook is a cloud-native storage orchestrator, providing the framework to deploy and manage Ceph storage on Kubernetes. Rook is hosted by the [Cloud Native Computing Foundation (CNCF)](https://cncf.io/) as a [graduated](https://www.cncf.io/announcements/2020/10/07/cloud-native-computing-foundation-announces-rook-graduation/) level project.

**Environment**: Ideal for Kubernetes environments. It allows users to manage Ceph storage systems as part of their Kubernetes workflow.

**Deployment**: It automates the deployment, scaling, and management of Ceph storage clusters on Kubernetes, using its declarative configuration syntax.

**Configuration and Management**: Rook extends Kubernetes functionalities to support Ceph storage operations, making it easier to integrate with cloud-native environments.

**Integration**: As a Kubernetes operator, Rook integrates deeply with Kubernetes, using many of it's features and managing storage with cloud-native tools.

### Comparison and integration into reference implementation (OSISM)

**Environment**: Cephadm is better suited for traditional or standalone environments. Conversely, Rook is tailored for Kubernetes. However, it's important to note that the current state of resource deployment and management on kubernetes within the reference implementation is still in its infancy.

**Deployment**: Cephadm uses containerization for Ceph components, whereas Rook fully embraces the Kubernetes ecosystem for deployment and management. Containerization is already a core concept in the refence implementation.

**Configuration and Management**: Rook may offer a more straightforward experience for those already utilizing Kubernetes, leveraging Kubernetes' features for automation and scaling. In contrast, Cephadm grants finer control over Ceph components, albeit necessitating more manual intervention. In both cases, this is something that needs to be partly abstracted by the reference implementation.

**Integration**: Rook provides better integration with cloud-native tools and environments, whereas Cephadm offers a more Ceph-centric management experience.

### Feature Decision Table

A comparative analysis of Cephadm and Rook highlights the following:

| Feature | Supported in Cephadm | Supported in Rook |
| ------- | -------------------- | ----------------- |
| **Migrate from other setups** | ☑ Adoption of clusters, that where built with ceph-ansible [is officially supported](https://docs.ceph.com/en/quincy/cephadm/adoption/).| ☐ Migration from other setups is not offically supported. See this [issue](https://github.com/rook/rook/discussions/12045). |
| **Connect RGW with OpenStack Keystone** | ☑ Connection is [officially supported](https://docs.ceph.com/en/latest/radosgw/keystone/) by native ceph configuration. | ☐ Only [via workarounds](https://github.com/rook/rook/issues/4754), but [feature is in development](https://github.com/rook/rook/blob/master/design/ceph/object/swift-and-keystone-integration.md). |
| Deploy specific Ceph versions | ☑  | ☑ |
| Upgrade to specific Ceph versions | ☑☑ Streamlined upgrade process. | ☑ Rook, CSI and ceph upgrades have to be aligned. |
| deploy Ceph Monitors | ☑ | ☑ |
| deploy Ceph Managers | ☑ | ☑ |
| deploy Ceph OSDs | ☑ | ☑ |
| deploy Ceph Object Gateway (RGW) | ☑ | ☑ |
| Removal of nodes | ☑ | ☑ |
| Purging of complete cluster | ☑☑ Deletion of data is possible with a [simple command](https://docs.ceph.com/en/quincy/cephadm/upgrade/). | ☑ A cleanup policy or custom jobs have to be created. |

(Deal-Breakers are bold)

☐ not supported (yet)\
☑ supported\
☑☑ better option\
☒ not supported on purpose

## Decision

We decided to adopt Cephadm as the primary method for deploying Ceph.

The decision to adopt Cephadm as the primary method for deploying Ceph is based on its **compatibility with existing ceph-ansible setups**, the **ease of migration**, and **comprehensive feature support**. Cephadm's **native integration with Ceph** and its **straightforward approach to upgrades and management** make it the more suitable choice for the OSISM framework, especially considering the technical challenges and limitations associated with Rook, particularly in **migration scenarios**.

## Related Documents

* [Cephadm Documentation](https://docs.ceph.com/en/latest/cephadm/)
* [Rook Project](https://www.cncf.io/projects/rook/)

## Conformance Tests

* Seamless migration from ceph-ansible to Cephadm.
* Compatibility with existing OSISM deployments and adherence to SCS standards.
