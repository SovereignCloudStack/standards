---
title: Decisions for the Volume Type Standard
type: Decision Record
status: Draft
track: IaaS
---

## Introduction

Volumes in OpenStack are virtual drives. They are managed by the storage service Cinder, which abstracts creation and usage of many different storage backends. While it is possible to use a backend like lvm which can reside on the sam host as the hypervisor, the SCS wants to make a more clear differenciation between volumes and the ephemeral storage of a virtual machine. For all SCS deployments we want to assume that volumes are always residing in a storage backend that is NOT on the same host as a hypervisor - in short terms: Volumes are network storage. Ephemeral storage on the other hand is the only storage residing on a compute host. It is created by creating a VM directly from an Image and is automatically los as soon as the VM cease to exist. Volumes on the other hand have to be created from Images and only after that can be used for VMs. They are persistant and will remain in the last state a VM has written on them before they cease to exit. Being persistant and not relying on the host where the VM resides, Volumes can easily be attached to another VM in case of a node outage and VMs be migrated way more easily, because only metadata and data in RAM has to be shifted to another host, accelerating any migration or evacuation of a VM.

Volume Types are used to classify volumes and provide a basic decision for what kind of volume should be created. These volume types can sometimes very be backend-specific and it might be hard for a user to choose the most suitable volume type, if there is more than one default type. Nevertheless the most of configuration is done in the backends themself, so volume types only work as a rough classification.

## Motivation

We want to standardize a few varieties of volume types. While a user can choose simple things like size when creating a volume, Volume Types define a few broader aspects of volume. Encryption of volumes for example is solely decided by the volume type. And whether the volume will be replicated is a mix between definiton in the volume type and backend specific configuration, but it's visiblity can only be reached in the volume type.

In General: what the different volume types are capable of is highly dependend on both the used backend and the configurations of OpenStack. A few options are worth being at least recommended.

## Design Considerations

We want to have a discoverable Standard. So there should be no naming conventions as per request by operators.

This first decision will have impacts on upstream OpenStack development, as those things, that would be nice to discover, may not be currently dicoverable by users or not at all.

There are severel aspects of volume types, which will be discussed in the following:

### Options considered

#### Encryption

Encryption for volumes is an option which has to be configured within the volume type. As an admin it is possible to set encryption-provider, key size, cipher and control location. As an admin it is also currently possible to see these configurations in a volume type with list and show commands. A user should not see these parameters in detail, but a boolean value that descibes whether encryption is used or not. Currently this is not possible in upstream OpenStack.

**Conclusion**: This is a solid aspect to be standardized. But it will need work on OpenStack, to have a boolean value presented to the users.

#### Backend Name

OpenStack Cinder works with a lot of different backends. They all have some kind of special features, which might be attractive for a user. But showing the name of the backend to users is also considered a security risk by Cinder developers. Overall it is always an option to make users aware of special features through the name and description of a volume type and sometimes even through extra_specs.

**Conclusion**: This should not be standardized.

#### Availability Zones

Availability Zones are used in Nova and Cinder seperatly to provide an often also physical separation of compute hosts or storage nodes. This leads to two options to consider:

1. Multiple Volume AZs: This might be used if there are different backends present in one IaaS structure. The different volume types are usually used for the different volume AZs. This makes migration between those AZs only be possible for administrators.

2. Volume Types that can be attached to multiple Nova Azs: This option can be seen in the extra specs of a volume type also by normal users. Another option is to use backend specific options, as for example with ceph that directly interacts with nova for this. In that case there will not be any visible extra specs for the users.

Another question is how many providers use one of these options or both.

**Conclusion**: The first part doesn't make much sense to standardize, as migration between the volume types can only be done by admins. However the second part might be noteable, but due to the variety of configuration options very hard to standardize.

#### Multiattach

It is possible in a few backends to attach a volume to multiple VMs. This has to be configured in the Volume Type and this information is also accessable for users. Nevertheless this option also needs a lot of work from users, as those types of volumes have to have a file system, that is capable of multiattach. Many providers don't provide multiattach.

**Conclusion**: It might be noteable, that this already is a discoverable option.

#### Replication

Replication states, whether or not there are multiple replicas of a volume. Thus answers the question, whether the data could survive a node outage. Again there are different ways to achive replicated volumes. It can either be defined in the volume type and is discoverable also by normal users or it is configured in the backend. The last option is usually used with ceph for example. This makes it hard to discover, whether a volume is replicated or not. Another point is the number of replicas, that exist.

**Conclusion**: Replication is a good option to be standardized. Whether this should be done as a boolean option or if the number of replicas is also something users need to know should still be discussed. Nevertheless due to the different options to configure replication this will be quite complex.

#### QoS

Quality of Service parameters can be stated in a volume qos object. These objects can then be associated to a volume type (or directly to a volume as an admin only option). But this is optional and thus even good or very good volume QoS parameters that are aquired through hardware configuration and storage parameters, might go by unmentioned.
Furthermore the indirection makes it harder to discover the qos for a volume type. Only admins will see the associated qos ID and will have to take a closer look at the qos after discovering the volume type. PLUS: there can only be one qos association for one volume type. But a qos can be used for multiple volumes.

**Conclusion**: The benefit of displaying qos parameters is clear, thus this option should be noted. But are volume qos objects widely used? If not, standardization process would be too much work.

#### Other Backend-specific Highlights

While every option above described things, that can at least be partly or for admins only visible in volume types, there are many different configuration options in hardware and backend providers can make use of. It is sadly not possible to get them into the volume type directly, but we recommend, that notable configurations are written into the description of a volume type to achieve transparency for the users.

## Open questions

1. How often are the different options used by providers and users respectively? Especially important for qos and replication!
2. Regarding Replication: Is the number of replicas needed by users and is it okay for providers to provide this information?

## Decision

| Aspect | Standardize? | Discoverability | other Things |
| ---- | ---- | ---- | ------ |
| encryption | **Recommended** | work needed | extra_spec: encrypted=True/False |
| Backend name | - | - | - |
| AZs | - | - | describe as optional and backend-dependend |
| multiattach | - | yes | describe as optional |
| Replication | **Recommended** | lot of work | either get from backend to OS or as extra_spec defined by deployer |
| Number of Replicas, etc | ? | lot of work | optional, work on it after Replication is standardized |
| Volume QoS | ? | admin only | needs further discussion, should be at least described as optional |

## Related Documents

[This is an etherpad](https://input.scs.community/JnaY5i70R_yc7JkSNVtlKQ) with a further look into the Options and a few examples.
