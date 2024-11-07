---
title: Domain Manager configuration for Keystone
type: Standard
status: Stable
stabilized_at: 2024-11-13
track: IAM
---

## Introduction

SCS Clouds should provide a way to grant Domain Manager rights to SCS Customers which provides IAM self-service capabilities within an OpenStack domain.
Such capabilities should enable the SCS customer to manage identity resources within their domain without involving the provider of the cloud.
To avoid conflict with the unscoped `admin` role in OpenStack we want to refer to this new persona as "Domain Manager", introducing the `manager` role in the API for domains.

:::info

The Domain Manager functionality will be a native part of the official OpenStack beginning with release 2024.2 ("Dalmatian").

To implement the Domain Manager in SCS clouds using an OpenStack release older than 2024.2, please refer to the supplemental [implementation notes for this standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-w1-domain-manager-implementation-notes.md).
The implementation notes document describes an alternative implementation that can be used for OpenStack 2024.1 and older releases.

:::

## Terminology

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
| persona | Abstract and conceptual role of a user in terms of IAM |
| IAM resources | projects, users, groups, roles, domains as managed by OpenStack Keystone |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| cloud admin | OpenStack user belonging to the CSP that possesses the `admin` role |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

## Motivation

In the default configuration of Keystone, only users with the `admin` role may manage the IAM resources such as projects, groups and users and their relation through role assignments.
The `admin` role in OpenStack Keystone is not properly scoped when assigned within a domain or project only as due to hard-coded architectural limitations in OpenStack, a user with the `admin` role may escalate their privileges outside their assigned project or domain boundaries.
Thus, it is not possible to properly give customers a self-service functionality in regard to project, group and user management with the default configuration.

To address this, this standard defines a new Domain Manager persona implemented using a domain-scoped `manager` role in conjunction with appropriate Keystone API policy adjustments to establish a standardized extension to the default Keystone configuration allowing for IAM self-service capabilities for customers within domains.

### Desired Workflow

1. The cloud admin deploys the Domain Manager policy configuration for Keystone as per this standard if it is not already applied.
2. The cloud admin creates the desired domains for the customers for which IAM self-service capabilities are desired.
3. The cloud admin creates one or more users within each of the applicable domains and assigns the `manager` role for a certain domain to them. These users represent the Domain Managers of the corresponding domain.
4. The customer uses the Domain Manager users to manage (create, update, delete) users, projects, groups and corresponding role assignments within their domain.

## Design Considerations

- the Domain Manager persona MUST support managing projects, groups and users within a specific domain
- the Domain Manager persona MUST be properly scoped to a domain, it MUST NOT gain access to resources outside its owning domain
- the Domain Manager persona MUST NOT be able to manipulate existing roles or create new roles
- the Domain Manager persona MUST only be able to assign specific non-administrative\* roles to their managed users where the applicable roles are defined by the CSP
- Domain Managers MUST NOT be able to abuse the role assignment functionalities to escalate their own privileges or those of other users beyond the roles defined by the CSP

\* "non-administrative" in this context means this excludes the role "`admin`" and any comparable role that grants permissions beyond domain and tenant scope.
Since the "`manager`" role as defined in this standard is domain-scoped for a Domain Manager, it does not count as administrative.

### Options considered

#### Re-using the existing `admin` role

As role assignments can be scoped to project, groups and domains the most obvious option would be to assign the existing `admin` role to users representing Domain Managers in a scoped fashion.

However, due to architectural limitations[^2] of the existing OpenStack implementation of roles, the `admin` role has a special meaning reaching beyond the RBAC checks done by Keystone and other OpenStack components.
This results in special permissions being granted to users possessing the role which ignore the project or domain scope of the role assignment.
This poses severe security risks as the proper scoping of the `admin` role is impossible.
**Due to this, this approach was discarded early.**

Upstream (OpenStack) is in the process of addressing this across the services, but it has not been fully implemented yet, especially for domains[^3].

