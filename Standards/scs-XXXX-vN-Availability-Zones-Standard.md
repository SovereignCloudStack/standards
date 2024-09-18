---
title: Availability Zones Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

On the IaaS level especially in OpenStack it is possible to group resources in Availability Zones.
Such Zones often are mapped to the physical layer of a deployment, such as e.g. physical separation of hardware or redundancy of power circuits or fire zones.
But how CSPs apply Availability Zones to the IaaS Layer in one deplyoment may differ widely.
Therefore this standard will address the minimal requirements that need to be met, when creating Avaiability Zones.

## Terminology

| Term               | Explanation                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Availability Zone  | (also: AZ) internal representation of physical grouping of service hosts, which also lead to internal grouping of resources.             |
| Fire Zone          | A physical separation in a data center that will contain fire within it. Effectively stopping spreading of fire.                         |
| PDU                | Power Distribution Unit, used to distribute the power to all physical machines of a single server rack.                                  |
| Compute            | A generic name for the IaaS service, that manages virtual machines (e.g. Nova in OpenStack).                                             |
| Network            | A generic name for the IaaS service, that manages network resources (e.g. Neutron in OpenStack).                                         |
| Storage            | A generic name for the IaaS service, that manages the storage backends and virtual devices (e.g. Cinder in OpenStack).                   |
| BSI                | German Federal Office for Information Security (Bundesamt für Sicherheit in der Informationstechnik)                                     |
| CSP                | Cloud Service Provider, provider managing the OpenStack infrastructure.                                                                  |

## Motivation

Redundancy is a non-trivial but relevant issue for a cloud deployment.
First and foremost it is necessary to increase failure safety through redundancy on the physical layer.
The IaaS layer as the first abstraction layer from the hardware has an important role in this topic, too.
The grouping of redundant physical resources into Availability Zones on the IaaS level, gives customers the option to distribute their workload to different AZs which will result in a better failure safety.
While CSPs already have some similarities in their grouping of physical resources to AZs, there are also differences.
This standard aims to reduce those differences and will clarify, what customers can expect from Availability Zones in IaaS.

Availability Zones in IaaS can be set up for Compute, Network and Storage separately while all may be referring to the same physical separation in a deployment.
This standard elaborates the necessity of having Availability Zones for each of these classes of resources.
It will also check the requirements customers may have, when thinking about Availability Zones in relation to the taxonomy of failure safety levels [^1].
The result should enable CSPs to know when to create AZs to be SCS-compliant.

## Design Considerations

Availability Zones should represent parts of the same physical deployment that are independent of each other.
The maximum level of physical independence is achieved through putting physical machines into different fire zones.
In that case a failure case up to level 3 as described in the taxonomy of failure safety levels document[^1] will not lead to a complete outage of the deployment.

Having Availability Zones represent fire zones will also result in AZs being able to take workload from another AZ in a Failure Case of Level 3.
So that even the destruction of one Availability Zone will not automatically include the destruction of the other AZs.

:::caution

Even with fire zones being physically designed to protect parts of a data center from severe destruction in case of a fire, this will not always succeed.
Availability Zones in Clouds are most of the time within the same physical data center.
In case of a big catastrophe like a huge fire or a flood the whole data center could be destroyed.
Availability Zones will not protect customers against these failure cases of level 4 of the taxonomy of failure safety[^1].

:::

Smaller deplyoments like edge deployments may not have more than one fire zone in a single location.
To include such deployments, it should not be required to use Availability Zones.

Other physical factors that should be considered are the power supplies, internet connection, cooling and core routing.
Availability Zones were also used by CSPs as a representations of redundant PDUs.
That means there are deployments, which have Availability Zones per rack as each rack has it's own PDU and this was considered to be the single point of failure an AZ should represent.
While this is also a possible measurement of independency it only provides failure safety for level 2.
Therefore this standard should be very clear about which independency an AZ should represent and it should not be allowed to have different deployments with their Availability Zones representing different levels of failure safety.

Additionally Availability Zones are available for Compute, Storage and Network services.
They behave differently for each of these resources and also when working across resource-based Availability Zones, e.g. attaching a volume from one AZ to a virtual machine in another AZ.
For each of these IaaS resource classes, it should be defined, under which circumstances Availability Zones should be used.

