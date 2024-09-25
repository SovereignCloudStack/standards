---
title: Replacement of the deprecated ceph-ansible tool
type: Decision Record
status: Draft
track: IaaS
---

## Abstract

This decision record evaluates the choice for a modern, future-proof deployment tool for the networked storage solution Ceph in the SCS reference implementation, [OSISM](https://osism.tech/).
The new deployment tool aims to enhance Kubernetes integration within SCS, potentially allowing users to manage the Ceph cluster with greater ease and efficiency.

## Context

The current reference implementation relies on `ceph-ansible`, [which is now deprecated](https://github.com/ceph/ceph-ansible/commit/a9d1ec844d24fcc3ddea7c030eff4cd6c414d23d). As a result, this decision record evaluates two alternatives: [Cephadm](https://docs.ceph.com/en/latest/cephadm/) and [Rook](https://rook.io/docs/rook/latest-release/Getting-Started/intro/).

Both tools are designed to roll out and configure Ceph clusters, providing the capability to manage clusters throughout their lifecycle. This includes functionalities such as adding or removing OSDs, upgrading Ceph services, and managing CRUSH maps, as outlined in the [Feature-Decision-Table](#feature-decision-table).

This decision record considers both the current and future needs of the reference implementation. The decision is guided by a comprehensive comparison of each tool's capabilities and limitations as well as the SCS communities needs and futures objectives.

### Comparison of Features

The tool selected in this decision MUST ensure:

* ease of migration
* future-proofness
* feature-completeness and feature-maturity
* effective management of Ceph clusters

#### Feature Decision Table

A comparative analysis of Cephadm and Rook highlights the following:

| Feature | Supported in Cephadm | Supported in Rook |
| ------- | -------------------- | ----------------- |
| Migrate from other setups | ☑ Adoption of clusters, that where built with ceph-ansible [is officially supported](https://docs.ceph.com/en/quincy/cephadm/adoption/).| ☐ Migration from other setups is not offically supported. See this [issue](https://github.com/rook/rook/discussions/12045). Consequently, SCS develops a migration tool, named [rookify](https://github.com/SovereignCloudStack/rookify). Alternatively, Rook allows to use [Ceph as an external cluster](https://rook.io/docs/rook/latest-release/CRDs/Cluster/external-cluster/external-cluster/). |
| Connect RGW with OpenStack Keystone | ☑ | ☑ Experimental |
| Deploy specific Ceph versions | ☑  | ☑ |
| Upgrade to specific Ceph versions | ☑ Streamlined upgrade process. | ☑ Rook, CSI and Ceph upgrades have to be aligned, there is a [guide](https://rook.io/docs/rook/latest-release/Upgrade/health-verification/) available for each Rook version. |
| Deploy Ceph Monitors | ☑ | ☑ |
| Deploy Ceph Managers | ☑ | ☑ |
| Deploy Ceph OSDs | ☑ | ☑ |
| Deploy Ceph Object Gateway (RGW) | ☑ | ☑ |
| Removal of nodes | ☑ | ☑ |
| Purging of complete cluster | ☑ | ☑ |

☐ not supported (yet)
☑ supported
☑☑ better option
☒ not supported on purpose

#### Evaluation in the Light of SCS Community Plans and Preferences

**Environment**: Cephadm is better suited for traditional or standalone environments. Conversely, Rook is tailored for Kubernetes. That being said, it's important to note that the current state of resource deployment and management on Kubernetes within the IaaS reference implementation is still in its early stages. This would make Rook one of the first components to utilise Kubernetes in OSISM.

**Deployment**: Cephadm uses containerization for Ceph components, whereas Rook fully embraces the Kubernetes ecosystem for deployment and management. Although containerization is already a core concept in the reference implementation, there is a strong push from the SCS community to adopt more Kubernetes.

**Configuration and Management**: Rook offers a more straightforward experience for those already utilizing Kubernetes, leveraging Kubernetes' features for automation and scaling. In contrast, Cephadm grants finer control over Ceph components, albeit necessitating more manual intervention. In both cases, this is something that needs to be partly abstracted by the reference implementation.

**Integration**: Rook provides better integration with cloud-native tools and environments, whereas Cephadm offers a more Ceph-centric management experience.

**Migration**: Rook does not currently provide any migration support, while Cephadm does offer this capability. However, the SCS community is highly supportive of developing a migration tool (Rookify) for Rook, as this would enhance SCS's influence by offering the first migration solution specifically for Rook users.

**SCS Community**: An important factor in our decision is the preferences and direction of the SCS community and its providers. There is a noticeable trend towards increased use of Kubernetes within the community. This indicates a preference for deployment tools that integrate well with Kubernetes environments.

**SCS Future Goals**: The SCS community is open to building tools that provide open-source, publicly available solutions beyond the scope of SCS. This openness to development efforts that address limitations of the chosen tools, such as Rook, is also a key consideration in our decision.

## Decision

As OSISM will increasingly focus on a Kubernetes-centric approach for orchestration in the near future, adopting Rook is a more suitable and standardized approach. Moreover, many service providers within the SCS community (including several who deploy OSISM) already have experience with Kubernetes. Regarding the missing OpenStack Keystone integration, we are confident that colleagues, who work on this issue, will provide a solution in a timely manner. We expect that deploying Ceph with Rook will simplify deployment and configuration form the outset.
In order to allow for a migration from existing Ceph installations to Rook, we decided to develop a migration tool (called Rookify) for the reference implementation. If the development of Rookify goes beyond the targeted scope of the reference implementation the tool will add value to the Ceph as well as the Rook community.

## Consequences

Migrating an existing Ceph environment onto Kubernetes, as well as bringing together existing but independent Ceph and Kubernetes environments, will become straight forward without much manual interference needed.
Landscapes that currently do not deploy a Kubernetes cluster have to adapt and provide a Kubernetes cluster in the future.
