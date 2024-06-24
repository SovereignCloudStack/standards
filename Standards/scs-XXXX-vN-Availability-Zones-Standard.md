---
title: Availability Zones Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

On the IaaS-Level especially in OpenStack it is possible to group resources in Availability Zones.
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

## Motivation

Redundancy is a non-trivial but relevant issue for a cloud deployment.
The IaaS layer especially as the first virtualization from the hardware has an important role in this topic, because it is possible to provide failure safety through redundancy from failures on the physical layer.
The grouping of physical resources into Availability Zones on the IaaS level, gives customers the option to distribute their workload to different AZs which will result in a better failure safety.
While CSPs already have some similarities in their grouping of physical resources to AZs, there are also differences.
Availability Zones can be set up for Compute, Network and Storage while all refering to the same physical separation in a deployment.
This standard elaborates the necessity of having Availability Zones for each of these classes.
It will also check the requirement customers may have, when thinking about Availability Zones in regarding of the taxonomy of failure safety levels [^1].
The result should enable CSPs to know when to create AZs to be SCS-compliant.

## Design Considerations

Availability Zones should represent parts of the same deployment, that have an independency of each other.
The maximum of physical independency is achieved through putting physical machines into different fire zones.
In that case a failure case up to level 3 as described in the taxonomy of failure safety levels document[^1] will not lead to a complete outage of the deployment.

Having Availability Zones represent fire zones will also result in AZs being to take workload from another AZ in a Failure Case of Level 3.
So that even the destruction of one Availability Zone will not automatically include the destruction of the other AZs.

Smaller deplyoments like edge deployments may not have more than one fire zone in a single location.
To include such deployments, it should not be required to use Availability Zones.

Other physical factors that should be considered are the power supplies, internet connection, cooling and core routing.
Availability Zones have been also being configured to show redundancy in e.g. Power Supply as in the PDU.
That means there are deployments, which have Availability Zones per rack as each rack has it's own PDU and this was considered to be the single point of failure an AZ should represent.
While this is also a possible measurement of independency it only provides failure safty for level 2.
Therefore this standard should be very clear about which independency an AZ should represent and it should not be allowed to have different deployments with their Availability Zones representing different levels of failure safety.

There are recommendations from the BSI for physical redundancy within a cloud deployment [^2].
This standard considers these recommendation ar followed by most CSPs and will thus be a basis for all data centers.
From this recommendations this standard assumes that the destruction of one fire zone will not lead to an outage of all power lines (not PDUs), internet connections, core routers or cooling systems.

For the setup of Availability Zone this means, that within every AZ, there needs to be redundancy in core routers, internet connection, power lines and at least two separate cooling systems to avoid single points of failure in Availability Zones.
But all this physical infrastructure can be the same over all Availability Zones in a deployment, when it is possible to survive the destruction of one fire zone.

Additionally Availability Zones are available for Compute, Storage and Network services.
They behave differently for each of these resources and also when working across resource-based Availability Zones, e.g. attaching a volume from one AZ to a virtual machine in another AZ.

[^2]: [Availability recommendations from the BSI](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/RZ-Sicherheit/RZ-Verfuegbarkeitsmassnahmen.pdf?__blob=publicationFile&v=9)

### Options considered

#### Physical-based Availability Zones

It is possible standardize the Usage of Availability Zones over all IaaS resources.
The downside from this is, that the IaaS resources behave so differently, that they have different requirements for redundancy and thus Availability Zones.
This is not the way to go.

The question that remains is, what an Availability Zone should consist of?
Having one Availability Zone per fire zone gives the best level of failure safety, that can be achieved by CSPs.
When building up on the relation between fire zone and physical redundancy recommendations as from the BSI, this combination is a good starting point, but need to be checked for the validity for the different IaaS resources.

Another point is where Availability Zones can be instanciated and what the connection between AZs should look like.
To have a proper way to deal with outages of one AZ, where a second AZ can step in, a few requirements need to be met for the connection between those two AZs.
The amount data that needs to be transferred very fast in a failure case may be enormous, so there is a requirement for a high bandwidth between connected AZs.
Tho avoid additional failure cases the latency between those two Availability Zones need to be low.
With such requirements it is very clear that AZs should only reside within one (physical) region of an IaaS-Deployment.

#### AZs in Compute

Compute Hosts are physical machines on which the compute service runs.
A single virtual machine is always running on ONE compute host.
Redundancy of virtual machines is either up to the layer above IaaS or up to the customers themself.
Having Availability Zones gives customers the possibility to let another virtual machine as a backup run within another Availability Zone.

