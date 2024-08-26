---
title: Domain Manager configuration for Keystone
type: Standard
status: Draft
track: IAM
---

## Introduction

SCS Clouds should provide a way to grant Domain Manager rights to SCS Customers which provides IAM self-service capabilities within an OpenStack domain.
This is not properly implemented in the default OpenStack configuration and requires specific adjustments to the Keystone identity management configuration.
To avoid conflict with the unscoped `admin` role in OpenStack we want to refer to this new persona as "Domain Manager", introducing the `manager` role in the API for domains.

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
| persona | Abstract and conceptual role of a user in terms of IAM |
| IAM resources | projects, users, groups, roles, domains as managed by OpenStack Keystone |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| cloud admin | OpenStack user belonging to the CSP that possesses the `admin` role |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

### Impact

Applying this standard modifies the API policy configuration of Keystone and introduces a new persona to Keystone to enable IAM self-service for customers within a domain.
Once assigned, this persona allows special Domain Manager users within a domain to manage users, project, groups and role assignments as part of the IAM self-service.

However, the configuration change introduced by this standard does not automatically assign the Domain Manager persona to any users per default.
Assigning the new persona and granting customers the resulting self-service capabilities is a deliberate action to be taken by the CSP on a per-tenant (i.e. per domain) basis.

Omitting the provisioning of any Domain Manager users (i.e. not assigning the new persona to any user) will result in an OpenStack cloud that behaves identically to a configuration without the standard applied, making the actual usage of the functionality a CSP's choice and entirely optional.

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

## Open questions

### Limitations

The approach described in this standard imposes the following limitations:

1. as a result of the "`identity:list_domains`" rule (see below), Domain Managers are able to see all domains[^5] via "`openstack domain list`" and can inspect the metadata of other domains with "`openstack domain show`"
2. as a result of the "`identity:list_roles`" rule (see below), Domain Managers are able to see all roles via "`openstack role list`" and can inspect the metadata of other roles with "`openstack role show`"

**As a result of points 1 and 2, metadata of all domains and roles will be exposed to all Domain Managers!**