[^1]: [Taxonomy of Failsafe Levels in SCS (TODO: change link as soon as taxonomy is merged)](https://github.com/SovereignCloudStack/standards/pull/579)

### Scope of the Availability Zone Standard

When elaborating redundancy and failure safety in data centers, it is necessary to also define redundancy on the physical level.
There are already recommendations from the BSI for physical redundancy within a cloud deployment [^2].
This standard considers these recommendation as a basis, that is followed by most CSPs.
So this standard will not go into details, already provided by the CSP, but will rather concentrate on the IaaS layer and only have a coarse view on the physical layer.
The first assumtion from the recommendations of the BSI is that the destruction of one fire zone will not lead to an outage of all power lines (not PDUs), internet connections, core routers or cooling systems.

For the setup of Availability Zone this means, that within every AZ, there needs to be redundancy in core routers, internet connection, power lines and at least two separate cooling systems.
This should avoid having single points of failure within the Availability Zones.
But all this physical infrastructure can be the same over all Availability Zones in a deployment, when it is possible to survive the destruction of one fire zone.

[^2]: [Availability recommendations from the BSI](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/RZ-Sicherheit/RZ-Verfuegbarkeitsmassnahmen.pdf?__blob=publicationFile&v=9)

### Options considered

#### Physical-based Availability Zones

It is possible standardize the usage of Availability Zones over all IaaS resources.
The downside from this is, that the IaaS resources behave so differently, that they have different requirements for redundancy and thus Availability Zones.
This is not the way to go.
Besides that, it is already possible to create two physically separated deployments close to each other, connect them with each other and use regions to differ between the IaaS on both deployments.

The question that remains is, what an Availability Zone should consist of?
Having one Availability Zone per fire zone gives the best level of failure safety, that can be achieved by CSPs.
When building up on the relation between fire zone and physical redundancy recommendations as from the BSI, this combination is a good starting point, but need to be checked for the validity for the different IaaS resources.

Another point is where Availability Zones can be instantiated and what the connection between AZs should look like.
To have a proper way to deal with outages of one AZ, where a second AZ can step in, a few requirements need to be met for the connection between those two AZs.
The amount data that needs to be transferred very fast in a failure case may be enormous, so there is a requirement for a high bandwidth between connected AZs.
Tho avoid additional failure cases the latency between those two Availability Zones need to be low.
With such requirements it is very clear that AZs should only reside within one (physical) region of an IaaS deployment.

#### AZs in Compute

Compute Hosts are physical machines on which the compute service runs.
A single virtual machine is always running on ONE compute host.
Redundancy of virtual machines is either up to the layer above IaaS or up to the customers themself.
Having Availability Zones gives customers the possibility to let another virtual machine as a backup run within another Availability Zone.

Customers will expect that in case of the failure of one Availability Zone all other AZs are still available.
The highest possible failure safety here is achieved, when Availability Zones for Compute are used for different fire zones.

When the BSI recommendations are followed, there should already be redundancy in power lines, internet connection and cooling.
An outage of one of these physical resources will not affect the compute host and its resources for more than a minimal timeframe.
But when a single PDU is used for a rack, a failure of that PDU will result in an outage of all compute hosts in this rack.
In such a case it is not relevant, whether this rack represents a whole Availability Zone or is only part of a bigger AZ.
All virtual machines on the affected compute hosts will not be available and need to be restarted on other hosts, whether of the same Availability Zone or another.

#### AZs in Storage

There are many different backends used for the storage service with Ceph being one of the most prominent backends.
Configuring those backends can already include to span one storage cluster over physical machines in different fire zones.
In combination with internal replication a configuration is possible, that already distributes replicas from volumes over different fire zones.
When a deployment has such a configured storage backend, it already can provide safety in case of a failure of level 3.

Using Availability Zones is also possible for the storage service, but configuring AZs, when having a configuration like above will not increase safety.
Nevertheless using AZs when having different backends in different fire zones will give customers a hint to backup volumes into storages of other AZs.

Additionally when the BSI recommendations are followed, there should already be redundancy in power lines, internet connection and cooling.
An outage of one of these physical resources will not affect the storage host and its resources for more than a minimal timeframe.
When internal replication is used, either through the IaaS or through the storage backend itself, the outage of a single PDU and such a single rack will not affect the availability of the data itself.
All these physical factors are not requiring the usage of an Availability Zone for Storage.
An increase of the level of failure safety will not be reached through AZs in these cases.

Still it might be confusing when having deployments with compute AZs but without storage AZs.
CSPs may need to communicate clearly up to which failure safety level their storage service can automatically have redundancy and from which level customers are responsible for the redundancy of their data.

#### AZs in Network

Virtualized network resources can typically be quickly and easily set up from building instructions.
Those instructions are stored in the database of the networking service.

If a physical machine, on which certain network resources are set up, is not available anymore, the resources can be rolled out on another physical machine, without being depended on the current situation of the lost resources.
There might only be a loss of a few packets within the affected network resources.

With having Compute and Storage in a good state (e.g. through having fire zones with a compute AZ each and storage being replicated over the fire zones) there would be no downsides to omitting Availability Zones for the network service.
It might even be the opposite: Having resources running in certain Availability Zones might prevent them from being scheduled in other AZs[^3].
As the network resources like routers are bound to an AZ, in a failure case of one AZ all resource definitions might still be there in the database, while the implementation of those resources is gone.
Trying to rebuild them in another AZ is not possible, because the scheduler will not allow them to be implemented in another AZ, then the one thats present in their definition.
In a failure case of one AZ this might lead to a lot of manual work to rebuild the SDN from scratch instead of just re-using the definitions.

Because of this severe sideeffect, this standard will make no recommendations about Network AZs.

[^3]: [Availability Zones in Neutron for OVN](https://docs.openstack.org/neutron/latest/admin/ovn/availability_zones.html)

### Cross-Attaching volumes from one AZ to another compute AZ

Without the networking AZs we only need to take a closer look into attaching volumes to virtual machines across AZs.

When there is more than one Storage Availability Zone, those AZs do normally align with the Compute Availability Zones.
This means that fire zone 1 contains compute AZ 1 and storage AZ 1 , fire zone 2 contains compute AZ 2 and storage AZ 2 and the same for fire zone 3.
It is possible to allow or forbid cross-attaching volumes from one storage Availability Zone to virtual machines in another AZ.
If it is not allowed, then the creation of volume-based virtual machines will fail, if there is no space left for VMs in the corresponding Availability Zone.
While this may be unfortunate, it gives customers a very clear picture of an Availability Zone.
It clarifies that having a virtual machine in another AZ also requires having a backup or replication of volumes in the other storage AZ.
Then this backup or replication can be used to create a new virtual machine in the other AZ.

It seems to be a good decision to not encourage CSPs to allow cross-attach.
Currently CSPs also do not seem to widely use it.

## Standard

If Compute Availability Zones are used, they MUST be in different fire zones.
Availabilty Zones for Storage SHOULD be setup, if there is no storage backend used that can span over different fire zones and automatically replicate the data.
Otherwise a single Availabilty Zone for Storage SHOULD be configured.

If more than one Availability Zone for Storage is set up, the attaching of volumes from one Storage Availability Zone to another Compute Availability Zone (cross-attach) SHOULD NOT be possible.

Within each Availability Zone:

- there MUST be redundancy in power supply, as in line into the deployment
- there MUST be redundancy in external connection (e.g. internet connection or WAN-connection)
- there MUST be redundancy in core routers
- there SHOULD be redundancy in the cooling system

AZs SHOULD only occur within the same region and have a low-latency interconnection with a high bandwidth.

## Related Documents

The taxonomy of failsafe levels can be used to get an overview over the levels of failure safety in a deployment(TODO: link after DR is merged.)

The BSI can be consulted for further information about [failure risks](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/Kompendium/Elementare_Gefaehrdungen.pdf?__blob=publicationFile&v=4), [risk analysis for a datacenter](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_3.pdf?__blob=publicationFile&v=2) or [measures for availability](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/RZ-Sicherheit/RZ-Verfuegbarkeitsmassnahmen.pdf?__blob=publicationFile&v=9).

## Conformance Tests

As this standard will not require Availability Zones to be present, we cannot automatically test the conformance.
The other parts of the standard are physical or internal and could only be tested through an audit.
Whether there are fire zones physically available is a criteria that will never change for a single deployment - this only needs to be audited once.
It might be possible to also use Gaia-X Credentials to provide such information, which then could be tested.
