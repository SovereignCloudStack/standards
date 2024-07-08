---
title: _End-to-End Encryption between Customer Workloads_
type: Decision Record
status: Proposal
track: IaaS 
---

## Abstract

This document explores options for developing end-to-end (E2E) encryption for VMs, Magnum workloads, and container
layers to enhance security between user services. It includes a detailed review of various technologies, feedback from
the OpenStack community, and the decision-making process that led to selecting VXLANs with the OpenStack ML2 plugin and
it's later abandonment in favour of natural openvswitch-ipsec solution.

## Context

To ensure end-to-end (E2E) encryption for user workloads, we need to mitigate the risk of man-in-the-middle (MITM)
attacks. This involves evaluating different technologies and integrating them with OpenStack to secure traffic between
virtual machines, Magnum workloads, and container layers.

In the beginning, we presented this in the IaaS call and received the following
feedback [minutes here](https://github.com/SovereignCloudStack/minutes/blob/main/iaas/20240214.md):

* We want to create a plugin into Neutron using eBPF to secure the traffic automatically between virtual machines.
  * there might be cases where traffic is not routed the encrypted way
* We should have a look into upstream to achieve some collaboration on that topic
* SecuStack has experience in encrypting traffic
  * using special SmartNICs which does the encryption, because those are dedicated hardware, not tied to Openstack
  * alternative approach in software (macsec) exists, incomplete
* How does the attacker model looks like?
  * basically the user doesn't have encrypted traffic between workloads
  * someone gaining software access on the compute node the attacker probably has also access to the private key and can
    decrypt the whole traffic
  * AI @fdobrovolny: create specific attacker models until next meeting
* AI VP04: Check Geneve/VXLAN encryption in OVN
  * Encrypting OVN tunnels with IPsec
  * rfc8926 -> 6.1.1. Inter-Data Center Traffic

The main point we gathered from this feedback was that encryption should be implemented with a specific attacker model
in mind. We also investigated the SecuStack solution with SmartNICs. However, since SecuStack was disbanded and the
solution was proprietary and focused on specific hardware, making it difficult to open-source, we decided not to pursue
this route.

## Specific requirements

Given the project is nearing the end of funding, the solution must be feasible to implement within this timeframe. To
maximize adoption and sustainability, our strategy includes the following specific requirements that should be
reevaluated when a solution has been found:

* Utilize Existing Solutions: Leverage existing technologies and frameworks as much as possible. This approach aims to
  reduce development time and ensure the solution is built on proven, reliable foundations.
* Upstream Integration: Move as much of the development work upstream into existing OpenStack projects. This
  will help ensure the solution is maintained by the wider OpenStack community, reducing the risk of it becoming
  unmaintained or unusable in the future.
* Address Threat Modeling Issues: The solution must address the specific security issues identified in the threat
  modeling exercise. This ideally includes protecting against both passive (eavesdropping) and active (spoofing,
  tampering) MITM
  attacks. As was the result of the IaaS call "We should not encrypt something just for the sake of encryption."
* Performance Impact and Ease of Use: Evaluate the performance impact of the encryption solution and ensure it is
  minimal. The solution should also be easy to use and manage, both for administrators and ideally fully transparent for
  end-users.
* Avoid Redundant Encryption: If possible, develop a mechanism to detect and avoid encrypting traffic that is already
  encrypted. This will help optimize performance and resource usage. As seen in the facebook solution.

## Detailed Considerations

Existing Solutions:

* OVS (Open Virtual Switch) + IPSec: Provides an overlay network and has built-in support for encryption using IPsec.
  Leveraging OVS can minimize development time since it is already integrated with OpenStack.
* Neutron with eBPF: Although still in the exploratory phase, using eBPF could provide fine-grained control over packet
  filtering and encryption directly in the kernel.
* TripleO (IPSEC):
  * TripleO tool for OpenStack deployment supports IPSEC tunnels between nodes.
  * TripleO has been deprecated as of February 2024.
  * Would need porting for compatibility with Ansible-Kolla.
  * Deploys an agent on each node that checks for VIP updates and creates or removes IPSEC tunnels on the fly.
  * Would potentially need replacement by a custom Neutron plugin.
* Neutron + Cilium: Potential architecture involves a Neutron plugin hooking an eBPF proxy on each interface and moving
  internal traffic via an encrypted Cilium mesh.
* Tailscale is a mesh VPN based on WireGuard that simplifies the setup of secure, encrypted networks. This could be a
  potential alternative to managing encrypted connections in OpenStack environments.

Upstream Integration:

* Collaborate with the OpenStack community to contribute changes upstream, particularly in projects like Neutron, OVN,
  kolla and ansible-kolla.
* Engage with other related projects and working groups within OpenStack to ensure alignment and gain support for the
  proposed changes.

Addressing Threat Modeling Issues:

* Passive Attacks: Implement robust encryption mechanisms to prevent eavesdropping on unencrypted traffic. This includes
  securing all communication channels between virtual machines, containers, and physical hosts.
* Active Attacks: Use authentication and integrity checks to prevent spoofing and tampering. For instance, IPsec
  provides mechanisms for both encryption and integrity verification. This should be ideally done using certificates.

Performance and Usability:

* Conduct performance benchmarking to assess the impact of the encryption solution on network throughput and latency.
* Simplify configuration and management processes to ensure that the encryption solution can be easily deployed and
  maintained. This may involve developing user-friendly interfaces and automated tools for key management and
  configuration.

By focusing on these detailed requirements and considerations, we aim to develop a robust, efficient, and sustainable
E2E encryption solution for OpenStack environments. This solution will not only enhance security for user workloads
but also ensure long-term maintainability and ease of use.

## Threat Modeling Results

### Assumptions

* The customer workloads are not executed within SGX or equivalent secure enclaves.
* The CSP OpenStack administrators are deemed trustworthy since they possess root access to the nodes, enabling them to
  bypass any form of encryption.
* A third party manages network communication among nodes within a colocation setting or by an independent team, which
  are both considered unreliable.

### Man in the Middle Attack

Considering the stated assumptions and the objective to enforce end-to-end (E2E) encryption for user workloads, our
primary security concern is averting man-in-the-middle (MITM) attacks. These can be categorized into two distinct forms:
active and passive.

#### Passive Attacks - Eavesdropping

Consider the scenario where an unauthorized individual engages in covert surveillance, such as a rogue network
administrator or an intruder with physical access to the data center. I described this type of attack as 'passive'
because their primary action is silently monitoring unencrypted traffic without interfering with data integrity or
network operations.

Wiretapping is a common technique employed in such espionage. It involves the unauthorized attachment to network
cabling, enabling the covert observation of data transit. This activity typically goes unnoticed as it does not disrupt
the flow of network traffic, although it may occasionally introduce minor transmission errors.

https://hackinglab.cz/en/blog/wiretapping/

An alternative strategy involves deploying an interception device that captures and retransmits data, which could
introduce network latency or, if deployed disruptively, cause connectivity interruptions. Such devices can be concealed
by synchronizing their installation with network downtime, maintenance periods, or less conspicuous times like power
outages. They could also be strategically placed in less secure, more accessible locations, such as inter-building
network links. This applies to wiretapping as well.

Furthermore, the vulnerability extends to network devices, where an attacker could exploit unsecured management ports or
leverage compromised remote management tools (like IPMI) to gain unauthorized access. Such access points, especially
those not routinely monitored like backup VPNs, present additional security risks.

Below is a conceptual diagram depicting potential vulnerabilities in an OpenStack deployment across dual regions,
highlighting how these passive eavesdropping techniques could be facilitated.

![image](https://github.com/SovereignCloudStack/issues/assets/1249759/f5b7edf3-d259-4b2a-8632-c877934f3e31)

#### Active - Spoofing / Tampering

Active network attacks like spoofing and tampering exploit various access points, often leveraging vulnerabilities
uncovered during passive eavesdropping phases. These attacks actively manipulate or introduce unauthorized
communications on the network.

Spoofing involves an attacker masquerading as another device or user within the network. This deception can manifest in
several ways:

* **ARP Spoofing:** The attacker sends forged ARP (Address Resolution Protocol) messages onto the network. This can
  redirect network traffic flow to the attacker's machine, intercepting, modifying, or blocking data before it reaches
  its intended destination.
* **DNS Spoofing:** By responding with falsified DNS replies, an attacker can reroute traffic to malicious sites,
  further compromising or data exfiltration. This manipulation can divert network traffic from its intended endpoint,
  potentially redirecting outbound traffic to external malicious sites if network policies do not constrain.
* **IP Spoofing:** The attacker disguises their network identity by falsifying IP address information in packets,
  tricking the network into accepting them as legitimate traffic. This can be particularly damaging if encryption is not
  enforced, enabling the attacker to interact with databases, invoke APIs, or execute unauthorized commands while
  appearing as a trusted entity.

Moreover, when an active interception device is in place, attackers can extend their capabilities to traffic filtering.
They might selectively delete or alter logs and metrics to erase traces of their intrusion or fabricate system
performance data, thus obscuring the true nature of their activities. For instance:

* **Log Filtering:** The attacker can configure the interception device to selectively remove log entries that record
  their unauthorized activities, effectively erasing evidence of their presence and actions.
* **Metric Spoofing:** By tampering with or fabricating the system's metrics, attackers can mask the resource
  utilization spikes or network anomalies typically indicative of a breach, allowing them to maintain persistence within
  the network undetected.

Below is a conceptual diagram depicting potential vulnerabilities in an OpenStack deployment across dual regions,
highlighting how these spoofing attacks could be facilitated.

![image](https://github.com/SovereignCloudStack/issues/assets/1249759/53b33dfc-6ca5-4625-8417-41136355f170)

### Notes from the IaaS Team Presentation

- IP spoofing from VMs is normally prevented by OpenStack (port security: allowed address pairs)
  * https://superuser.openinfra.dev/articles/managing-port-level-security-openstack/
  * https://docs.openstack.org/security-guide/networking/services-security-best-practices.html
    * (Needs update, `policy.json` is no longer)
  * May not be secure enough for L2 networking
- General observation: Somewhere the keys for en/decryption are handled, if the attack happens there, encryption does
  obviously not help. Threat modeling thus highly desirable.
- When looking at inter-cloud connections, the traffic invariably will go via untrusted cables.
  - Encryption in the infra will allow users not to need to know about the details on where infra is located.
- Performance impact: May need opt-out for local trusted scenarios?
- Key management for cross-provider scenarios will be complex -> backlog for now. Begin with encryption OpenStack first
- Talk to Tellus project regarding non-OpenStack implementations
  - Exposing infra encryption capability to containers (so we do not end up encrypting twice)
    - Discoverability thing
    - External (non-SCS :-)) cloud providers may not be trusted

## Exploration of Technologies

Based on the result of the threat modeling and presentation, we explored the following technologies and also reached out
to the OpenStack mailing list for additional comments.

This section provides design decisions for encryption between customer workloads and a brief explanation of OpenStack
networking for VP04 newcomers.

### Networking in OpenStack

#### Open vSwitch (OVS)

- Open vSwitch has capabilities to provide insight and deep traffic visibility.
- Allows a network control system to respond to environment changes.
- Supports simple accounting and monitoring protocols such as NetFlow, IPFIX, and sFlow.
- Network state database (OVSDB) for inventory management, observability, tracking VM migrations, and states.
- Manages virtual ports, bridges, and tunnels.
- Must be used with OVN or Neutron to provide all networking features.
- Supports multiple tunneling protocols like Geneve, GRE, VXLAN, STT, and LISP.

##### Resources

- [OVS Wikipedia article](https://en.wikipedia.org/wiki/Open_vSwitch)
- [OVS Website](https://docs.openvswitch.org/en/latest/intro/what-is-ovs/)
- [OVS in OpenStack Neutron](https://docs.openstack.org/neutron/latest/admin/deploy-ovs-selfservice.html)
- [Data centre networking: what is OVS?](https://ubuntu.com/blog/data-centre-networking-what-is-ovs)

![Classic OVS Implementation](https://input.scs.community/uploads/3873eb66-9f24-4a77-bb24-01c34a8c3deb.png)

#### Open Virtual Network (OVN)

- Provides an abstraction layer on top of OVS.
- Manages logical networks insulated from physical and virtual networks by tunnels or other encapsulations.
- Supports L2 switching and replaces the OVS agent.
- Supports L3 routing with distributed routing.
- Manages security groups with support for L2/L3/L4 Access Control Lists (ACLs).
- Includes built-in DHCP and DNS.
- Provides routing, access control, and distributed load balancing.

##### Resources

- [OVN Docs](https://docs.ovn.org/en/latest/tutorials/ovn-openstack.html)
- [OVN presentation](https://www.openvswitch.org/support/slides/OVN-Vancouver.pdf)
- [Data centre networking: what is OVS?](https://ubuntu.com/blog/data-centre-networking-what-is-ovn)
- [OVN architecture](https://www.ovn.org/en/architecture/)

![OVN Architecture ](https://input.scs.community/uploads/e0e2fd6f-8bfe-479d-858a-e202090b4dab.png)

#### Neutron

- OpenStack's native NaaS (Network as a Service).
- Creates and manages network resources such as networks, subnets, routers, firewalls, and load balancers.
- Provides APIs for creating and managing these network resources.
- Utilizes a plugin architecture to support L2/L3 plugins such as OVS and OVN.
- Extends capabilities with features such as DHCP, external DNS, routing, and security.

##### Resources

- [Neutron Docs](https://docs.openstack.org/neutron/latest/)
- [Cambridge article on Neutron](https://docs.hpc.cam.ac.uk/cloud/userguide/02-neutron.html)
- [Networking OVN docs](https://docs.openstack.org/networking-ovn/latest/)
- [Everything you need to know to get started with Neutron](https://superuser.openinfra.dev/articles/everything-you-need-to-know-to-get-started-with-neutron-f90e2797-26b7-4d1c-84d8-effef03f11d2/)

### Encryption Technologies

#### eBPF-based Encryption

- Example: [Cilium](https://cilium.io/)
- Can run at the kernel level.
- Filters can capture packets for encryption/decryption.

##### Resources

- [Enforcing encryption at scale](https://engineering.fb.com/2021/07/12/security/enforcing-encryption/)
- [Decrypting SSL at scale with eBPF, libbpf & K8s](https://www.airplane.dev/blog/decrypting-ssl-at-scale-with-ebpf)

#### IPSEC

- Example: [Strongswan](https://www.strongswan.org/)
- A secure network protocol suite.
- Authenticates and encrypts packets.
- Provides secure encrypted communication over IP.

### E2E Solution Proposals

#### TripleO (IPSEC)

- TripleO tool for OpenStack deployment supports IPSEC tunnels between nodes.
- TripleO has been deprecated as of February 2024.
- Would need porting for compatibility with Ansible-Kolla.
- Deploys an agent on each node that checks for VIP updates and creates or removes IPSEC tunnels on the fly.
- Would potentially need replacement by a Neutron plugin.

#### OVN + IPSEC

- OVN tunnel traffic is transported by physical routers and switches.
- OVN can use IPSEC.
- [OVN IPSEC Tutorial](https://docs.ovn.org/en/latest/tutorials/ovn-ipsec.html)

#### Neutron + Cilium

- Potential architecture involves a Neutron plugin hooking an eBPF proxy on each interface and moving internal traffic
  via an encrypted Cilium mesh.

##### Resources

- [Neutron + Cilium architecture example](https://gist.github.com/oblazek/466a9ae836f663f8349b71e76abaee7e)
- [Neutron + Cilium Proposal](https://github.com/cilium/cilium/issues/13433)

#### VXLAN/Geneve

- Runs on top of IPSEC tunnels.
- VXLAN technology addresses scalability issues in cloud deployments.

##### Resources

- [Setup of VXLANs](https://leftasexercise.com/2020/03/02/openstack-neutron-building-vxlan-overlay-networks-with-ovs/)
- [OpenStack ML2 plugin](https://docs.openstack.org/neutron/pike/admin/config-ml2.html)

![VXLAN Setup](https://input.scs.community/uploads/73b6da1e-33ab-432b-88b1-e6818bf58c03.png)

```bash
vagrant@compute1:~$ sudo ovs-vsctl show
f4ccc7ab-ac69-4aad-9e9f-b7d3ae353865
    Manager "ptcp:6640:127.0.0.1"
        is_connected: true
    Bridge br-tun
        Controller "tcp:127.0.0.1:6633"
            is_connected: true
        fail_mode: secure
        Port "vxlan-c0a8010b"
            Interface "vxlan-c0a8010b"
                type: vxlan
                options: {df_default="true", egress_pkt_mark="0",
                          in_key=flow, local_ip="192.168.1.21",
                          out_key=flow, remote_ip="192.168.1.11"}
        Port patch-int
            Interface patch-int
                type: patch
                options: {peer=patch-tun}
        Port "vxlan-c0a80116"
            Interface "vxlan-c0a80116"
                type: vxlan
                options: {df_default="true", egress_pkt_mark="0",
                          in_key=flow, local_ip="192.168.1.21",
                          out_key=flow, remote_ip="192.168.1.22"}
        Port br-tun
            Interface br-tun
                type: internal
    Bridge br-int
        Controller "tcp:127.0.0.1:6633"
            is_connected: true
        fail_mode: secure
        Port br-int
            Interface br-int
                type: internal
        Port int-br-phys
            Interface int-br-phys
                type: patch
                options: {peer=phy-br-phys}
        Port "tap518a9769-b5"
            tag: 1
            Interface "tap518a9769-b5"
        Port patch-tun
            Interface patch-tun
                type: patch
                options: {peer=patch-int}
    Bridge br-phys
        Controller "tcp:127.0.0.1:6633"
            is_connected: true
        fail_mode: secure
        Port phy-br-phys
            Interface phy-br-phys
                type: patch
                options: {peer=int-br-phys}
        Port "eth2"
            Interface "eth2"
        Port br-phys
            Interface br-phys
                type: internal
    ovs_version: "2.11.5"
```

![](https://input.scs.community/uploads/e5c35380-bd74-4b99-82ae-c4774df9ec71.png)

```
vagrant@compute2:~$ cat /etc/ipsec.conf 
# ipsec.conf - strongSwan IPsec configuration file

conn vxlan-tunnel-compute1
    left=192.168.1.22
    leftid=192.168.1.22
    right=192.168.1.21
    rightid=192.168.1.21
    type=tunnel
    auto=start
    authby=secret
    keyexchange=ikev2
    ike=aes256-sha1-modp1024!
    esp=aes256-sha1!
    ikelifetime=60m
    keylife=20m
    rekeymargin=3m
    keyingtries=1
    forceencaps=yes
    mobike=no
```

```
vagrant@compute2:~$ sudo cat /etc/ipsec.secrets
# This file holds shared secrets or RSA private keys for authentication.

# RSA private key for this host, authenticating it to any other host
# which knows the public part.

192.168.1.22 192.168.1.21 : PSK "YourStrongPreSharedKey"
```

```
sudo apt-get install strongswan
# Apply config from above
sudo systemctl start strongswan
sudo ipsec restart
```

### Neutron Plugin

#### Developing a plugin

- Plugins are developed outside Openstack/Neutron
- Example: [Neutron Vpnaas](https://github.com/openstack/neutron-vpnaas)
- Example 2 [Security Groups](https://docs.openstack.org/neutron/latest/contributor/internals/security_group_api.html)

#### API extension

- Using [Neutron-lib docs](https://docs.openstack.org/neutron-lib/latest/contributor/internals.html)
- User interacts with Neutron and plugins using RESTful API
- Resources are defined in `RESOURCE_ATTRIBUTE_MAP`
- `RESOURCE_ATTRIBUTE_MAP`  is used by `ExtensionDescriptor` class
- `ExtensionDescriptor` needs to bein `neutron/extensions` directory and is then loaded by `ExtensionManager` class in
  neutron core
- There are predefined APIs in [neutron-lib](https://github.com/openstack/neutron-lib/tree/master/neutron_lib) that are
  not implemented, i.e. [vpn](https://github.com/openstack/neutron-lib/blob/master/neutron_lib/api/definitions/vpn.py)
  these can be used by `APIExtensionDescriptor` class

#### Database API

- [Example](https://opendev.org/openstack/neutron/src/branch/master/neutron/db/securitygroups_db.py)
- Interacts with database

#### Agent RPC

- Processes requests from users/projects
- Can run external processes
- Uses RPC to communicate
- Neutron [Callback system](https://docs.openstack.org/neutron-lib/latest/contributor/callbacks.html)

#### Test Plugin

- Encryption [test plugin](https://github.com/MatusJenca2/neutron-encryption)
- Does nothing yet, just writes into logs
- It can be used as a base for further plugin developement
- It is in my personal repo, it might be moved to SCS if we decided to use it

## Proof of Concept 1

We created a working Proof of Concept with manually set up VXLAN tunnels between nodes. While this solution ensures no
impact on OpenStack and is easy to set up, it has limitations, such as unencrypted data transmission if the connection
breaks. To mitigate this, we proposed using a dedicated subnet present only in the IPSEC tunnels.

### Feedback from vPTG and Further Steps

We presented the idea to the Ansible-Kolla project, but it was deemed out of scope. Instead, we were directed towards a
native Open vSwitch solution supporting IPSEC (Open vSwitch IPSEC Tutorial). This requires creating a new OpenStack
service (working name: openstack-ipsec) and a role to manage chassis keys and run the openstack-ipsec container on each
node.

## Proof of Concept 2

In our second proof of concept, we decided to implement support for openstack-ipsec. The initial step involved creating
a new container image within the Kolla project specifically for this purpose. However, we encountered a significant
challenge: the ovs-ctl start-ovs-ipsec command could not run inside the container because it requires a running init.d
or systemctl to start the IPsec daemon immediately after Open vSwitch (OVS) deploys the configuration.

### Issues and Solutions

Running ovs-ctl start-ovs-ipsec in Containers:

* Challenge: The ovs-ctl process didn't behave well inside Docker containers due to the absence of a proper init.d or
  systemctl environment.
* Attempted Solution: We attempted to use supervisor to manage the processes within the container. However, this
  solution
  forced a manual start of the IPsec daemon before ovs-ctl had the chance to create the appropriate configurations.
* Outcome: The issue was not fully resolved, leading to a less-than-ideal situation where the IPsec daemon's manual
  start
  could potentially cause timing issues and misconfigurations.
  Container Co-Location Issue: Another challenge was the requirement for both the IPsec daemon and ovs-ipsec to run
  within
  a single container. This added complexity to the container configuration and management, making it harder to ensure
  both
  services operated correctly and efficiently.

### Chassis Key Management:

* Utility Development: We developed a new ansible role for generating chassis keys and distributing them to the
  respective
  machines. This utility also handles the configuration on each machine.
* Challenges: Managing and creating production certificates were shifted to the user. This approach poses a risk of
  downtime when certificates expire, as it requires careful management and timely renewal of certificates.

### Implementation Details

Container Image: The new container image was designed to include all necessary components for openstack-ipsec.
Process Management: Using supervisor to manage the IPsec daemon within the container involved creating configuration
files to ensure all services start correctly. However, integrating supervisor introduced additional complexity and
potential points of failure.
Key Distribution Utility: This new ansible role for generating and distributing chassis keys, simplifies
the dev setup. Yet, it requires users to handle, generate certificate and renewals manually, which could lead to
operational
challenges if not managed properly.

### Considerations for Improvement

Process Management: Further refinement is needed to ensure ovs-ctl and the IPsec daemon start and configure correctly
within the container environment. Exploring alternative process management tools or improving the configuration of
supervisor could help achieve a more robust solution.
Certificate Management: Implementing automated certificate management could mitigate the risks associated with manual
certificate renewals. Tools like Certbot or integration with existing Public Key Infrastructure (PKI) solutions might be
beneficial.
Upstream Collaboration: Engaging with the upstream Open vSwitch community to address containerization challenges and
improve support for running ovs-ctl within containers could lead to more sustainable solutions.

## Conclusion

The second proof of concept demonstrated the feasibility of implementing openstack-ipsec, though several challenges
remain. Addressing these issues will require further development and testing, with a focus on improving process
management within containers and automating certificate management. Despite these challenges, the potential for upstream
adoption and long-term maintainability makes this a promising direction for securing inter-node communication in
OpenStack environments.