If a CSP deems either of these points critical, they may abstain from granting the `"manager"` role to any user in a domain scope, effectively disabling the Domain Manager functionality. See [Impact](#impact).

[^5]: see the [corresponding Launchpad bug at Keystone](https://bugs.launchpad.net/keystone/+bug/2041611)

## Decision

A role named "`manager`" is to be created via the Keystone API and the policy adjustments quoted below are to be applied.

### Policy adjustments

The following policy has to be applied to Keystone in a verbatim fashion.
The only parts of the policy definitions that may be changed are:

1. The "`base_*`" definitions to align them to the correct OpenStack defaults matching the OpenStack release of the environment in case those differ from this template.
2. The "`is_domain_managed_role`" definition (see next section below).

```yaml
# SCS Domain Manager policy configuration

# Section A: OpenStack base definitions
# The entries beginning with "base_<rule>" should be exact copies of the
# default "identity:<rule>" definitions for the target OpenStack release.
# They will be extended upon for the manager role below this section.
"base_get_domain": "(role:reader and system_scope:all) or token.domain.id:%(target.domain.id)s or token.project.domain.id:%(target.domain.id)s"
"base_list_domains": "(role:reader and system_scope:all)"
"base_list_roles": "(role:reader and system_scope:all)"
"base_get_role": "(role:reader and system_scope:all)"
"base_list_users": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.domain_id)s)"
"base_get_user": "(role:reader and system_scope:all) or (role:reader and token.domain.id:%(target.user.domain_id)s) or user_id:%(target.user.id)s"
"base_create_user": "(role:admin and system_scope:all) or (role:admin and token.domain.id:%(target.user.domain_id)s)"
"base_update_user": "(role:admin and system_scope:all) or (role:admin and token.domain.id:%(target.user.domain_id)s)"
"base_delete_user": "(role:admin and system_scope:all) or (role:admin and token.domain.id:%(target.user.domain_id)s)"
"base_list_projects": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.domain_id)s)"
"base_get_project": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.project.domain_id)s) or project_id:%(target.project.id)s"
"base_create_project": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.project.domain_id)s)"
"base_update_project": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.project.domain_id)s)"
"base_delete_project": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.project.domain_id)s)"
"base_list_user_projects": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.user.domain_id)s) or user_id:%(target.user.id)s"
"base_check_grant": "(role:reader and system_scope:all) or ((role:reader and domain_id:%(target.user.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:reader and domain_id:%(target.user.domain_id)s and domain_id:%(target.domain.id)s) or (role:reader and domain_id:%(target.group.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:reader and domain_id:%(target.group.domain_id)s and domain_id:%(target.domain.id)s)) and (domain_id:%(target.role.domain_id)s or None:%(target.role.domain_id)s)"
"base_list_grants": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.user.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:reader and domain_id:%(target.user.domain_id)s and domain_id:%(target.domain.id)s) or (role:reader and domain_id:%(target.group.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:reader and domain_id:%(target.group.domain_id)s and domain_id:%(target.domain.id)s)"
"base_create_grant": "(role:admin and system_scope:all) or ((role:admin and domain_id:%(target.user.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:admin and domain_id:%(target.user.domain_id)s and domain_id:%(target.domain.id)s) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.domain.id)s)) and (domain_id:%(target.role.domain_id)s or None:%(target.role.domain_id)s)"
"base_revoke_grant": "(role:admin and system_scope:all) or ((role:admin and domain_id:%(target.user.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:admin and domain_id:%(target.user.domain_id)s and domain_id:%(target.domain.id)s) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.project.domain_id)s) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.domain.id)s)) and (domain_id:%(target.role.domain_id)s or None:%(target.role.domain_id)s)"
"base_list_role_assignments": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.domain_id)s)"
"base_list_groups": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.group.domain_id)s)"
"base_get_group": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.group.domain_id)s)"
"base_create_group": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.group.domain_id)s)"
"base_update_group": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.group.domain_id)s)"
"base_delete_group": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.group.domain_id)s)"
"base_list_groups_for_user": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.user.domain_id)s) or user_id:%(user_id)s"
"base_list_users_in_group": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.group.domain_id)s)"
"base_remove_user_from_group": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.user.domain_id)s)"
"base_check_user_in_group": "(role:reader and system_scope:all) or (role:reader and domain_id:%(target.group.domain_id)s and domain_id:%(target.user.domain_id)s)"
"base_add_user_to_group": "(role:admin and system_scope:all) or (role:admin and domain_id:%(target.group.domain_id)s and domain_id:%(target.user.domain_id)s)"

# Section B: Domain Manager Extensions

# classify domain managers with a special role
"is_domain_manager": "role:manager"

# specify a rule that whitelists roles which domain admins are permitted
# to assign and revoke within their domain
"is_domain_managed_role": "'member':%(target.role.name)s or 'load-balancer_member':%(target.role.name)s"

# allow domain admins to retrieve their own domain (does not need changes)
"identity:get_domain": "rule:base_get_domain or rule:admin_required"

# list_domains is needed for GET /v3/domains?name=... requests
# this is mandatory for things like
# `create user --domain $DOMAIN_NAME $USER_NAME` to correctly discover
# domains by name
"identity:list_domains": "rule:is_domain_manager or rule:base_list_domains or rule:admin_required"

# list_roles is needed for GET /v3/roles?name=... requests
# this is mandatory for things like `role add ... $ROLE_NAME`` to correctly
# discover roles by name
"identity:list_roles": "rule:is_domain_manager or rule:base_list_roles or rule:admin_required"

# get_role is needed for GET /v3/roles/{role_id} requests
# this is mandatory for the OpenStack SDK to properly process role assignments
# which are issued by role id instead of name
"identity:get_role": "(rule:is_domain_manager and rule:is_domain_managed_role) or rule:base_get_role or rule:admin_required"

# allow domain admins to manage users within their domain
"identity:list_users": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:base_list_users or rule:admin_required"
"identity:get_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_get_user or rule:admin_required"
"identity:create_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_create_user or rule:admin_required"
"identity:update_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_update_user or rule:admin_required"
"identity:delete_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_delete_user or rule:admin_required"

# allow domain admins to manage projects within their domain
"identity:list_projects": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:base_list_projects or rule:admin_required"
"identity:get_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:base_get_project or rule:admin_required"
"identity:create_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:base_create_project or rule:admin_required"
"identity:update_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:base_update_project or rule:admin_required"
"identity:delete_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:base_delete_project or rule:admin_required"
"identity:list_user_projects": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_list_user_projects or rule:admin_required"

# allow domain managers to manage role assignments within their domain
# (restricted to specific roles by the 'is_domain_managed_role' rule)
#
# project-level role assignment to user within domain
"is_domain_user_project_grant": "token.domain.id:%(target.user.domain_id)s and token.domain.id:%(target.project.domain_id)s"
# project-level role assignment to group within domain
"is_domain_group_project_grant": "token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.project.domain_id)s"
# domain-level role assignment to group
"is_domain_level_group_grant": "token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.domain.id)s"
# domain-level role assignment to user
"is_domain_level_user_grant": "token.domain.id:%(target.user.domain_id)s and token.domain.id:%(target.domain.id)s"
"domain_manager_grant": "rule:is_domain_manager and (rule:is_domain_user_project_grant or rule:is_domain_group_project_grant or rule:is_domain_level_group_grant or rule:is_domain_level_user_grant)"
"identity:check_grant": "rule:domain_manager_grant or rule:base_check_grant or rule:admin_required"
"identity:list_grants": "rule:domain_manager_grant or rule:base_list_grants or rule:admin_required"
"identity:create_grant": "(rule:domain_manager_grant and rule:is_domain_managed_role) or rule:base_create_grant or rule:admin_required"
"identity:revoke_grant": "(rule:domain_manager_grant and rule:is_domain_managed_role) or rule:base_revoke_grant or rule:admin_required"
"identity:list_role_assignments": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:base_list_role_assignments or rule:admin_required"


# allow domain managers to manage groups within their domain
"identity:list_groups": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or (role:reader and system_scope:all) or rule:base_list_groups or rule:admin_required"
"identity:get_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or (role:reader and system_scope:all) or rule:base_get_group or rule:admin_required"
"identity:create_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:base_create_group or rule:admin_required"
"identity:update_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:base_update_group or rule:admin_required"
"identity:delete_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:base_delete_group or rule:admin_required"
"identity:list_groups_for_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:base_list_groups_for_user or rule:admin_required"
"identity:list_users_in_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:base_list_users_in_group or rule:admin_required"
"identity:remove_user_from_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:base_remove_user_from_group or rule:admin_required"
"identity:check_user_in_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:base_check_user_in_group or rule:admin_required"
"identity:add_user_to_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:base_add_user_to_group or rule:admin_required"
```

Note that the policy file begins with a list of "`base_*`" rule definitions ("Section A").
These mirror the default policies of recent OpenStack releases.
They are used as a basis for the domain-manager-specific changes which are implemented in "Section B" where they are referenced to via "`or rule:base_*`" accordingly.
The section of "`base_*`" rules is meant for easy maintenance/update of default rules while keeping the domain-manager-specific rules separate.

> **Note:**
> The "`or rule:admin_required`" appendix to the rule definitions in "Section B" is included for backwards compatibility with environments not yet fully configured for the new secure RBAC standard[^6].

[^6]: [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

#### Specifying manageable roles via "`is_domain_managed_role`"

The "`is_domain_managed_role`" rule of the above policy template may be adjusted according to the requirements of the CSP and infrastructure architecture to specify different or multiple roles as manageable by Domain Managers as long as the policy rule adheres to the following:

- the "`is_domain_managed_role`" rule MUST NOT contain the "`admin`" role, neither directly nor transitively
- the "`is_domain_managed_role`" rule MUST define all applicable roles directly, it MUST NOT contain a "`rule:`" reference within itself

##### Example: permitting multiple roles

The following example permits the "`reader`" role to be assigned/revoked by a Domain Manager in addition to the default "`member`" and "`load-balancer_member`" roles.
Further roles can be appended using the logical `or` directive.

```yaml
"is_domain_managed_role": "'member':%(target.role.name)s or 'load-balancer_member':%(target.role.name)s or 'reader':%(target.role.name)s"
```

**Note regarding the `manager` role**

When adjusting the "`is_domain_managed_role`" rule a CSP might opt to also include the "`manager`" role itself in the manageable roles, resulting in Domain Managers being able to propagate the Domain Manager capabilities to other users within their domain.
This increases the self-service capabilities of the customer but introduces risks of Domain Managers also being able to revoke this role from themselves or each other (within their domain) in an unintended fashion.

CSPs have to carefully evaluate whether Domain Manager designation authority should reside solely on their side or be part of the customer self-service scope and decide about adding "`'manager':%(target.role.name)s`" to the rule accordingly.

## Related Documents

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
