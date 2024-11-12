---
title: _End-to-End Encryption between Customer Workloads_
type: Decision Record
status: Draft
track: IaaS
---

## Abstract

This document explores options for developing end-to-end (E2E) encryption for
VMs, Magnum workloads, and container layers to enhance security between user
services. It includes a detailed review of various technologies, feedback from
the OpenStack community, and the decision-making process that led to selecting
VXLANs with the OpenStack ML2 plugin and it's later abandonment in favour of
natural openvswitch-ipsec solution.

## Terminology

| Term | Meaning |
|---|---|
| CSP | Cloud service provider, in this document it includes also an operator of a private cloud |
| VM | Virtual machine, alternatively instance, is a virtualized compute resource that functions as a self-contained server for a customer |
| Node | Machine under CSP administration which hosts cloud services and compute instances |

## Context

### Motivation

The security of customer/user workloads is one of CSPs main concerns. With
larger and more diverse cloud instances, parts of the underlying physical
infrastructure can be outside of CSPs direct control, either when
interconnecting datacenters via public internet or in the case of renting
infrastructure from third party. Many security breaches occur due to
actions of malicious or negligent inhouse operators. While some burden lies
with customers, which should secure their own workloads, CSP should have the
option to transparently protect the data pathways between instances, more so
for private clouds, where CSP and customer are the same entity or parts of the
same entity.

In RFC8926[^rfc] it is stated:
> A tenant system in a customer premises (private data center) may want to
> connect to tenant systems on their tenant overlay network in a public cloud
> data center, or a tenant may want to have its tenant systems located in
> multiple geographically separated data centers for high availability. Geneve
> data traffic between tenant systems across such separated networks should be
> protected from threats when traversing public networks. Any Geneve overlay
> data leaving the data center network beyond the operator's security domain
> SHOULD be secured by encryption mechanisms, such as IPsec or other VPN
> technologies, to protect the communications between the NVEs when they are
> geographically separated over untrusted network links.

We aren't considering the communication intra node, meaning inside one host
node between different VMs potentially of multiple tenants as this is a
question of tenant isolation, not of networking security, and encryption here
would be possibly a redundant measure. Isolation of VMs is handled by OpenStack
on multiple levels - overlay tunneling protocols, routing rules on networking
level, network namespaces on kernel level and hypervisor isolation mechanisms.
All the communication here is existing inside node and any malicious agent with
high enough access to the node itself to observe/tamper with the internal
communication traffic would pressumably have access to the encryption keys
themselves, rendering the encryption ineffective.

### Potential threats in detail

We are assuming that:

* the customer workloads are not executed within secure enclaves (e.g. Security
Guard Extensions (SGX)) and aren't using security measures like end-to-end
encryption themselves, either relying with security on the CSP or in the case
of a private cloud are run by the operator of the cloud
* the CSP OpenStack administrators are deemed trustworthy since they possess
root access to the host nodes, with access to keys and certificates, enabling
them to bypass any form of internode communication encryption
* a third party or an independent team manages physical network communication
between nodes within a colocation setting or the communication passes unsafe
public infrastructure in the case of a single stretched instance spanning
multiple data centers

#### Man in the Middle Attack

Considering the assumptions and the objective to enforce end-to-end (E2E)
encryption for user workloads, our primary security concern is averting
man-in-the-middle (MITM) attacks. These can be categorized into two distinct
forms: active and passive.

##### Passive Attacks - Eavesdropping

Consider the scenario where an untrusted individual, such as a third party
network administrator, with physical access to the data center engages in
'passive' covert surveillance, silently monitoring unencrypted traffic
without interfering with data integrity or network operations.

Wiretapping is a common technique employed in such espionage. It involves the
unauthorized attachment to network cabling, enabling the covert observation of
data transit. This activity typically goes unnoticed as it does not disrupt
the flow of network traffic, although it may occasionally introduce minor
transmission errors.

