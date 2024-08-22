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

This is why this decision record aims to define different levels of failure safety.
These levels can then be used in standards to clearly set the scope that certain procedures in e.g. OpenStack offer.

## Glossary

| Term                | Explanation                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Availability Zone   | (also: AZ) internal representation of physical grouping of service hosts, which also lead to internal grouping of resources.             |
| BSI                 | German Federal Office for Information Security (Bundesamt für Sicherheit in der Informationstechnik).                                    |
| CSP                 | Cloud Service Provider, provider managing the OpenStack infrastructure.                                                                  |
| Compute             | A generic name for the IaaS service, that manages virtual machines (e.g. Nova in OpenStack).                                             |
| Network             | A generic name for the IaaS service, that manages network resources (e.g. Neutron in OpenStack).                                         |
| Storage             | A generic name for the IaaS service, that manages the storage backends and virtual devices (e.g. Cinder in OpenStack).                   |
| RTO                 | Recovery Time Objective.                                                                                                                 |
| Disk                | A physical disk drive (e.g. HDD, SSD) in the infrastructure.                                                                             |
| Host                | A physical machine in the infrastructure providing computational, storage and/or network connectivity capabilities.                      |
| Cyber attack/threat | Attacks on the infrastructure through the means of electronic access.                                                                    |

## Context

Some standards provided by the SCS project will talk about or require procedures to back up resources or have redundancy for resources.
This decision record should discuss, which failure threats exist within an IaaS and KaaS deployment and will classify them into several levels according to their impact and possible handling mechanisms.
In consequence these levels should be used in standards concerning redundancy or failure safety.

Based on our research, no similar standardized classification scheme seems to exist currently.
Something close but also very detailed is the [BSI-Standard 200-3 (german)][bsi-200-3] published by the German Federal Office for Information Security.
As we want to focus on IaaS and K8s resources and also have an easily understandable structure that can be applied in standards covering replication, redundancy and backups, this document is too detailed.

<!--
TODO: goals vs. non-goals
TODO: Resolve confusion between high availability vs. disaster recovery vs. redundancy vs. backups
TODO: What time frame do we look at? (so called Recovery Time Objecte aka RTO)
TODO: how does this relate to Business Continuity Planning (BCP)
-->

### Goal of this Decision Record

The SCS wants to classify levels of failure cases according to their impact and the respective measures CSPs can implement to prepare for each level.
Standards that deal with redundancy or backups or recovery SHOULD refer to the levels of this standard.
Thus every reader knows, up to which level of failsafeness the implementation of the standard works.
Reader then should be able to abstract what kind of other measures they have to apply, to reach the failsafe lavel they want to reach.

### Differentiation between failsafe levels and high availability, disaster recovery, redundancy and backups

The levels auf failsafeness that are defined in this decision record are classifying the possibilities and impacts of failure cases (such as data loss) and possible measures.
High Availability, disaster recovery, redundancy and backups are all measures that can and should be applied to IaaS and KaaS deployments by both CSPs and Users to reduce the possibility and impact of data loss.
So with this document every reader can see to what level of failsafeness their measures protect user data.

To differentiate also between the named measures the following table can be used:

| Term               | Explanation                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| High Availability  | Refers to the availability of resources over an extended period of time unaffected by smaller hardware issues. E.g. achievable through having several instances of resources.      |
| Disaster Recovery  | Measures taken after an incident to recover data, IaaS resource and maybe even physical resources.                                                                                 |
| Redundancy         | Having more than one (or two) instances of each resource, to be able to switch to the second resource (could also be a data mirror) in case of a failure.                          |
| Backup             | A specific copy of user data, that presents all data points at a givne time. Usually managed by users themself, read only and never stored in the same place as the original data. |

### Failsafe Levels and RTO

As this documents classifies failure case with very broad impacts and it is written in regards of mostly IaaS and KaaS, there cannot be one simple RTO set.
It should be taken into consideration that the RTO for IaaS and KaaS means to make user data available again through measures within the infrastructure.
But this will not be effective, when there is no backup of the user data or a redundancy of it already in place.
The different failsafe levels, measures and impacts will lead to very different RTOs.
For example a storage disk that has a failure will result in an RTO of 0 seconds, when the storage backend uses internal replication and still has two replicas of the user data.
While in the worst case of a natural disaster, most likely a severe fire, the whole deployment will be lost and if there were no off-site backups done by users there will be no RTO, because the data cannot be recovered anymore.

[bsi-200-3]: https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_3.pdf?__blob=publicationFile&v=2

## Decision

### Failsafe Levels

This Decision Record defines **four** failsafe levels, each of which describe what kind of failures have to
be tolerated by a provided service.

:::caution

This table only contains examples of failure cases.
This should not be used as a replacement for a risk analysis.

:::

In general, the lowest, **level 1**, describes isolated/local failures which can occur very frequently, whereas
the highest, **level 4**, describes relatively unlikely failures that impact a whole or even multiple datacenter(s):

