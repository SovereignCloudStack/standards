---
title: Taxonomy of Failsafe Levels
type: Decision Record
status: Draft
track: IaaS
---


## Abstract

When talking about redundancy and backups in the context of cloud infrastructures, the scope under which circumstances these concepts apply to various resources is neither homogenous nor intuitive.
There does exist very detailed lists of risks and what consequences there are for each risk, but this Decision Record should give a high-level view on the topic.
So that in each standard that referenced redundancy, it can easily be seen how far this redundancy goes in that certain circumstance.
Readers of such standards should be able to know at one glance, whether the achieved failure safeness is on a basic level or a higher one and whether there would be additional actions needed to protect the data.

This is why this decision record aims to define different levels of failure-safety.
These levels can then be used in standards to clearly set the scope that certain procedures in e.g. OpenStack offer.

## Glossary

### General Terms

| Term               | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Disk               | A physical disk drive (e.g. HDD, SSD) in the infrastructure.                                                                             |
| Host               | A physical machine in the infrastructure providing computational, storage and/or network connectivity capabilities.                      |
| Cyber threat       | Attacks on the infrastructure through the means of electronic access.                                                                    |

### OpenStack Resources

| Resource           | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Virtual Machine    | Equals the `server` resource in Nova.                                                                                                    |
| Ironic Machine     | A physical host managed by Ironic or as a `server` resource in Nova.                                                                     |
| Ephemeral Storage  | Disk storage directly supplied to a virtual machine by Nova. Different from volumes.                                                     |
| (Glance) Image     | IaaS resource usually storing raw disk data. Managed by the Glance service.                                                              |
| (Cinder) Volume    | IaaS resource representing block storage disk that can be attached as a virtual disk to virtual machines. Managed by the Cinder service. |
| (Volume) Snapshot  | Thinly-provisioned copy-on-write snapshots of volumes. Stored in the same Cinder storage backend as volumes.                             |
| Volume Type        | Attribute of volumes determining storage details of a volume such as backend location or whether the volume will be encrypted.           |
| (Barbican) Secret  | IaaS resource storing cryptographic assets such as encryption keys. Managed by the Barbican service.                                     |
| Key Encryption Key | IaaS resource, used to encrypt other keys to be able to store them encrypted in a database.                                              |
| Floating IP        | IaaS resource, an IP that is usually routed and accessible from external networks.                                                       |

### Kubernetes Resources

| Resource           | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Node               | A physical or virtual machine that runs workloads (Pods) managed by the Kubernetes control plane.                                        |
| Kubelet            | An agent that runs on each node in the cluster. It makes sure that containers are running in a Pod.                                      |
| API Server         | The Kubernetes control plane component which exposes the Kubernetes Application Programming Interface (API).                             |
| Pod                | Kubernetes object that represents a workload to be executed, consisting of one or more containers.                                       |
| Container          | A lightweight and portable executable image that contains software and all of its dependencies.                                          |
| Persistent Volume Claim (PVC) | Persistent storage that can be bound and mounted to a pod.                                                                    |

Source: https://kubernetes.io/docs/reference/glossary/

## Context

Some standards provided by the SCS project will talk about or require procedures to back up resources or have redundancy for resources.
This decision record should discuss, which failure threats are CSP-facing and will classify them into several levels.
In consequence these levels should be used in standards concerning redundancy or failure-safety.

## Decision

### Failure Scenarios

First there needs to be an overview about possible failure scenarios in infrastructures as well as their probability of occurrence and the damage they may cause:

#### Hardware Related

| Failure Scenario | Probability | Consequences |
|----|-----|----|
| Disk Failure/Loss | High | Permanent data loss in this disk. Impact depends on type of lost data (data base, user data) |
| Host Failure/Loss (without disks) | Medium to High | Permanent loss of functionality and connectivity of host (impact depends on type of host) |
| Host Outage | Medium to High | Data loss in RAM and temporary loss of functionality and connectivity of host (impact depends on type of host) |
| Rack Outage | Medium | Outage of all nodes in rack |
| Network router/switch outage | High/Medium/Low | ... |
| Loss of network uplink | High/Medium/Low | |
| Power Outage (Data Center supply) | Medium | temporary outage of all nodes in all racks |

#### Environmental

Note that probability for these scenarios is dependent on the location.

| Failure Scenario | Probability | Consequences |
|----|-----|----|
| Fire | Medium | permanent Disk and Host loss in the affected zone |
| Flood | Low | permanent Disk and Host loss in the affected zone |
| Earthquake | Very Low | permanent Disk and Host loss in the affected zone |
| Storm/Tornado | Low | permanent Disk and Host loss in the affected fire zone |

#### Others

| Failure Scenario | Probability | Consequences |
|----|-----|----|
| Cyber threat | High | permanent loss or compromise of data on affected Disk and Host |
| Cluster operator error | High/Medium/Low | ... |
| Software Bug | High | permanent loss or compromise of data that trigger the bug up to data on the whole physical machine |

#### Kubernetes Specific

