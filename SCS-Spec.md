# SCS specification draft 0.1

Must, Should, May, Should Not, Must Not used as in RFCs.

## Infrastructure (Software)

### BMC

Should support Redfish for server management (fallback: IPMI)

### Host OS: Linux

5\.4+

### Virtualization: KVM

5\.x+

### Storage (SDN): ceph

octopus+

### Networking (SDN): OvS/OVN

## Identity & Trust -- primary owner is GXFS

Must support federation of users

Must support SP role allowing Identities from Open ID Connect (OIDC) IdP

Must support flexible mapping of identity attributes to roles/rights

Should also support SP role with SAML Federation, also allowing mapping rules

Should support IdP role, allowing to expose locally managed identities to 3rd party SPs via OIDC

## IaaS layer

### OpenStack

Victoria or later

#### Version & upgrade policy

Follow SCS: SCS release \~5mo after OpenStack release, 1mo to upgrade to SCS-latest

#### RefStack, InterOp and Trademark Certification

Must comply (at least) to OpenStack Powered Compute 2020.11

Will move forward with newer SCS releases

#### Structure

##### Regions

domains must be cross-region

user management is per domain thus also cross-region

projects may be cross-region

TL;DR: regions must share identity management (keystone)\
Regions may share object storage namespace\
Regions should provide means to create network connections easily between them

##### Domains

Customers are handed out domains

Allowing sub structure (projects) managed by customer

User management (local users AND federated users) happens at domain level

##### Projects

Customer can create projects (limited by quota)

Customers should have more than one project quota by default

Project deletion: Cloud must revoke tokens. \
Cloud may require customer to have cleaned out all resources for project deletion to succeed.\
Cloud may do resource cleanup for customer when asked for deletion of project. Resource cleanup may be asynchronous then. Must not take longer than 24hrs.

Cloud must not leave orphaned resources around after project deletion (at least not longer than 24hrs). Specifically, it most also not bill them (at least no longer than 24hrs).

##### Availability zones

Compute availability zones. Must be fire protection zones, must have independent power supply. Must be reported by `openstack availability zone list --compute`.

Block storage (`openststack availability zone list --volumes`) must be EITHER one AZ for the whole region OR the same set as compute AZs. In the latter case, compute instances must have access at least to the volumes in the same AZ.

Network should not use availability zones. All networks in one region (for one project and connected by a router) should have connectivity. (TODO: Should we allow per-AZ networking? Then mandate same zoning&naming as compute. Or can we make this a must)

##### Tagging

TBW

#### Core Services

##### keystone (identity) - required

must provide keystone v3

must have option to connect users via OIDC

must provide catalog with all services for auto-discovery

must allow user management

##### nova (compute) - required

should support cells?

must support groups and affinity/anti-affinity

should support shelving/unshelving (?)

must support pause/unpause

must support suspend/resume

must support resize

must support rebuild

may support lock/unlock

may support rescue/unrescue

must support dynamic block storage attachment / detachment

must support dynamic network interface attachment / detachment

should support (the more robust) config-drive metadata injection, may use network datasource instead

should use placement service for scheduling

must follow flavor specification

must support console log

must (should?) support (no)vnc attachment

##### flavors -- see SCS flavor spec

##### placement - recommended

##### cinder (volumes) - required

must support cinderv3

may additionally support cinderv2

must support volume backup function

may support different volume types

may support volume qos settings

should support volume transfer

should support multiattach

must encrypt data written to disk/SSD

##### neutron (networking) - required

must support routers

must support snat, should be enabled by default

must support DHCP and static IP assignment

must offer public network

must offer IPv4 floating IPs

should offer IPv6 support internally (east-west)

may offer IPv6 floating IPs

must allow multiple subnets in a net (mainly for IPv4 plus IPv6 dual-stack)

must support LBaaSv2 as proxy to octavia (recommended) or independently

should support FWaaS

should support VPNaaS (IPsec)

may support bgpvpn

must support security groups

must support port security (allowed address pair settings), must default to enabled

should support dns integration

##### glance (images) - required

must allow users to register own images

must support image sharing (member setting)

must support qcow2 and raw image input

must support bare container format

must not require properties outside of SCS image standard

##### Images -- see SCS image standard spec

##### octavia (loadbalancer) - required if neutron LBaaSv2 is not deployed

must support health checks, stickiness, SSL/TLS termination ...

