# SCS Glossary

This file serves as the central glossary within SCS. It is intended to clearly
define terms used within SCS where there may be differing understandings. The
glossary is not intended to evaluate or standardize specific terms.

## Definition of a Region

An OpenStack/SCS region consists of at least one or more Availability Zones that share a Control Plane with their services. As a result, they share one API. Also a Control Plane can share one CEPH cluster over different fire departments or each Availbility Zone can have its own CEPH cluster. Within the region, any Layer 2 networks are available to the user. Availbility Zones which build a region are connected by redundant low-latency (<2ms (guess!!) ) high bandwidth (10s of Gbps) connections.

Regions can be federated when the SCS code is ready.

## Definition of a Availability Zone

An Availability Zone is a (physical) group of multiple compute nodes, controlled by the region's control plane that provides the API and interface.

An Availability Zone allows OpenStack compute hosts to be divided into logical groups and provides a form of physical isolation and redundancy from other Availability Zones, for example by using a separate power supply or network devices.

When users provision resources, they can specify in which Availability Zone their instances should be created. In this way, customers can ensure that their application resources are distributed across different failure domains to achieve high availability in the event of a hardware failure.

## Definition of Host Aggregates

Host aggregates are a mechanism for partitioning compute nodes which is not explicitly visible to users in an OpenStack/SCS cloud.  Host aggregates are based on arbitrary characteristics such as server type, processor type, GPU, disk speed, etc.
Administrators assign flavors to host aggregates by specifying metadata on the host aggregate and customizing the extra specifications of the flavor. It is then up to the Nova scheduler to determine the best match for the user request. Compute nodes can also be in more than one host aggregate.

Optionally, one can designate a host aggregate as an Availability Zone, e.g. for simplification reasons of the user selection of an availbility zone.  
Availability Zones differ from Host Aggregates in that they are shown to the user as a Nova boot option, so Compute VMs can be started on them.
Compute Nodes, however, can only be in a single Availability Zone. We can configure a default Availability Zone where instances will be scheduled if the user does not specify an Availability Zone.

Info: A prerequisite for creating an Availability Zone is a host aggregate.

## Definition of a Cell

The Cells paradigm simplifies the handling of large Openstack deployments.

Cells is an OpenStack Nova feature that improves scalability for Nova in OpenStack Platform. Each Cell has a separate database and message queue, which increases performance when scaling. One can provision additional Cells to handle large deployments, and compared to Regions, this allows access to a large number of compute nodes through a single API.

Each Cell has its own Cell controllers running the database server and RabbitMQ along with the Nova Conductor services.

Nova Conductor services, called "Super Conductor", continue to run on the main controller nodes.

The services in the Cell Controllers can still call placement APIs, but cannot access other API layer services via RPC, nor can they access global API databases on the control nodes.

## Definition of a Control Plane

In Openstack/SCS, a Control Plane consists of at least 5 hardware nodes, which together serve several Availability Zones and thus provide a common usable API for a region. The Control Plane also shares the network (Neutron), the Scheduler and the CEPH services.

It includes the Controller Nodes (Galera Cluster, RabbitMQ) and the Manager Nodes, Maas,...

## Definition of Control Node

The Control Node runs the Identity Service, Image Service , management processes for compute nodes, management processes for networking, various networking agents, and the Dashboard. It also includes supporting services such as an SQL database, a message queue, and NTP.

Optionally, the Controller Node runs parts of the Block Storage, Object Storage, Orchestration and Telemetry services.

The Controller Node requires at least two network interfaces.

## Definition of Compute Node

A compute host runs the hypervisor part of compute that runs instances. By default, compute uses the KVM hypervisor. The compute host also runs a networking service agent that connects instances to virtual networks and provides firewall services to the instances through security groups.

If you offer hyper-converged infrastructure, a compute host also serves the Ceph. This makes the storage dynamically scalable (horizontally and vertically). For the Ceph services, 1 CPU core and 4 GB of RAM are reserved per OSD to ensure appropriate performance.

## Definition of Manager Node

From here, the OSISM Ansible playbooks are applied to the environment. Furthermore, the following services often run here non-redundantly: Prometheus server,....

## Definition of provider network

The provider network is the network that is "in front", i.e. at the output points of the openstack/SCS. This is usually a public network, but can also be a private network in individual cases. IPs from the provider network can be assigned to instances within the SCS. The same applies to load balancers, of course.

## Definition of API

The Rest API provides the core of openstack/SCS  and can be addressed for a whole region. It accepts and responds to end-user API calls.  The service supports the OpenStack Compute API, the Amazon EC2 API, and a special Admin API for privileged users to perform administrative actions. Policies are enforced and most orchestration actions can be started, such as launching an instance.

## Horizon

Horizon is openstack's preferred GUI for the end user, but also for the administrator for a quick overview. It runs on the controller node. Other GUIs are possible, also GUIs which replace the horizon interface