A similar overview can be provided for Kubernetes infrastructures. These also include the things mentioned for infrastructure failure scenario, since a Kubernetes cluster
would most likely be deployed on top of this infrastructure or face similar problems on a bare-metal installation.
Part of this list comes directly from the official [Kubernetes docs](https://kubernetes.io/docs/tasks/debug/debug-cluster/).

| Failure Scenario                             | Probability | Consequences                                                                                                                                                         |
|----------------------------------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| API server VM shutdown or apiserver crashing | Medium      | Unable to stop, update, or start new pods, services, replication controller                                                                                          |
| API server backing storage lost              | Medium      | kube-apiserver component fails to start successfully and become healthy                                                                                              |
| Supporting services VM shutdown or crashing  | Medium      | Colocated with the apiserver, and their unavailability has similar consequences as apiserver                                                                         |
| Individual node shuts down                   | Medium      | Pods on that Node stop running                                                                                                                                       |
| Network partition / Network problems         | Medium      | Partition A thinks the nodes in partition B are down; partition B thinks the apiserver is down                                                                       |
| Kubelet software fault                       | Medium      | Crashing kubelet cannot start new pods on the node / kubelet might delete the pods or not / node marked unhealthy / replication controllers start new pods elsewhere |
| Cluster operator error                       | Medium      | Loss of pods, services, etc. / lost of apiserver backing store / users unable to read API                                                                            |
| Failure of multiple nodes or underlying DB   | Low         | Possible loss of all data depending on the amount of nodes lost compared to the cluster size, otherwise costly rebuild                                               |

These failure scenarios can result in temporary (T) or permanent (P) loss of the resource or data within.
Additionally, there are a lot of resources in IaaS alone that are more or less affected by these failure scenarios.
The following tables shows the impact **when no redundancy or failure safety measure is in place**:

### Impact on OpenStack Resources (IaaS layer)

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | Natural Catastrophy | Cyber Threat | Software Bug |
|----|----|----|----|----|----|----|----|
| Image | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| Volume | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| User Data on RAM /CPU | | P | P | P | P | T/P | P |
| volume-based VM | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| ephemeral-based VM | P (if on disk) | P | P | T | P (T if lucky) | T/P | P |
| Ironic-based VM | P (all data on disk) | P | P | T | P (T if lucky) | T/P | P |
| Secret | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| network configuration (DB objects) | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | P |
| network connectivity (materialization) | | T (if on node) | T/P | T | P (T if lucky) | T/P | T |
| floating IP | P (if on disk) | T (if on node) | T/P | T | P (T if lucky) | T/P | T |

### Impact on Kubernetes Resources (KaaS layer)

:::note

In case the KaaS layer runs on top of IaaS layer, the impacts described in the above table apply for the KaaS layer as well.

:::

| Resource | Disk Loss | Node Loss | Rack Loss | Power Loss | Natural Catastrophy | Cyber Threat | Software Bug |
|----|----|----|----|----|----|----|----|
|Node|P| | | | | |T/P|
|Kubelet|T| | | | | |T/P|
|Pod|T| | | | | |T/P|
|PVC|P| | | | | |P|
|API Server|T| | | | | |T/P|

For some cases, this only results in temporary unavailability and cloud infrastructures usually have certain mechanisms in place to avoid data loss, like redundancy in storage backends and databases.
So some of these outages are easier to mitigate than others.

### Classification by Severity

A possible way to classify the failure cases into levels considering the matrix of impact would be, to classify the failure cases from small to big ones.
The following table shows such a classification, the occurrence probability of a failure case of each class and what resources with user data might be affected.

:::caution

This table only contains examples of failure cases and examples of affected resources.
This should not be used as a replacement for a risk analysis.
The column **user hints** only show examples of standards that may provide this class of failure safety for a certain resource.
Customers should always check, what they can do to protect their data and not rely solely on the CSP.

:::

| Level/Class | Probability | Failure Causes | Loss in IaaS | User Hints |
|---|---|---|-----|-----|
| 1. Level | Very High | small Hardware or Software Failures (e.g. Disk/Node Failure, Software Bug,...) | individual volumes, VMs... | CSPs MUST operate replicas for important components (e.g. replicated volume back-end, uninterruptible power supply, ...). Users SHOULD backup their data themself and place it on an other host. |
| 2. Level | High | important Hardware or Software Failures (e.g. Rack outage, small Fire, Power outage, ...) | limited number of resources, sometimes recoverable | CSPs MUST operate replicas for important components (e.g. replicated volume back-end, uninterruptible power supply, ...) OR users MUST backup their data themselves and place it on an other host. |
| 3. Level | Medium | small catastrophes or major Failures (e.g. fire, regional Power Outage, orchestrated cyber attacks,...) | lots of resources / user data + potentially not recoverable | CPSs SHOULD operate hardware in dedicated Availability Zones. Users SHOULD backup their data, themself. |
| 4. Level | Low | whole deployment loss (e.g. natural disaster,...) | entire infrastructure, not recoverable | CSPs may not be able to save user data from such catastrophes. Users are responsible for saving their data from natural disasters. |

Based on our research, no similar standardized classification scheme seems to exist currently.
Something close but also very detailed can be found in [this (german)](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_3.pdf?__blob=publicationFile&v=2) from the German Federal Office for Information Security.
As we want to focus on IaaS and K8s resources and also have an easily understandable structure that can be applied in standards covering replication, redundancy and backups, this document is too detailed.

## Consequences

Using the definition of levels established in this decision record throughout all SCS standards would allow readers to understand up to which level certain procedures or aspects of resources (e.g. volume types or a backend requiring redundancy) would protect their data and/or resource availability.
