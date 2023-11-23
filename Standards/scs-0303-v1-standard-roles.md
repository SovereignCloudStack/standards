---
title: SCS Standard Roles
type: Standard
status: Draft
track: IAM
---

## Introduction

SCS aims to provide a standardized role model for RBAC roles across all supported OpenStack API services that applies sensible and consistent permission sets based on a set list of roles defined by a standard.
It is closely guided by the OpenStack defaults.

### Glossary

The following special terms are used throughout this standard document:

| Term | Meaning |
|---|---|
| RBAC | Role-Based Access Control[^1] established by OpenStack Keystone |
| project | OpenStack project as per Keystone RBAC |
| user | OpenStack user as per Keystone RBAC |
| group | OpenStack group as per Keystone RBAC |
| role | OpenStack role as per Keystone RBAC |
| domain | OpenStack domain as per Keystone RBAC |
| IAM | identity and access management |
| IAM resources | projects, users, groups, roles, domains as managed by OpenStack Keystone |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| cloud admin | OpenStack user belonging to the CSP that possesses the `admin` role |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

## Motivation

The permission settings of OpenStack RBAC roles are configured in service-specific deployment configuration files (usually the respective "`policy.yaml`") in a rather static way and have to be carefully managed.
In contrast to many of OpenStack's IAM and IaaS resources, these settings cannot be changed via its API at runtime.
For this reason it is important to have a secure and sensible default configuration in SCS clouds that is both intuitive and flexible enough to cover all necessary use cases of permission models desired by CSPs and customers.

## Design Considerations

One key aspect of the design considerations for this standard is to be as close to the native (upstream) OpenStack role model and role definitions as possible to not introduce unnecessary complexity or divergence from OpenStack.
Meanwhile the standardized roles and permission sets should cover all scenarios and use cases that SCS deems necessary.

### Options considered

#### Using the current OpenStack default roles as-is

At the time of writing this standard, OpenStack is in the midst of updating and unifying the default roles and their permission set in an ongoing RBAC rework[^2].
This will update the set of default roles and their permission sets.

Currently, Barbican still uses a separate set of default roles[^3] that is distinct from Keystone and the rest of the services.
However, this will be replaced by the unified roles with the RBAC rework.

Due to this, the current state of the default roles and permissions in OpenStack can be considered depracated and will change as soon as the RBAC rework is concluded.

As a result, this option is not a good choice for standardization in SCS, because it would be based on soon-to-be outdated OpenStack defaults.

[^2]: [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

[^3]: [OpenStack Barbican Documentation: Access Control - Default Policy](https://docs.openstack.org/barbican/2023.2/admin/access_control.html#default-policy)

#### Fully using the RBAC rework of OpenStack as a basis

Instead of focusing on the current defaults of OpenStack at the time of writing this standard, the upcoming RBAC rework[^1] could serve as a basis for a unified role and permission set in SCS.

For this option, SCS would adopt the upcoming changes to OpenStack's default roles in advance and only incorporate minimal adjustments where necesary.

The risk associated to this approach is related to the parts of the RBAC rework that are not finally implemented yet.
For instance, this concerns the "manager" role that OpenStack aims to establish on a project-scope level.
In case this standard would prematurely adopt role and policy configuration that get changed until the RBAC rework concludes, it would introduce unnecessary divergence and burden CSPs with another transition later on.

#### Using only the stable parts of the OpenStack RBAC rework as a basis

Instead of prematurely adopting all proposed changes of the upcoming RBAC rework in OpenStack[^1], this standard could limit its adoption scope to changes of the rework that have already been finalized in OpenStack at the time of writing this standard.
This way, no role or policy definitions would be incorporated that pose the risk of still receiving major changes from upstream.

Once the RBAC rework concludes, anything not already included in this standard could be added to it in a later version/revision of the standard, seamlessly aligning with upstream later on.

## Open questions

## Decision

TODO

Furthermore, the project-scoped "manager" role defined by OpenStack's RBAC rework will not be incorporated into the SCS standard as long as its integration is not finalized in upstream OpenStack.

### Roles

| Role | Purpose |
|---|---|
| admin | CSP-exclusive cloud administrator possessing all privileges. |
| domain-manager\* | Manager within customer-specific domains. Is allowed to manage groups, projects and users within a domain. Used for IAM self-service by the customer. |
| member | Read/write access to resources within projects. |
| reader | Non-administrative read-only access to resources within projects. |

\* Roles that are currently specific to the SCS standard and diverge from the default set of OpenStack or its RBAC rework are marked with an asterisk.


## Related Documents

### SCS Domain Manager standard

**Description:** SCS standard that describes the Domain Manager role introduced by SCS and its configuration.

**Link:** [SCS Standards: Domain Manager configuration for Keystone](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-v1-domain-manager-role.md)

### Consistent and Secure Default RBAC

**Description:** Upstream rework of the default role definitions and hierarchy across all OpenStack services (ongoing as of 2023).

**Link:** [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

## Conformance Tests

Conformance Tests, OPTIONAL

## Appendix

### Decision Record

#### An auditor role will not be included

Decision Date: 2023-11-22

Decision Maker: Team IaaS

Decision:

- we will not introduce a SCS-specific "auditor" role that diverges from OpenStack and resembles a subset of the "reader" role

Rationale:

- the auditor role was intended to be a restricted reader role that has read-only access but does not see everything a reader does to hide potentially sensitive information
- RBAC granularity is not fine enough to properly differentiate between sensitive and non-sensitive information on API endpoints (mostly individual properties of response body contents)
- there is no one-size-fits-all classification of sensitive API response contents as requirements vary between use cases and environments; "what counts as sensitive information?" is hard to answer in a standardized fashion

Links / Comments / References:

- [Team IAM meeting protocol entry](https://github.com/SovereignCloudStack/minutes/blob/main/iaas/20231122.md#role-standard) 


#### Introduction of "auditor" role should be considered

Decision Date: 2023-10-18

Decision Maker: Team IAM

Decision:

- we should consider and evaluate the possibility of adding a "auditor" role as a reader subset for hiding sensitive data

Rationale:

- the reader role might still expose sensitive data about the tenant and their resources and is unsuited for inspections by independent third parties and similar use cases

Links / Comments / References:

- [Team IAM meeting protocol entry](https://github.com/SovereignCloudStack/minutes/blob/main/iam/20231018.md#roles-markus-hentsch)

#### Align with upstream, avoid divergence

Decision Date: 2023-10-18

Decision Maker: Team IAM

Decision:

- the standard should use OpenStack's defaults as much as possible; the standard should only diverge where absolutely necessary
- if using diverging permission sets for roles, roles should be named differently from OpenStack
- any resulting divergences should be attempted to bring upstream (e.g. the domain-manager role)
- we will not incorporate the "manager" role as proposed by the upstream RBAC rework yet as it might still be subject to change

Rationale:

- diverging from OpenStack in the IAM basics introduces unnecessary friction for CSPs and hinders interoperability

Links / Comments / References:

- [Team IAM meeting protocol entry](https://github.com/SovereignCloudStack/minutes/blob/main/iam/20231018.md#roles-markus-hentsch)