An alternative strategy involves deploying an interception device that
captures and retransmits data, which could potentially introduce network
latency or, if deployed disruptively, cause connectivity interruptions. Such
devices can be concealed by synchronizing their installation with network
downtime, maintenance periods, or less conspicuous times like power outages.
They could also be strategically placed in less secure, more accessible
locations, such as inter-building network links. This applies to wiretapping
as well.

Furthermore, the vulnerability extends to network devices, where an attacker
could exploit unsecured management ports or leverage compromised remote
management tools (like IPMI) to gain unauthorized access. Such access points,
especially those not routinely monitored like backup VPNs, present additional
security risks.

Below is a conceptual diagram depicting potential vulnerabilities in an
OpenStack deployment across dual regions, highlighting how these passive
eavesdropping techniques could be facilitated.

![image](https://github.com/SovereignCloudStack/issues/assets/1249759/f5b7edf3-d259-4b2a-8632-c877934f3e31)

##### Active - Spoofing / Tampering

Active network attacks like spoofing and tampering exploit various access
points, often leveraging vulnerabilities uncovered during passive eavesdropping
phases. These attacks actively manipulate or introduce unauthorized
communications on the network.

Spoofing involves an attacker masquerading as another device or user within the
network. This deception can manifest in several ways:

* **ARP Spoofing:** The attacker sends forged ARP (Address Resolution Protocol)
  messages onto the network. This can redirect network traffic flow to the
  attacker's machine, intercepting, modifying, or blocking data before it
  reaches its intended destination.
* **DNS Spoofing:** By responding with falsified DNS replies, an attacker can
  reroute traffic to malicious sites, further compromising or data exfiltration.
* **IP Spoofing:** The attacker disguises their network identity by falsifying
  IP address information in packets, tricking the network into accepting them
  as legitimate traffic. This can be particularly damaging if encryption is not
  enforced, enabling the attacker to interact with databases, invoke APIs, or
  execute unauthorized commands while appearing as a trusted entity.

Moreover, when an active interception device is in place, attackers can extend
their capabilities to traffic filtering. They might selectively delete or alter
logs and metrics to erase traces of their intrusion or fabricate system
performance data, thus obscuring the true nature of their activities.

### Preliminary considerations

Initially we wanted to create a plugin into Neutron[^ne] using eBPF[^eb] to
secure the traffic automatically between VMs. We presented the idea in a
team IaaS call[^ia]. After the initial round of feedback specific requirements
emerged.

#### Utilize existing solutions

Leverage existing technologies and frameworks as much as possible. This
approach aims to reduce development time and ensure the solution is built on
proven, reliable foundations. Potential technologies include:

* **OVS[^sw] + IPSec[^ip]**: Provides an overlay network and has built-in
  support for encryption using IPsec. Leveraging OVS can minimize development
  time since it is already integrated with OpenStack.
* **Neutron[^ne] with eBPF[^eb]**: Using eBPF[^eb] could provide fine-grained
  control over packet filtering and encryption directly in the kernel.
* **TripleO[^to] (with IPsec)**: TripleO[^to] tool set for OpenStack deployment
  supports IPsec tunnels between nodes.
* **Neutron[^ne] + Cilium[^ci]**: Cilium is an open source, cloud native
  eBPF[^eb]-based networking solution, including transparent encryption tools.
* **Tailscale[^ta]** is a mesh VPN based on WireGuard[^wg] that simplifies the
  setup of secure, encrypted networks. This could be a potential alternative
  to managing encrypted connections in OpenStack environments.

#### Upstream integration

Move as much of the development work upstream into existing OpenStack projects.
This will help ensure the solution is maintained by the wider OpenStack
community, reducing the risk of it becoming unmaintained or unusable in the
future. This means to collaborate with the OpenStack community to contribute
changes upstream, particularly in projects like Neutron[^ne], OVN[^ov],
kolla[^kl] and ansible-kolla[^ka].

#### Address threat modeling issues

"We should not encrypt something just for the sake of encryption." The solution
must address the specific security issues identified in the
[threat modeling](#potential-threats-in-detail). This ideally includes
protecting against both passive (eavesdropping) and active (spoofing,
tampering) MITM attacks. Encryption mechanisms on all communication channels
between VMs, containers, hosts prevents successfull eavesdropping,
authentication and integrity checks prevent spoofing and tampering. For example
IPsec[^ip] provides mechanisms for both encyption and integrity verification.

#### Performance impact and ease of use

Evaluate the performance impact of the encryption solution and ensure it is
minimal. Performance benchmarking should be conducted to assess the impact of
the encryption solution on network throughput and latency. For local trusted
scenarios opt out should be possible. The solution should also be easy to use
and manage, both for administrators and ideally fully transparent for
end-users. This may involve developing user-friendly interfaces and automated
tools for key management and configuration.

#### Avoid redundant encryption

If possible, develop a mechanism to detect and avoid encrypting traffic that is
already encrypted. This will help optimize performance and resource usage.

By focusing on these detailed requirements and considerations, we aim to
develop a robust, efficient, and sustainable E2E encryption solution for
OpenStack environments. This solution will not only enhance security for user
workloads but also ensure long-term maintainability and ease of use.

### Exploration of technologies

Based on the result of the threat modeling and presentation, we explored the
following technologies and also reached out to the OpenStack mailing list for
additional comments.

This section provides a brief explanation of OpenStack networking and design
decisions for encryption between customer workloads.

#### Networking in OpenStack

The foundation of networking in OpenStack is the Neutron[^ne] project,
providing networking as a service (NaaS). It creates and manages network
resources such as switches, routers, subnets, firewalls and load balancers,
uses plugin architecture to support different physical network implementation
options and is accessible to admin or other services through API.

Another integral part is the Open vSwitch (OVS)[^sw] - a widely adopted virtual
switch implementation, which is not strictly necessary, as Neutron is quite
flexible with compenents used to implement the infrastructure, but tends to
be the agent of choice and is the current default agent for Neutron. It allows
it to respond to environment changes, supporting accounting and monitoring
protocols and maintaining OVSDB state database. It manages virtual ports,
bridges and tunnels on hosts.

Open Virtual Networking (OVN[^ov]) is a logical abstraction layer on top of OVS,
developed by the same community that became the default controller driver for
Neutron. It manages logical networks insulated from underlying physical/virtual
networks by encapsulation. It replaces the need for OVS agents running on each
host and supports L2 switching, distributed L3 routing, access control and load
balancing.

#### Encryption options

##### MACsec[^ms]

A layer 2 security protocol, defined by an IEEE standard 802.1AE. It allows to
secure an ethernet link for almost all traffic, including control protocols
like DHCP and ARP. It is mostly implemented in hardware, in routers and
switches, but software implementations exist, notably a Linux kernel module.

##### eBPF[^eb]-based encryption with Linux Kernel Crypto API

A network packet specific filtering technology in Linux kernel called
Berkeley Packet Filter (BPF) uses a specialized virtual machine inside
kernel to run filters on the networking stack. eBPF is an extension of this
principle to a general purpose stack which can run sandboxed programs in kernel
without changes of kernel code or loading modules. High-performance networking
observability and security is a natural use-case with projects like Cilium[^ci]
implementing transparent in-kernel packet encryption with it. Linux kernel
itself also provides an encryption framework called
Linux Kernel Crypto API[^lkc] which such solutions use.

##### IPsec[^ip]

Internet Protocol security is a suite of protocols for network security on
layer 3, providing authentication and packets encryption used for example in
Virtual Private Network (VPN) setups. It is an IETF[^ie] specification with
various open source and commercial implementations. For historical
reasons[^ipwh] it defines two main transmission protocols
Authentication Header (AH) and Encapsulating Security Payload (ESP) where only
the latter provides encryption in addition to authentication and integrity. The
key negotiations use the IKE(v1/v2) protocol to establish and maintain
Security Associations (SA).

##### WireGuard[^wg]

Aims to be a simple and fast open source secure network tunneling solution
working on layer 3, utilizing state-of-the-art cryptography while maintaining
much simpler codebase and runtime setup as alternative solutions[^wgwp]. Focus
is on fast in-kernel encryption. WireGuard[^wg] adds new network interfaces,
managable by standard tooling (ifconfig, route,...) which act as tunneling
interfaces. Main mechanism, called _Cryptokey routing_, are tables associating
public keys of endpoints with allowed IPs inside given tunnels. These behave as
routing tables when sending and access control lists (ACL) when receiving
packets. All packets are sent over UDP. Built-in roaming is achieved by both
server and clients being able to update the peer list by examining from where
correctly authenticated data originates.

### Solution proposals

#### TripleO[^to] with IPsec[^ip]

> TripleO is a project aimed at installing, upgrading and operating OpenStack
> clouds using OpenStack's own cloud facilities as the foundation - building on
> Nova, Ironic, Neutron and Heat to automate cloud management at datacenter
> scale

This project is retired as of February 2024, but its approach was considered
for adoption.

Its deployment allowed for IPsec[^ip] encryption of node communication. When
utilized, two types of tunnels were created in overcloud: node-to-node tunnels
for each two nodes on the same network, for all networks those nodes were on,
and Virtual IP tunnels. Each node hosting the Virtual IP would open a tunnel
for any node in the specific network that can properly authenticate.

#### OVN[^ov] + IPsec[^ip]

There is support in the OVN[^ov] project for IPsec[^ip] encryption of tunnel
traffic[^oit]. A daemon running in each chassis automatically manages and
monitors IPsec[^ip] tunnel states.

#### Neutron[^ne] + Cilium[^ci]

Another potential architecture involves a Neutron[^ne] plugin hooking an
eBPF[^eb] proxy on each interface and moving internal traffic via an encrypted
Cilium[^ci] mesh. Cilium uses IPsec[^ip] or WireGuard[wg] to transparently
encrypt node-to-node traffic. There were some attempts to integrate Cilium[^ci]
with OpenStack [^neci1], [^neci2], but we didn't find any concrete projects
which would leverage the transparent encryption ability of Cilium[^ci] in
OpenStack environment. This path would pressumably require significant
development.

#### Neutron[^ne] + Calico[^ca]

The Calico[^ca] project in its community open source version provides
node-to-node encryption using WireGuard[^wg]. Despite being primarily a
Kubernetes networking project, it provides an OpenStack integration[^caos] via
a Neutron[^ne] plugin and deploying the necessary subset of tools like etcd,
Calico agent Felix, routing daemon BIRD and a DHCP agent.

### Proof of concept implementations

#### Neutron Plugin

Initially the potential for developing a specialized Neutron plugin was
investigated and a simple skeleton implementation for testing purposes was
devised.

Own development was later abandoned in favor of a more sustainable solution
using existing technologies as disussed in
[preliminary considerations](#preliminary-considerations).

#### Manual setup

We created a working Proof of Concept with manually setting up VXLAN tunnels
between nodes. While this solution ensures no impact on OpenStack and is easy
to set up, it has limitations, such as unencrypted data transmission if the
connection breaks. To mitigate this, we proposed using a dedicated subnet
present only in the IPsec[^ip] tunnels.

We presented the idea to the kolla-ansible[^ak] project, but it was deemed out
of scope. Instead, we were directed towards a native Open vSwitch solution
supporting IPsec[^ip]. This requires creating a new OpenStack service
(working name: openstack-ipsec) and a role to manage chassis keys and run the
openstack-ipsec container on each node.

#### Proof of concept (PoC) implementation

In our second proof of concept, we decided to implement support for
openstack-ipsec. The initial step involved creating a new container image
within the kolla[^kl] project specifically for this purpose.

##### Architecture

When Neutron[^ne] uses OVN[^ov] as controller it instructs it to create the
necessary virtual networking infrastructure (logical switches, routers, etc.),
particullary to create Geneve tunnels between compute nodes. These tunnels are
used to carry traffic between instances on different compute nodes.

In PoC setup Libreswan[^ls] suite runs on each compute node and manages the
IPSec[^ip] tunnels. It encrypts the traffic flowing over the Geneve tunnels,
ensuring that data is secure as it traverses the physical network. In setup
phase it establishes IPSec tunnels between compute nodes by negotiating the
necessary security parameters (encryption, authentication, etc.). Once the
tunnels are established, Libreswan[^ls] monitors and manages them, ensuring
that the encryption keys are periodically refreshed and that the tunnels remain
up. It also dynamically adds and removes tunnels based on changes of network
topology.

A packet originating from a VM on one compute node and destined for a VM on
a different node is processed by OVS and encapsulated into a Geneve tunnel.
Before the Geneve-encapsulated packet leaves the compute node, it passes
through the Libreswan process, which applies IPSec encryption. The encrypted
packet traverses the physical network to the destination compute node. On the
destination node, Libreswan[^ls] decrypts the packet, and OVN[^ov] handles
decapsulation and forwards it to the target VM.

##### Challanges

Implementing the openstack-ipsec image we encountered a significant challenge:
the ovs-ctl start-ovs-ipsec command could not run inside the container because
it requires a running init.d or systemctl to start the IPsec daemon immediately
after OVS[^ov] deploys the configuration. We attempted to use supervisor to
manage the processes within the container. However, this solution forced a
manual start of the IPsec daemon before ovs-ctl had the chance to create the
appropriate configurations.

Another challenge was the requirement for both the IPsec daemon and ovs-ipsec
to run within a single container. This added complexity to the container
configuration and management, making it harder to ensure both services operated
correctly and efficiently.

##### Additional infrastructure

New ansible role for generating chassis keys and distributing them to the
respective machines was created. This utility also handles the configuration on
each machine. Managing and creating production certificates is up to the user,
which is also true for the backend TLS certificates in kolla-ansible[^ka].
While this management should be handled within the same process, it currently
poses a risk of downtime when certificates expire, as it requires careful
management and timely renewal of certificates.

The new container image was designed to include all necessary
components for openstack-ipsec. Using supervisor to manage the IPsec daemon
within the container involved creating configuration files to ensure all
services start correctly. However, integrating supervisor introduced additional
complexity and potential points of failure.

##### Possible improvements

PoC doesn't currently address the opt-out possibility for disabling the
encryption for some specific group of nodes, where operator deems it
detrimental because of them being virtual or where security is already handled
in some other layer of the stack. This could be implemented as a further
customization available to the operator to encrypt only some subset of Geneve
tunnels, either in blacklist or whitelist manner.

Further refinement is needed to ensure ovs-ctl and the IPsec daemon start and
configure correctly within the container environment. Exploring alternative
process management tools or improving the configuration of supervisor could
help achieve a more robust solution.

Implementing automated certificate management could mitigate the risks
associated with manual certificate renewals. Tools like Certbot or integration
with existing Public Key Infrastructure (PKI) solutions might be beneficial.

Engaging with the upstream Open vSwitch community to address containerization
challenges and improve support for running ovs-ctl within containers could lead
to more sustainable solution.

## Decision

The final proof of concept implementation demonstrated the feasibility of
implementing transparent IPsec[^ip] encryption between nodes in an OVN[^ov]
logical networking setup in OpenStack.
To recapitulate our preliminary considerations:

### Utilize existing solutions

Implementation in kolla-ansible[^ka] is unintrusive, provided by a
self-contained new kolla[^kl] container, which only adds an IPsec[^ip]
tunneling support module to OVS[^sw], which is already an integral part of
OpenStack networking, and a mature open source toolkit - Libreswan[^ls]. Also
OVN[^ov] has native support in OpenStack and became the default controller for
Neutron[^ne].

### Address threat modeling issues

As disussed in [motivation](#motivation) and [threat
modelling](#potential-threats-in-detail) sections our concern lies with the
potentially vulnerable physical infrastructure between nodes inside or between
data centers. In this case ensuring encryption and integrity of packets before
leaving any node addresses these threats, while avoiding the complexity of
securing the communication on the VM level, where frequent additions, deletions
and migrations could render such system complicated and error prone. We also
don't needlessly encrypt VM communication inside one node.

### Avoid redundant encryption

As the encryption happens inside tunnels specific for inter-node workload
communication, isolated on own network and also inside Geneve tunnels, no cloud
service data, which could be possibly encrypted on higher-levels (TLS) is
possible here. As to the workload communication itself - detecting higher-layer
encryption in a way that would allow IPsec[^ip] to avoid redundant encryption
is complex and would require custom modifications or non-standard solutions.
It's usually safer and more straightforward to allow the redundancy, ensuring
security at multiple layers, rather than trying to eliminate it.

### Performance impact and ease of use

Setup is straightforward for the operator, there is just a flag to enable or
disable the IPsec[^ip] encryption inside Geneve tunnels and the need to set the
Neutron[^ne] agent to OVN[^ov]. No other configuration is necessary. The only
other administrative burden is the deployment of certificates to provided
configuration directory on the control node.

Certificate management for this solution can and should be handled in the same
way as for the backend service certificates which are part of the ongoing
efforts to provide complete service communication encryption in kolla-ansible.
Currently the management of these certificates is partially left on external
processes, but if a toolset or a process would be devised inside the project,
this solution would fit in.

### Upstream integration

The potential for upstream adoption and long-term maintainability makes this a
promising direction for securing inter-node communication in OpenStack
environments.

## References

[^ne]: [Neutron](https://docs.openstack.org/neutron/latest/) - networking as a service (NaaS) in OpenStack
[^eb]: [eBPF](https://en.wikipedia.org/wiki/EBPF)
[^ia]: Team IaaS call [minutes](https://github.com/SovereignCloudStack/minutes/blob/main/iaas/20240214.md)
[^sw]: [open vSwitch](https://www.openvswitch.org/)
[^ip]: [IPsec](https://en.wikipedia.org/wiki/IPsec)
[^ipwh]: [Why is IPsec so complicated](https://destcert.com/resources/why-the-is-ipsec-so-complicated/)
[^to]: [TripleO](https://docs.openstack.org/developer/tripleo-docs/) - OpenStack on OpenStack
[^ci]: [Cillium](https://cilium.io/)
[^ca]: [Calico](https://docs.tigera.io/calico/latest/about)
[^caos]: [Calico for OpenStack](https://docs.tigera.io/calico/latest/getting-started/openstack/overview)
[^ta]: [Tailscale](https://tailscale.com/solutions/devops)
[^ov]: [Open Virtual Network](https://www.ovn.org/en/) (OVN)
[^oit]: [OVN IPsec tutorial](https://docs.ovn.org/en/latest/tutorials/ovn-ipsec.html)
[^kl]: [kolla](https://opendev.org/openstack/kolla) project
[^ka]: [kolla-ansible](https://docs.openstack.org/kolla-ansible/latest/) project
[^wg]: [WireGuard](https://www.wireguard.com/)
[^wgwp]: WireGuard [white paper](https://www.wireguard.com/papers/wireguard.pdf)
[^ie]: [Internet Engineering Task Force](https://www.ietf.org/) (IETF)
[^rfc]: [RFC8926](https://datatracker.ietf.org/doc/html/rfc8926#name-inter-data-center-traffic)
[^lkc]: [Linux Kernel Crypto API](https://www.kernel.org/doc/html/v4.10/crypto/index.html)
[^ls]: [Libreswan](https://libreswan.org/) VPN software
[^ms]: [MACsec standard](https://en.wikipedia.org/wiki/IEEE_802.1AE)
[^neci1]: [Neutron + Cilium architecture example](https://gist.github.com/oblazek/466a9ae836f663f8349b71e76abaee7e)
[^neci2]: [Neutron + Cilium Proposal](https://github.com/cilium/cilium/issues/13433)