| Level | Probability | Impact                | Examples |
| -     | -           | -                     | -       |
| 1     | Very High   | small Hardware Issue  | Disk failure, RAM failure, small software bug |
| 2     | High        | Rack-wide             | Rack outage, power outage, small fire |
| 3     | Medium      | site-wide (temporary) | Regional power outage, huge fire, orchestrated cyber attack |
| 4     | Low         | site destruction      | Natural disaster |

For example, a provided service with failsafe level 2 tolerates a rack outage (because there is some kind of
redundancy in place.)

There are some *general* consequences, that can be addressed by CSPs and users in the following ways:

| Level | consequences for CSPs | consequences for Users |
|---|-----|-----|
| 1. Level | CSPs MUST operate replicas for important components (e.g. replicated volume back-end, replicated database, ...). | Users SHOULD backup their data themself and place it on an other host. |
| 2. Level | CSPs MUST have redundancy for important components (e.g. HA for API services, redundant power supply, ...). | Users MUST backup their data themselves and place it on an other host. |
| 3. Level | CSPs SHOULD operate hardware in dedicated Availability Zones. | Users SHOULD backup their data, in different AZs or even other deployments. |
| 4. Level | CSPs may not be able to save user data from such catastrophes. | Users MUST have a backup of their data in a different geographic location. |

:::caution

The columns **consequences for CSPs / Users** only show examples of actions that may provide this class of failure safety for a certain resource.
Customers should always check, what they can do to protect their data and not rely solely on the CSP.

:::

More specific guidance on what these levels mean on the IaaS and KaaS layers will be provided in the sections
further down.
But beforehand, we will describe the considered failure scenarios and the resources that may be affected.

### Failure Scenarios

The following failure scenarios have been considered for the proposed failsafe levels.
For each failure scenario, we estimate the probability of occurence and the (worst case) damage caused by the scenario.
Furthermore, the corresponding minimum failsafe level covering that failure scenario is given.

<!--
TODO: define the meaning of our probabilities
-->

#### Hardware Related

| Failure Scenario | Probability | Consequences | Failsafe Level Coverage |
|----|-----|----|----|
| Disk Failure | High | Permanent data loss in this disk. Impact depends on type of lost data (data base, user data) | L1 |
| Host Failure (without disks) | Medium to High | Permanent loss of functionality and connectivity of host (impact depends on type of host) | L1 |
| Host Failure | Medium to High | Data loss in RAM and temporary loss of functionality and connectivity of host (impact depends on type of host) | L1 |
| Rack Outage | Medium | Outage of all nodes in rack | L2 |
| Network router/switch outage | Medium | Temporary loss of service, loss of connectivity, network partitioning | L2 |
| Loss of network uplink | Medium | Temporary loss of service, loss of connectivity | L3 |
| Power Outage (Data Center supply) | Medium | Temporary outage of all nodes in all racks | L3 |

#### Environmental

Note that probability for these scenarios is dependent on the location.

| Failure Scenario | Probability | Consequences | Failsafe Level Coverage |
|----|-----|----|----|
| Fire | Medium | permanent Disk and Host loss in the affected zone | L3 |
| Flood | Low | permanent Disk and Host loss in the affected region | L4 |
| Earthquake | Very Low | permanent Disk and Host loss in the affected region | L4 |
| Storm/Tornado | Low | permanent Disk and Host loss in the affected region | L4 |

As we consider mainly deployments in central Europe, the probability of earthquakes is low and in the rare case of such an event the severity is also low compared to other regions in the world (e.g. the pacific ring of fire).
The event of a flood will most likely come from overflowing rivers instead of storm floods from a sea.
There can be measures taken, to reduce the probability and severity of a flooding event in central Europe due to simply choosing a different location for a deployment.

#### Software Related

| Failure Scenario | Probability | Consequences | Failsafe Level Coverage |
|----|-----|----|----|
| Software bug (major) | Low | permanent loss or compromise of data that trigger the bug up to data on the whole physical machine | L3 |
| Software bug (minor) | High | temporary or partial loss or compromise of data | L1 |

