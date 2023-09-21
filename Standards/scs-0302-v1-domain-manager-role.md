---
title: Domain Manager configuration for Keystone
type: Standard
status: Draft
track: IAM
---

## Introduction

SCS Clouds should provide a way to grant Domain Manager rights to SCS Customers which provides IAM self-service capabilities within an OpenStack domain.
This is not properly implemented in the default OpenStack configuration and requires specific adjustments to the Keystone identity management configuration.
To avoid conflict with the unscoped `admin` role in OpenStack we want to refer to this new role as "Domain Manager" (`domain-manager`).

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
| cloud admin | OpenStack user belonging to the cloud provider that possesses the `admin` role |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

### Impact

Applying this standard modifies the API policy configuration of Keystone and introduces a new global role to Keystone to enable IAM self-service for customers within a domain.
This IAM self-service allows special Domain Manager users within a domain to manage users, project, groups and role assignments.

The provisioning of such self-service capabilities using the new role works on a per-tenant (customer domain) basis and is up to the cloud provider, thus entirely optional.
Omitting the provisioning of Domain Manager users for customers will result in an OpenStack cloud that behaves identically to a configuration without the standard applied.

## Motivation

In the default configuration of Keystone, only users with the `admin` role may manage the IAM resources such as projects, groups and users and their relation through role assignments.
The `admin` role in OpenStack Keystone is not properly scoped when assigned within a domain or project only as due to hard-coded architectural limitations in OpenStack, a user with the `admin` role may escalate their privileges outside of their assigned project or domain boundaries.
Thus, it is not possible to properly give customers a self-service functionality in regards to project, group and user management with the default configuration.

To address this, this standard defines a new Domain Manager role in conjunction with appropriate Keystone API policy adjustments to establish a standardized extension to the default Keystone configuration allowing for IAM self-service capabilities for customers within domains.

### Desired Workflow

1. The cloud admin creates the desired domains for the customers for which IAM self-service capabilities are desired.
2. The cloud admin creates one or more users within each of the applicable domains and assigns the Domain Manager role to them. These users represent the Domain Managers of the corresponding domain.
3. The customer uses the Domain Manager users to manage (create, update, delete) users, projects, groups and corresponding role assignments within their domain.

## Design Considerations

- the Domain Manager role MUST support managing projects, groups and users within a specific domain
- the Domain Manager role MUST be properly scoped to a domain, it MUST NOT gain access to resources outside of its owning domain
- the Domain Manager role MUST NOT enable customers to manipulate existing roles or create new roles
- the Domain Manager role MUST only allow customers to assign specific non-administrative roles to their managed users, Domain Managers MUST NOT be able to abuse the role assignment functionalities to escalate their own privileges or those of other users

### Options considered

#### Re-using the existing `admin` role

As role assigments can be scoped to project, groups and domains the most obvious option would be to assign the existing `admin` role to users representing Domain Managers in a scoped fashion.

However, due to architectural limitations[^2] of the existing OpenStack implementation of roles, the `admin` role has a special meaning reaching beyond the RBAC checks done by Keystone and other OpenStack components.
This results in special permissions being granted to users possessing the role which ignore the project or domain scope of the role assignment.
This poses severe security risks as the proper scoping of the `admin` role is impossible.
**Due to this, this approach was discarded early.**

[^2]: [Launchpad bug: "admin"-ness not properly scoped](https://bugs.launchpad.net/keystone/+bug/968696)

#### Introducing a new role and API policy changes

OpenStack Keystone allows for new roles to be created via its API by administrative users.
Additionally, each OpenStack API's RBAC can be adjusted through an API policy file (`policy.yaml`) through olso-policy[^3], Keystone included.
The possibility of managing users, projects, role assignments and so on is regulated through Keystone's RBAC configured by its API policy file.

This means that by creating a new role and extending Keystone's API policy configuration a new Domain Manager role can be established that is limited to a specific subset of the Keystone API to be used to manage users, projects and role assignments within a domain.

[^3]: [OpenStack Documentation: Administering Applications that use oslo.policy](https://docs.openstack.org/oslo.policy/latest/admin/index.html)

## Open questions

### Limitations

The approach described in this standard imposes the following limitations:

1. as a result of the "`identity:list_domains`" rule (see below), Domain Managers are able to see all domains via "`openstack domain list`" and can inspect the metadata of other domains with "`openstack domain show`"
2. as a result of the "`identity:list_roles`" rule (see below), Domain Managers are able to see all roles via "`openstack role list`" and can inspect the metadata of other roles with "`openstack role show`"

**The result of points 1 and 2 is that the metadata of all domains and roles will be exposed to all Domain Managers!**

## Decision

A role named "`domain-manager`" is to be created via the Keystone API and the policy adjustments quoted below are to be applied.

### Policy adjustments

```yaml
# classify domain managers with a special role
"is_domain_manager": "role:domain-manager"

# specify a rule that whitelists roles which domain admins are permitted
# to assign and revoke within their domain
"is_domain_managed_role": "'member':%(target.role.name)s"

# allow domain admins to retrieve their own domain
"identity:get_domain": "(rule:is_domain_manager and token.domain.id:%(target.domain.id)s) or rule:admin_required"

# list_domains is needed for GET /v3/domains?name=... requests
# this is mandatory for things like
# `create user --domain $DOMAIN_NAME $USER_NAME` to correctly discover
# domains by name
"identity:list_domains": "rule:is_domain_manager or rule:admin_required"

# list_roles is needed for GET /v3/roles?name=... requests
# this is mandatory for things like `role add ... $ROLE_NAME`` to correctly
# discover roles by name
"identity:list_roles": "rule:is_domain_manager or rule:admin_required"

# allow domain admins to manage users within their domain
"identity:list_users": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:admin_required"
"identity:get_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:create_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:update_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:delete_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"

# allow domain admins to manage projects within their domain
"identity:list_projects": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:admin_required"
"identity:get_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:admin_required"
"identity:create_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:admin_required"
"identity:update_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:admin_required"
"identity:delete_project": "(rule:is_domain_manager and token.domain.id:%(target.project.domain_id)s) or rule:admin_required"

# allow domain managers to manage role assignments within their domain
# (restricted to specific roles by the 'is_domain_managed_role' rule)
"is_domain_user_project_grant": "token.domain.id:%(target.user.domain_id)s and token.domain.id:%(target.project.domain_id)s and rule:is_domain_managed_role"
"is_domain_group_project_grant": "token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.project.domain_id)s and rule:is_domain_managed_role"
"domain_manager_grant": "rule:is_domain_manager and (rule:is_domain_user_project_grant or rule:is_domain_group_project_grant)"
"identity:check_grant": "rule:domain_manager_grant or rule:admin_required"
"identity:list_grants": "rule:domain_manager_grant or rule:admin_required"
"identity:create_grant": "rule:domain_manager_grant or rule:admin_required"
"identity:revoke_grant": "rule:domain_manager_grant or rule:admin_required"
"identity:list_role_assignments": "(rule:is_domain_manager and token.domain.id:%(target.domain_id)s) or rule:admin_required"

# allow domain managers to manage groups within their domain
"identity:list_groups": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:get_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:create_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:update_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:delete_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:list_groups_for_user": "(rule:is_domain_manager and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:list_users_in_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s) or rule:admin_required"
"identity:remove_user_from_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:check_user_in_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
"identity:add_user_to_group": "(rule:is_domain_manager and token.domain.id:%(target.group.domain_id)s and token.domain.id:%(target.user.domain_id)s) or rule:admin_required"
```

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

Conformance Tests, OPTIONAL
