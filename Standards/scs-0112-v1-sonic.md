---
title: SONiC Support in SCS
type: Decision Record # Standard  | Decision Record | Procedural
status: Draft
track: Global # Global | IaaS | Ops | KaaS | IAM
description: |
  SCSS-0112 outlines architectural decisions in SCS in regards to SONiC support and integration.
---

<!---
This is a template striving to provide a starting point for
creating a standard or decision record adhering to scs-0001.
Replace at least all text which is _italic_.
See https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md
--->

## Introduction

SONiC support in [SCS](https://scs.community) was considered within the context of [VP04 Networking](https://scs.community/tenders/lot4), sub-lot 1 SDN scalability. Different challenges and approaches to SDN scalability have been explored and more specifically those who require support in the underlay network. Using SONiC in the underlay can have benefits for SCS users by using a standardized OS for network devices and also having a clear path for network scalability when using SONiC. For this to work, we have to define how SONiC is used and supported architecturally in SCS. This document outlines the architectural decisions in regards to SONiC support and integration in SCS.

## Motivation

In respect to SDN scalability improvements in Openstack and SCS, there are several ways SONiC can be leveraged.

### SONiC as a network OS where dynamic network configuration in Openstack is required

In many network designs for Openstack, configuration of the actual network hardware by Openstack Neutron service is required. The following network designs apply:

- VLANs. Uisng VLANs to segment tenant networks requires the network switch to be configured. This can be manual or dynamic configuration via the ML2 Neutron driver.

- EVPN/VXLAN on the switch. In this use case, SONiC runs on leaf switches. Leafs terminate VXLAN endpoints and run BGP/EVPN for the control plane. Again, the ML2 Neutron driver is used to dynamically configure the network switch. The link between the switch and the service is regular VLAN.

- VXLAN on servers and switches. This is a hybrid use case, where most of the SDN is pushed to the server, but the network is still involved where support for bare metal hosts is needed.

### Automation and tooling for SONiC

There is no tooling in SCS or Openstack communities to facilitate the rollout and configuration of enterprise scale SONiC deployments. Netbox and OSISM can be integrated, so that Netbox becomes the source of truth for network configuration and OSISM supports the initial rollout and configuration for the switches.

### OVN for SONiC

OVN and OVS are extensively leveraged in Neutron to SDN. In large scale deployments, OVN can become a bottleneck by exhausting resources on network nodes. SONiC can host the OVN control plane as a module (container) and spare the resources in network nodes. There is however a potential other bottleneck on SONiC hardware, as OVN control plane can be resource intensive. This is a potential area for further investigation.

## Design Considerations

There are different ways SONiC support can be implemented in SCS, very similar to existing approaches with Linux.

### Options considered

#### Option 1: SCS distribution of SONiC

With this approach, SCS will create it's own distribution of SONiC, similar to what Debian or Arch are for Linux. This distribution will be based on the SONiC community distribution, but will have SCS specific modules, which will be developed and maintained by SCS. SCS will contribute its code to dedicated SCS repositories and build its own SONiC images. The code can eventually be pushed upstream, but not as top priority. This approach will allow SCS to have a clear path for SONiC support and integration in SCS, but will also require SCS to maintain a distribution of SONiC, which is a significant effort. Upstream/downstream changes will have to be managed and maintained. However the advantage is that SCS will have full control over the distribution and can make changes as needed. Users will have to use the SCS distribution of SONiC, which will be based on the community distribution. If users already deploy community or enterprise SONiC, a migration path to SCS SONiC will be needed.

#### Option 2: SCS will support SONiC but will not change it

SCS supports enterprise ans community versions of SONiC but will not develop its own code for it. This will significantly limit the ability to develop new features for SDN, because all changes will be done in the tooling around SONiC and not in the OS itself. The advantages are that SCS will still improve SONiC support and will have minimal effort for this. The downside is that some features like OVN control plane for SONiC will not be possible.

#### Option 3: SCS develops SCS-specific modules as add-on for any SONiC (Community or Enterprise)

In option 3, SCS will change SONiC by releasing its own modules for it. Those module can be provided as add-ons and installed on top of any version, community or enterprise. While compatability between the modules the SONiC releases will need to be maintained, there will be much broader support for SONiC and users will be able to pick and chose distributions based on their existing relationships and experience and use SCS independent of this. In cases where SCS provides contributions to core SONiC, those can be made in upstream Community repositories, so that the whole community including the propriatory vendors can adopt them eventually.

## Open questions

State of SONiC community?

- community version: mature or not?

Commits: between 40-52 per month. Contributors to master: 10-20. Mailing list: 6 lists, about 10-30 messages/month for list. Community version supports 25 hardware vendors. Requires significant time and resource investment and "Explorer's mindset".

- enterprise version: mature or not?

Multiple vendor distributions. Expensive in general

- release schedule - how often are features and bugfixes released?

New tags appears on different periods, once 2 times per month, other 3 months between releases.

- adoption penetration - how many vendors use it? What type of venders (big, medium and large)?

Good initial adoption: Microsoft, Target. Adoption requires time and money

- Is SONiC being overtaken by alternatives: SmartNICs and DPUs? How relevant is it still and will be in the coming years?

Actually not, because of different use cases.

- Sustainability of community SONIC for 2025+

The SONiC community is healthy and growing, however progress is slower due to factors like investment of resources. The barrier of entry is much higher than other similar OSS projects.

## Decision

IaaS team recommends to use Option 3: SCS develops SCS-specific modules as add-on for any SONiC (Community or Enterprise). It has the best tradeoff between time and resource investment and benefits for the community. Adopting this strategy would allow SCS to be agile and quickly adopt SONiC, by providing users with clear path while allowing the freedom to chose different hardware and software vendors. SCS code can be packaged independently of each SONiC distribution and installed as add-on. Also SCS contributions to core SONiC will be done directly upstream, so that the whole community can benefit from them.

Work on hardware support in SONiC should be raised in upstream and SCS shouldn't make significant investments in this area.

## Related Documents

- [Research SDN scalability](https://input.scs.community/VP04-issues-455-research-SDN-scalability)
- [Results SONIC Usage in SCS](https://input.scs.community/SCS-DR-SONIC-usage)
- [SONiC Community research](https://input.scs.community/oW_plPZ6RkuXs3k9mrRDdw#)
