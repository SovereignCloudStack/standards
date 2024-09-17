---
title: Domain Manager implementation notes
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0302-v1-domain-manager-role.md
---

## Implementation notes

:::caution

If a Keystone release of OpenStack 2024.2 or later is used, **the policy configuration described in this document MUST be removed again** in case it was applied in the past prior to the upgrade.

:::

:::info

The implementation described in this document only applies to Keystone releases prior to the OpenStack release 2024.2 ("Dalmatian").
This document describes a transitional solution to offer the Domain Manager functionality for SCS clouds based on an OpenStack release earlier than 2024.2.

Beginning with the 2024.2 release of OpenStack, the Domain Manager persona is integrated natively into Keystone and the implementation described below is unnecessary and might conflict with the native implementation.

:::

### Policy adjustments

The following policy can be applied to Keystone releases older than 2024.2 ("Dalmatian").
It mimics the Domain Manager persona implemented by Keystone starting with version 2024.2 and makes the functionality available for earlier releases of Keystone.

The only parts of the policy definitions below that may be changed are:

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
> The "`or rule:admin_required`" appendix to the rule definitions in "Section B" is included for backwards compatibility with environments not yet fully configured for the new secure RBAC standard[^1].

[^1]: [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

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

### Impact

Applying this implementation modifies the API policy configuration of Keystone and introduces a new persona to Keystone to enable IAM self-service for customers within a domain.
Once assigned, this persona allows special Domain Manager users within a domain to manage users, project, groups and role assignments as part of the IAM self-service.

However, the configuration change introduced by this implementation does not automatically assign the Domain Manager persona to any users per default.
Assigning the new persona and granting customers the resulting self-service capabilities is a deliberate action to be taken by the CSP on a per-tenant (i.e. per domain) basis.

Omitting the provisioning of any Domain Manager users (i.e. not assigning the new persona to any user) will result in an OpenStack cloud that behaves identically to a configuration without the implementation applied, making the actual usage of the functionality a CSP's choice and entirely optional.

#### Security implications

As a result of the "`identity:list_roles`" rule (see above), Domain Managers are able to see all roles via "`openstack role list`" and can inspect the metadata of any role with "`openstack role show`"