[^2]: [Launchpad bug: "admin"-ness not properly scoped](https://bugs.launchpad.net/keystone/+bug/968696)

[^3]: [OpenStack Documentation: Keystone for Other Services - Domain Scope](https://docs.openstack.org/keystone/latest/contributor/services.html#domain-scope)

#### Introducing a new persona and role with API policy changes

OpenStack Keystone allows for new roles to be created via its API by administrative users.
Additionally, each OpenStack API's RBAC can be adjusted through an API policy file (`policy.yaml`) through olso-policy[^4], Keystone included.
The possibility of managing users, projects, role assignments and so on is regulated through Keystone's RBAC configured by its API policy file.

This means that by creating a new role and extending Keystone's API policy configuration a new Domain Manager persona can be established that is limited to a specific subset of the Keystone API to be used to manage users, projects and role assignments within a domain.

[^4]: [OpenStack Documentation: Administering Applications that use oslo.policy](https://docs.openstack.org/oslo.policy/latest/admin/index.html)

## Decision

A role named "`manager`" MUST be present in the identity service.

The identity service MUST implement the Domain Manager functionality for this role.
The implementation details depend on the OpenStack Keystone version used.
See the sections below for reference.

### For OpenStack Keystone 2024.2 or later

For OpenStack Keystone 2024.2 or later the Domain Manager persona is already integrated natively.
To guarantee proper scope protection, the Identity API MUST be configured with "`enforce_scope`" and "`enforce_new_defaults`" enabled for the oslo.policy library.

Example entries for the `keystone.conf` configuration file:

```ini
[oslo_policy]
enforce_new_defaults = True
enforce_scope = True
```

The "`is_domain_managed_role`" policy rule MAY be adjusted using a dedicated `policy.yaml` file for the Identity API in order to adjust the set of roles a Domain Manager is able to assign/revoke.
When doing so, the `admin` role MUST NOT be added to this set.

#### Note about upgrading from SCS Domain Manager to native integration

In case the Identity API was upgraded from an older version where the policy-based Domain Manager implementation of SCS described in the [implementation notes for this standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-w1-domain-manager-implementation-notes.md) was still in use, the policies described there MUST be removed.
The only exception to this is the "`is_domain_managed_role`" rule in case any adjustments have been made to that rule and the CSP wants to preserve them.

### For OpenStack Keystone 2024.1 or below

For OpenStack Keystone 2024.1 or below, the Domain Manager functionality MUST be implemented using API policies.
For details, refer to the [implementation notes for this standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-w1-domain-manager-implementation-notes.md).

For the release 2024.1 and below, changing the "`enforce_scope`" and "`enforce_new_defaults`" options for the Identity API is not necessary for the Domain Manager implementation.

## Related Documents

### Upstream contribution spec for the Domain Manager functionality

**Description:** Upstream Identity service specification to introduce the Domain Manager functionality natively in OpenStack Keystone.
After implementing the Domain Manager functionality as described in the [implementation notes for this standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-w1-domain-manager-implementation-notes.md), the SCS project contributed the functionality to the official OpenStack project.
This eventually resulted in the feature being integrated natively in OpenStack Keystone starting with the 2024.2 release.
The specification was the starting point of the contribution.

**Link:** [OpenStack Identity Specs: Domain Manager Persona for domain-scoped self-service administration](https://specs.openstack.org/openstack/keystone-specs/specs/keystone/2024.1/domain-manager-persona.html)

### "admin"-ness not properly scoped

**Description:** Upstream bug report about the underlying architectural issue of the `admin` role not being properly scoped and giving system-level admin permissions regardless of whether the `admin` role assignment was scoped to project or domain level.
This is the main reason for the `admin` role being inappropriate to implement Domain Managers.

**Link:** [Launchpad bug: "admin"-ness not properly scoped](https://bugs.launchpad.net/keystone/+bug/968696)

### Consistent and Secure Default RBAC

**Description:** Upstream rework of the default role definitions and hierarchy across all OpenStack services.
Aims to introduce support for a scoped `manager` role by 2024 but only focuses on project-level scoping for this role so far, not domain-level.

**Link:** [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

## Conformance Tests

There is a test suite in [`domain-manager-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iam/domain-manager/domain-manager-check.py).
The test suite connects to the OpenStack API using two sample domains and corresponding Domain Manager accounts.
It verifies the compliance to the standard and the proper domain-scoping as defined by the Keystone policy.
Please consult the associated [README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iam/domain-manager/README.md) for detailed setup and testing instructions.

## Appendix

### Decision Record

#### Change the naming of the Domain Manager role to align with upstream

Decision Date: 2024-03-13

Decision Maker: Team IaaS

Decision:

- the Domain Manager role should be named "manager" not "domain-manager"

Rationale:

- upstream (OpenStack) will introduce a "manager" role with the upcoming RBAC rework
- the "manager" role is intended to grant managing capabilities bound to the scope it is assigned for, e.g. projects; it would make sense to also integrate the Domain Manager approach here
- during the process of contributing the Domain Manager functionality upstream we were asked to use the already defined "manager" role instead of introducing a new role; so the rename would then also be in line with the upstream contribution

Links / Comments / References:

- [Team IaaS meeting protocol entry](https://github.com/SovereignCloudStack/minutes/blob/main/iaas/20240313.md#domain-manager-rolepersona-markus-hentsch)
- [request from upstream to re-use existing "manager" role](https://review.opendev.org/c/openstack/keystone-specs/+/903172/2/specs/keystone/2023.1/domain-manager-role.rst#20)

#### Allow flexibility for the roles a Domain Manager can assign/revoke within domain

Decision Date: 2023-09-27

Decision Maker: Team IaaS, Team IAM

Decision:

- the standard should not strictly limit the roles a Domain Manager can assign/revoke to/from other users within a domain to the "member" role
- the standard should allow CSPs to define one or more roles for Domain Managers to manage
- whether or not this includes the Domain Manager role itself is not to be predefined by the standard and should be up to the CSP to decide instead
- the standard should only strictly prohibit adding the "admin" role to the list of roles manageable by Domain Managers

Rationale:

- the available and configured roles might differ between CSPs and infrastructures
- the Domain Manager standard should be flexible enough to adapt to different environments while still offering the intended functionality
- there might be a tradeoff between self-service flexibility desired by customers and the security regulation a CSP wants to impose, thus allowing or prohibiting the designation of Domain Managers by customers themselves should be up to the CSP to decide

Links / Comments / References:

- [Team IaaS meeting protocol entry](https://input.scs.community/2023-scs-team-iaas?view#Domain-Manager-Standard-markus-hentsch)

#### Extend domain management functionality to Keystone groups

Decision Date: 2023-08-04

Decision Maker: SIG IAM

Decision:

- the Domain Manager Standard configuration should cover the groups functionality of Keystone, allowing domain manager to manage groups in domains

Rationale:

- the groups functionality is a desired IAM feature for customers

Links / Comments / References:

- [SIG IAM meeting protocol entry](https://input.scs.community/2023-scs-sig-iam#Domain-Admin-rights-for-SCS-IaaS-Customers-184)
- [action item issue](https://github.com/SovereignCloudStack/issues/issues/383)

#### Change the naming of the Domain Manager role

Decision Date: 2023-08-04

Decision Maker: SIG IAM

Decision:

- the Domain Manager role should be named "domain-manager" not "domain-admin".

Rationale:

- avoid confusion with the unscoped admin role and to be inline with the upstream plan: [Default Service Role - Identity Specs](https://specs.openstack.org/openstack/keystone-specs/specs/keystone/2023.1/default-service-role.html)

Links / Comments / References:

- [SIG IAM meeting protocol entry](https://input.scs.community/2023-scs-sig-iam#Domain-Admin-rights-for-SCS-IaaS-Customers-184)
- [issue comment about decision](https://github.com/SovereignCloudStack/issues/issues/184#issuecomment-1670985934)