##### barbican (secrets) - required

##### designate (dns) - required

Trademark spec (OpenStack Powered DNS 2020.11 add-on)

must allow users to use to serving their own registered zone

should offer a default domain allowing users to register subdomains as zones

should have a code of conduct on using subdomains (or encode unique identifiers in there)

must be protected against DoS

TODO: Anything needed for secure DNS?

##### heat (orchestration) - recommended (maybe required for TOSCA?)

Support at least HOT version 2018-08-31 (Rocky)

Trademark spec (OpenStack Powered Orchestration 2020.11 add-on)

##### swift (object-storage) - recommended

Should have same namespace as S3

OpenStack Powered (Object) Storage 2020.11 Interop Tests (exceptions needed for ceph?)

##### magnum (container infra) - optional

TODO: Predefined templates?

##### karbor (backup automation) - optional

##### mistral (workflow) - optional

##### ceilometer (metering) - optional

##### gnocchi (metric) - optional

##### panko (event) - optional

##### manila (shared filesystems) - optional

OpenStack Powered Shared Filesystem 2020.11 add-on

##### ironic (bare metal) - optional

##### Web Interface - recommended

Horizon may be used

##### Other IaaS services

Other OpenStack services may be offered

Non-OpenStack services may be added to the catalog, but then must have a provider prefix

TODO: Should we require that providers offer a per-project setting where only SCS-base, SCS-extended or full will be listed in service catalogue? Making it easier for dev teams to ensure they don't introduce a dependency by mistake?

### S3 object storage

must have https support

must provide static web hosting

must not enforce 100 bucket limit

should have policy for bucket naming resolution

must encrypt data stored

should support S3 access controls ... (TBW)

## CaaS

### Must provide Kubernetes as a Service - required

Must provide K8s Cluster API version XX (beta1?)

Must output kubectl config files

Should provide multi-SCS-cloud cluster management 

May provide multi-partially-non-SCS-cloud cluster management

### Cloud integration - required

Must provice CSI

Must provide CNI (with proper network separation, not just flat networks)

### Registry - required

Must provide registry for customer images

Should provide registry with provider vetted images

Should offer artifact security scanning

### Helm - required

Must provide helm v3

### Mesh - optional

Should provide mesh discovery

Should offer sidecars for containers

Should offer proxy

### Service catalog - optional

OSB, kyma, ...

### Policy Management

OPA ...

## Monitoring & Logging

### Operator logging

Must have event log

### Operator monitoring

#### health monitoring

Must have control plane tests (e.g. os-health-monitor)

Must have data plane tests

#### capacity monitoring

Must have capacity monitoring in place (storage, CPU, RAM, network)

### User facing monitoring

Should have multi-tenant prometheus service

Should offer scraping of user-defined data exporters

Should have configurable retention/aggregation policies

Should expose relevant metrics from underlaying infra (CaaS/IaaS)

## Transparency

### Geolocations, Data Centers

### Jurisdiction(s) of DCs, Operating companies, Operator personell, ...

### Security

#### Patch policy and status (firmware, SCS, images, ...)

Should deploy SCS fixes daily

Must have CI pipeline to validate fixes in reference environment

Must include compliance/certification tests in CI (refstack - OpenStack InterOp, TBD k8s test workload)

Must deploy latest SCS release withing 1 month

Must update operator-managed images at least monthly (until declared EOL)

#### Isolation (incl. CPU vuln mitigation)

Must not use HT on L1TF affected (intel) CPUs except special flavors

Must have current mitigation against CPUs vulnerabilities (latest kernel defaults fine, except HT, see above)

Should use VxLAN for network isolation between tenants (?)

#### Encryption policy

Must encrypt all volume data before it hits permanent storage (disk/ssd/nvme)

Encryption keys must be under user control; operator managed keys must not be global and must be rotated

#### Security certs

Should have ISO27k1, 27k17, 27k18

...

#### Pentesting

### Operations

#### Update and upgrade policy

#### Deprecation & feature removal policy

#### Maintenance windows and announcement

#### SLAs & Refunds

#### RCAs

#### Contributions

### Support

#### Proactive support (newsletters etc.)

#### Reactive support (hotline, chat, tickets, ...)

### Pricing

Consumption reports

Consumption alerts

### T&C

### Technical setup documentation

### Source code & licenses

Complete Software Bill of Materials (BOM)?