Many software components have lots of lines of code and cannot be proven correct in their whole functionality.
They are tested instead with at best enough test cases to check every interaction.
Still bugs can and will occur in software.
Most of them are rather small issues, that might even seem like a feature to some.
An exmple for this would be: [whether a floating IP in OpenStack could be assigned to a VM even if it is already bound to another VM](https://bugs.launchpad.net/neutron/+bug/2060808).
Bugs like this do not affect a whole deployment, when they are triggered, but just specific data or resources.
Nevertheless those bugs can be a daily struggle.
This is the reason, the probability of such minor bugs may be pretty high, but the consequences would either be just temporary or would only result in small losses or compromisation.

On the other hand major bugs, which might be used to compromise data, that is not in direct connection to the triggered bug, occur only a few times a year.
This can be seen e.g. in the [OpenStack Security Advisories](https://security.openstack.org/ossalist.html), where there were only 3 major bugs found in 2023.
While these bugs might appear only rarely their consequences are immense.
They might be the reason for a whole deployment to be compromised or shut down.
CSPs should be in contact with people triaging and patching such bugs, to be informed early and to be able to update their deployments, before the bug is openly announced.

#### Human Interference

| Failure Scenario | Probability | Consequences | Failsafe Level Coverage |
|----|-----|----|----|
| Minor operating error | High | Temporary outage | L1 |
| Major operating error | Low | Permanent loss of data | L3 |
| Cyber attack (minor) | High | permanent loss or compromise of data on affected Disk and Host | L1 |
| Cyber attack (major) | Medium | permanent loss or compromise of data on affected Disk and Host | L3 |

Mistakes in maintaining a data center will always happen.
To reduce the probability of such a mistake, measures are needed to reduce human error, which is more an issue of sociology and psychology instead of computer science.
On the other side an attack on an infrastructure cannot be avoided by this.
Instead every deployment needs to be prepared for an attack all the time, e.g. through security updates.
The severity of Cyber attacks can also vary broadly: from denial-of-service attacks, which should only be a temporary issue, up until coordinated attacks to steal or destroy data, which could also affect a whole deployment.
The more easy an attack is, the more often it will be used by various persons and organizations up to be just daily business.
Major attacks are often orchestrated and require speicif knowledge e.g. of Day-0 Bugs or the attacked infrastructure.
Due to that nature their occurance is less likely, but the damage done can be far more severe.

## Consequences

Using the definition of levels established in this decision record throughout all SCS standards would allow readers to understand up to which level certain procedures or aspects of resources (e.g. volume types or a backend requiring redundancy) would protect their data and/or resource availability.

### Affected Resources

#### IaaS Layer (OpenStack Resources)

| Resource           | Explanation                                                                                                                              | Affected by Level |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| Ephemeral VM       | Equals the `server` resource in Nova, booting from ephemeral storage.                                                                    | L1, L2, L3, L4    |
| Volume-based VM    | Equals the `server` resource in Nova, booting from a volume.                                                                             | L2, L3, L4        | 
| Ephemeral Storage  | Disk storage directly supplied to a virtual machine by Nova. Different from volumes.                                                     | L1, L2, L3, L4    |
| Ironic Machine     | A physical host managed by Ironic or as a `server` resource in Nova.                                                                     | L1, L2, L3, L4    |
| (Glance) Image     | IaaS resource usually storing raw disk data. Managed by the Glance service.                                                              | (L1), L2, L3, L4  |
| (Cinder) Volume    | IaaS resource representing block storage disk that can be attached as a virtual disk to virtual machines. Managed by the Cinder service. | (L1, L2), L3, L4  |
| (Volume) Snapshot  | Thinly-provisioned copy-on-write snapshots of volumes. Stored in the same Cinder storage backend as volumes.                             | (L1, L2), L3, L4  |
| Volume Type        | Attribute of volumes determining storage details of a volume such as backend location or whether the volume will be encrypted.           | L3, L4            |
| (Barbican) Secret  | IaaS resource storing cryptographic assets such as encryption keys. Managed by the Barbican service.                                     | L3, L4            |
| Key Encryption Key | IaaS resource, used to encrypt other keys to be able to store them encrypted in a database.                                              | L3, L4            |
| Floating IP        | IaaS resource, an IP that is usually routed and accessible from external networks.                                                       | L3, L4            |

#### KaaS Layer (Kubernetes Resources)

A detailed list of consequnces for certain failures can be found in the [Kubernetes docs](https://kubernetes.io/docs/tasks/debug/debug-cluster/).
The following table gives an overview about certain resources on the KaaS Layer and in which failsafe classes they are affected:

| Resource(s)        | Explanation                                                                                                                              | Affected by Level |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| Pod                | Kubernetes object that represents a workload to be executed, consisting of one or more containers.                                       | ???               |
| Container          | A lightweight and portable executable image that contains software and all of its dependencies.                                          | ???               |
| Deployment, StatefulSet | Kubernetes objects that manage a set of Pods.                                                                                       | ???               |
| Job                | Application workload that runs once.                                                                                                     | ???               |
| CronJob            | Application workload that runs once, but repeatedly at specific intervals.                                                               | ???               |
| ConfigMap, Secret  | Objects holding static application configuration data.                                                                                   | ???               |
| Service            | Makes a Pod's network service accessible inside a cluster.                                                                               | ???               |
| Ingress            | Makes a Service externally accessible.                                                                                                   | ???               |
| PersistentVolumeClaim (PVC) | Persistent storage that can be bound and mounted to a pod.                                                                      | ???               |

Also see [Kubernetes Glossary](https://kubernetes.io/docs/reference/glossary/).

## Old sections

### Impact of the Failure Scenarios

These failure scenarios can result in temporary (T) or permanent (P) loss of the resource or data within.
Additionally, there are a lot of resources in IaaS alone that are more or less affected by these failure scenarios.
The following tables shows the impact **when no redundancy or failure safety measure is in place**, i.e., when
**not even failsafe level 1 is fulfilled**.

TODO: why should we do that?

#### Impact on OpenStack Resources (IaaS layer)

TODO: this table is getting difficult to maintain

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

For some cases, this only results in temporary unavailability and cloud infrastructures usually have certain mechanisms in place to avoid data loss, like redundancy in storage backends and databases.
So some of these outages are easier to mitigate than others.

#### Impact on Kubernetes Resources (KaaS layer)

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