## Message Queue

Most OpenStack services communicate with each other through the message queue. For example, Compute communicates with Block Storage services and Network services via the message queue. RabbitMQ, Qpid, and Zeromq are popular choices for a message queue service. When the message queue fails or becomes inaccessible, the cluster generally comes to a halt and ends up in a read-only state where the information is stuck at the point where the last message was sent. Therefore, this is clustered.  RabbitMQ has shown itself to be the most widespread and best supported variant in the OpenStack context, Qpid occurs occasionally, ZeroMQ lacks HA functionality to date

## Keystone

( The OpenStack Identity module called Keystone is used as an authentication and rights system between the OpenStack components. Keystone divides access to projects in the cloud into so-called "tenants". A tenant is a tenant of the cloud and has at least one assigned user. It is possible to create multiple users per tenant with different rights. Keystone uses a token system for authorization and also supports the connection to other authentication options such as LDAP. (wikipedia) )

## Glance

The OpenStack Image Service, also called Glance, is a service that provides virtual machine images to OpenStack users. These images are used by Nova as a template to compile virtual machine instances. Both local hard disks and object storage solutions such as Swift or Ceph can be used as storage backends.

In addition to the images, Glance can also store metadata such as the operating system used or the kernel version. Access to both this metadata and the images themselves is via a REST API. Glance supports a number of formats such as VHD, VMDK and qcow2.

## OSISM

The Open Source Infrastructure & Service Manager is a powerful deployment framework for OpenStack and Ceph as well as required services such as a RabbitMQ broker or a MariaDB Galera cluster.

## Ceph

Ceph is an open source distributed storage solution. The core component is RADOS (Reliable Autonomic Distributed Object Store), an object store that can be distributed redundantly over any number of servers. Ceph offers the user three types of storage: An object store compatible with the Swift and S3 API (RADOS Gateway), virtual block devices (RADOS Block Devices) and CephFS, a distributed file system.

## Nova

Nova is virtually a synonym for Compute. It is the part of the stack that can manage groups of virtual machines.

The virtualized systems can be distributed over any number of so-called compute nodes. Hypervisors supported include KVM, Xen Hyper-V and ESXI. In the community, KVM is considered to be set and best supported (we use KVM), which is controlled via libvirt. ESXI and Hyper-V can be used, sometimes with limited functionality.

## Neutron

The OpenStack Networking module Neutron provides the networking service for OpenStack. Neutron can be used to manage networks, subnets, and IP addresses/floating IPs. A floating IP in OpenStack refers to an official IP that serves as an interface from the internal to the public network. In addition to a load balancer, HA proxy and health monitor, Neutron also supports techniques such as VLAN and VPN. To secure the networks, Neutron uses a firewall that allows versatile port rules, e.g. on a security group basis. For trademark reasons, the OpenStack networking module had to be renamed "Neutron". The previous name was "Quantum."

For the management of the data link layer, Neutron offers the possibility to use various already existing networking software such as Open vSwitch or the bridge functionality of the Linux kernel by means of plugins.

In the OpenStack releases since Ussuri, the "OpenVirtualNetwork"(OVN) has established itself, it replaces many of the Neutron components, e.g. L3 and DHCP agent, so that Neutron only has to talk directly to OVN.

## Cinder

OpenStack Block Storage or Cinder provides virtual block storage in the form of virtualized storage media (hard disks, CDs, etc.). The block storage can be attached to virtual machines. An API interface allows Cinder to connect to Swift so that block storage media can communicate with object storage. Meanwhile, many other storage backends are also fully or partially supported. There is also the option of defining multiple backends and creating a volume type for each backend, so that when a new volume is created, it can be selected on which storage backend the volume is created.

## Swift

Swift is the so-called object storage that can be used by Nova. This is responsible for redundant data storage. Swift can also be used as a backend for Cinder or Glance. Objects are stored in so-called containers, which are primarily used to group objects and store metadata and in turn belong to individual accounts. Objects and containers are accessed via a REST API.

## Ceph OSD

A Ceph OSD (Object Storage Daemon) logically represents a storage device in a Ceph cluster, which can logically be a hard disk, which is the ideal case. In other cases it can also be a raid, which however leads to considerable performance limitations due to caching or other raid optimization.

## Personas

|Persona|Description|
|SCS Operator|The SCS Operator is the one who owns and operates a standardized cloud environment.|
|SCS Consumer|The SCS Consumer consumes a standardized SCS environment and operates and orchestrates applications on top of it. The SCS Consumer is typically a customer or user of the SCS Operator.|
|SCS Integrator|The SCS Integrator assists in or is building up a standardized cloud environment. The SCS Integrator can be 2nd or 3rd level support for the SCS Operator.|
|SCS Project|The SCS Project oversees the overall activities around the Sovereign Cloud Stack.|
|SCS Developer|The SCS Developer actively contributes to technical elements of the Sovereign Cloud Stack.|

