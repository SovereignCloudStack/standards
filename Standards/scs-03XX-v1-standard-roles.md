---
title: SCS Standard Roles
type: Standard
status: Draft
track: IAM
---

## Introduction

SCS aims to provide a standardized role model for RBAC roles across all supported OpenStack API services that applies sensible and consistent permission sets based on a set list of roles defined by a standard.
It is closely guided by the OpenStack defaults.

## Terminology

The following special terms are used throughout this standard document:

| Term | Meaning |
|---|---|
| API | Application Programming Interface, often referring to the REST API interfaces provided by OpenStack and related services |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| RBAC | Role-Based Access Control[^1] established by OpenStack Keystone |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

## Motivation

The permission settings of OpenStack RBAC roles are configured in service-specific deployment configuration files (usually the respective "`policy.yaml`") in a rather static way and have to be carefully managed.
In contrast to many of OpenStack's IAM and IaaS resources, these settings cannot be changed via its API at runtime.
For this reason it is important to have a secure and sensible default configuration in SCS clouds that is both intuitive and flexible enough to cover all necessary use cases of permission models desired by CSPs and customers.

## Design Considerations

One key aspect of the design considerations for this standard is to be as close to the native (upstream) OpenStack role model and role definitions as possible to not introduce unnecessary complexity or divergence from OpenStack.
Meanwhile the standardized roles and permission sets should cover all scenarios and use cases that SCS deems necessary.

### Scope Enforcement Compatibility

The API policy library used by OpenStack (oslo.policy) introduced two new [configuration options](https://docs.openstack.org/oslo.policy/latest/configuration/#oslo-policy) during the [ongoing RBAC rework of OpenStack](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html):

- `enforce_scope`
- `enforce_new_defaults`

Using those new defaults and scope-enforcing options [will currently break](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html#the-issues-we-are-facing-with-scope-concept) orchestration tooling such as **OpenStack Heat** and Tacker.
Due to OpenStack Heat being a service supported by the SCS project, those conflicting options cannot be mandated by a SCS standard.

Some service-specific role sets currently found in OpenStack services can only be eliminated and streamlined with the general roles when those new options are enabled.
As a result, this standard cannot consider role models dependent on the aforementioned options due to their currently unresolved compatibility issues and must incorporate the service-specific role sets for the time being.
The affected services and roles are documented below.

#### Barbican Role Set

The Key Manager component Barbican [established a set of dedicated roles](https://docs.openstack.org/barbican/2024.1/admin/access_control.html#default-policy):

- key-manager:service-admin
- creator
- observer
- audit

This set of roles is Barbican-specific and not used by any other API.
It became deprecated during the [RBAC rework](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html) of OpenStack but is still included per default in recent OpenStack releases (as of the 2024.1 release).

Due to its deprecation it is possible to enable Barbican's use of the already established reader, member and admin roles instead.
This however requires the olso.policy options `enforce_scope` and `enforce_new_default` to be enabled, which are currently non-defaults and break compatibility with orchestration tooling, see above.

#### Octavia Role Set

The Load-Balancer-as-a-Service (LBaaS) component Octavia comes with a set of specific roles in its default API policy configuration:

- load-balancer_observer
- load-balancer_global_observer
- load-balancer_member
- load-balancer_quota_admin
- load-balancer_admin

This set of roles is Octavia-specific and not used by any other API.
However, Octavia also [officially supports alternative policy configurations](https://docs.openstack.org/octavia/2024.1/configuration/policy.html#openstack-default-roles-policy-override-file) that use the already established reader, member and admin roles instead.

Using the alternative configurations would streamline Octavia's policies with the rest of the services and reduce complexity as well as ambiguity in the global role model of this standard.

However, both of the alternative policy files that omit the Octavia-specific roles currently state "The [oslo_policy] `enforce_scope` and `enforce_new_defaults` must be `True`.".
This would mean enabling the new defaults and scope-enforcing options that currently break compatibility with orchestration tooling like explained above.

### Open questions

RECOMMENDED

## Standard

### Established Roles

This standard establishes the following roles in SCS clouds.

Core Roles:

- reader
- member
- manager
- admin
- service

Service-specific Roles:

- key-manager:service-admin
- creator
- observer
- audit
- load-balancer_observer
- load-balancer_global_observer
- load-balancer_member
- load-balancer_quota_admin
- load-balancer_admin
- ResellerAdmin
- heat_stack_user

#### Role Definitions

The following overview will explain the roles' purposes and target scopes.
Roles marked as "internal" are roles only meant to be assigned to technical user accounts intended for internal use by OpenStack services.

Core Roles:

| Role | Primary Target(s) | Purpose |
|---|---|---|
| reader | customer | read-only access to resources and information in the scope of authentication (e.g. project) |
| member | customer | similar to *reader* but extended by write access to resources in the scope of authentication (e.g. project) |
| manager | customer, CSP | slightly more elevated privileges than *member*, able to manage core resources or settings of a project or domain |
| admin | CSP | cloud-level global administrative access to all resources (cross-domain, cross-project) |
| service | internal | internal technical user role for service communication |

Service-specific Roles:

| Service | Role | Primary Target(s) | Purpose |
|---|---|---|---|
| Barbican | audit | customer | allows read-only access to metadata of secrets within a project; does not allow secret retrieval or decryption |
| Barbican | observer | customer | allows read-only access to secrets within a project, including retrieval and decryption |
| Barbican | creator | customer | allows access to, creation and deletion of secrets within a project, including retrieval and decryption |
| Barbican | key-manager:service-admin | CSP | management API access for the cloud administrator, e.g. for project quota settings |
| Octavia | load-balancer_observer | customer | access to read-only APIs |
| Octavia | load-balancer_global_observer | CSP | access to read-only APIs including resources owned by others |
| Octavia | load-balancer_member | customer | access to read and write APIs |
| Octavia | load-balancer_quota_admin | CSP | admin access to quota APIs only, including quota resources owned by others |
| Octavia | load-balancer_admin | CSP | admin access to all LB APIs including resources owned by others |
| Ceilometer | ResellerAdmin | internal | technical user of Ceilometer with access privileges in the object storage API to store statistics for metering |
| Heat | heat_stack_user | internal | assigned to technical user accounts resulting from other resources' creation in Heat templates |

## Related Documents

- [OpenStack Governance: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

## Conformance Tests

Conformance Tests, OPTIONAL