Customers will expect that in case of the failure of one Availability Zone all other AZs are still available.
The highest possible failure safety here is achieved, when Availability Zones for Compute are used for different fire Zones.

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

Using Availability Zone is also possible for the storage service, but configuring AZs, when having a configuration like above will not increase safety.
Nevertheless using AZs when having different backends in different fire zones will give customers a hint to backup volumes into storages of other AZs.

Additionally when the BSI recommendations are followed, there should already be redundancy in power lines, internet connection and cooling.
An outage of one of these physical resources will not affect the storage host and its resources for more than a minimal timeframe.
When internal replication is used, either through the IaaS or through the storage backend itself, the outage of a single PDU and such a single rack will not affect the availability of the data itself.
All these physical factors are not requiring the usage of an Availability Zone for Storage.
An increase of the level auf failure safety will not be reached through AZs in these cases.

Still it might be confusing when having deployments with compute AZs but without storage AZs.
CSPs may need to communicate clearly up to which failure safety level their storage service can automatically have redundancy and from which level customers are responsible for the redundancy of their data.

#### AZs in Network

Network resources can be typically fastly and easily set up from building instruction.
Those instructions are stored in the database of the networking service.

If a physical machine, on which certain network resources are set up, is not available anymore, the resources can be rolled out on another physical machine, without being depended on the current situation of the lost resources.
There might only be a loss of a few packages within the los network ressources.

With having Compute and Storage in a good state (e.g. through having fire zones with a compute AZ each and storage being replicated over the fire zones) it would not have downsides to not have Availability Zones for the network service.
It might even be the opposite: Having resources running in certain Availability Zones might permit them from being scheduled in other AZs[^3].
This standard will therefore make no recommendations about Network AZs.

[^3]: [Availability Zones in Neutron for OVN](https://docs.openstack.org/neutron/latest/admin/ovn/availability_zones.html)

### Open questions

Without the networking AZs we only need to take a closer look into attaching volumes to virtual machines across AZs.

It is possible to allow or forbid cross-attaching volumes from one AZ to virtual machines in another AZ.
If it is not allowed, then the creation of volume-based virtual machines will fail, in case of an outage of a complete Availability Zone.
This does not seem to be a good option in regard for the failure safety level, as transfering a virtual machine from one AZ to another in a failure case will get way more complex.
A replication of the volume has to be present in another storage Availability Zone that can be attached to the corresponding compute Availability Zone, which is not the AZ, that has an outage.
Then this replication - maybe a snapshot - can be used to create a new virtual machine.

While it seems to be a good decision to allow cross-attach, CSPs currently do not seem to widely use it.
The reasons for and against this configuration may need to be discussed further to decide, whether this standard should make any recommendations regarding cross-attach.

## Standard

Compute Availability Zone MUST be in different fire zones.
Availabilty Zones for Storage SHOULD be setup, if there is no storage backend used that can span over different fire zones and automatically replicate the data.

[TO BE DISCUSSED:] If Availability Zones for Storage are used, the attaching of volumes from one Storage Availability Zone to another Compute Availability Zone (cross-attach) SHOULD be allowed.

Within each Availability Zone:

- there MUST be redundancy in power supply, as in line into the deployment
- there MUST be redundancy in external connection (e.g. internet connection or WAN-connection)
- there MUST be redundancy in core routers
- there SHOULD be at least two cooling systems, that are independent of each other

AZs SHOULD only occur within the same region and have a low-latency interconnection with a high bandwidth.

## Related Documents

The taxonomy of failsafe levels can be used to get an overview over the levels of failure safety in a deployment(TODO: link after DR is merged.)

The BSI can be consulted for further information about [failure risks](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/Kompendium/Elementare_Gefaehrdungen.pdf?__blob=publicationFile&v=4), [risk analysis for a datacenter](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_3.pdf?__blob=publicationFile&v=2) or [measures for availability](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/RZ-Sicherheit/RZ-Verfuegbarkeitsmassnahmen.pdf?__blob=publicationFile&v=9).

## Conformance Tests

As this standard will not require Availability Zones to be present, we cannot automatically test the conformance.
The other parts of the standard are physical or internal and could only be tested through an audit.
Whether there are fire zones physically available is a criteria that will never change for a single deployment - this only needs to be audited once.
It might be possible to also use Gaia-X Credentials to provide such information, which then could be tested.
