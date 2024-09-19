---
title: SCS Standard Roles
type: Standard
status: Draft
track: IAM
---

## Introduction

SCS aims to provide a standardized role model for Role-Based Access Control (RBAC) across all supported OpenStack API services.
The goal of this standard is to define IaaS roles for SCS clouds with sensible and consistent permission sets.
It is closely guided by the OpenStack defaults to achieve compatibility and interoperability.

:::note

The standard described below is only applicable to OpenStack releases 2024.2 or later.

:::

## Terminology

The following special terms are used throughout this standard document:

| Term | Meaning |
|---|---|
| API | Application Programming Interface, often referring to the REST API interfaces provided by OpenStack and related services |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| IaaS | Infrastructure-as-a-Service |
| IAM | Identity and Access Management |
| RBAC | Role-Based Access Control[^1] established by OpenStack Keystone |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

## Motivation

The permission settings of OpenStack RBAC roles are preconfigured in the OpenStack API implementations and can optionally be adjusted in service-specific deployment configuration files (usually the respective "`policy.yaml`") individually.
In contrast to many of OpenStack's IAM and IaaS resources however, these settings cannot be changed via its API at runtime, only via configuration files.
Changing these settings can also have a wide range of implications and requires careful testing and maintenance.
For these reasons it is important to have a secure and sensible default configuration in SCS clouds that is both intuitive and flexible enough to cover all necessary use cases of permission models desired by CSPs and customers.

## Design Considerations

One key aspect of the design considerations for this standard is to be as close to the native (upstream) OpenStack role model and role definitions as possible to not introduce unnecessary complexity or divergence from OpenStack.
Meanwhile the standardized roles and permission sets should cover all scenarios and use cases that SCS deems necessary.

Due to the high level of modularity and the large amount of available services for OpenStack clouds, this standard cannot address all possible manifestations of OpenStack clouds.
This standard will therefore only cover IaaS APIs and services that are classified as either mandatory or supported by the SCS project.

### Scope Enforcement Compatibility

The API policy library used by OpenStack (oslo.policy) introduced two new [configuration options](https://docs.openstack.org/oslo.policy/latest/configuration/#oslo-policy) during the ongoing RBAC rework of OpenStack[^2]:

- `enforce_scope`
- `enforce_new_defaults`

Using those new defaults and scope-enforcing options [will currently break](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html#the-issues-we-are-facing-with-scope-concept) orchestration tooling such as **OpenStack Heat** and Tacker.
This must be considered when making decisions in this standard.
Careful evaluation of benefits as well as implications of adopting these changes is necessary.
The new options are not adopted equally across all OpenStack services yet in context of the ongoing rework.

Some service-specific role sets currently found in OpenStack services can only be eliminated and streamlined with the general roles (reader, member etc.) when those new options are enabled.

[^2]: [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

#### Core Role Set

Independently from any service-specific roles, the set of core roles is fundamentally affected by the scope enforcement options as well.

The proper distinction between reader, member and manager roles is only fully implemented in all services when the `enforce_scope` and `enforce_new_defaults` oslo.policy options are used.
Otherwise the OpenStack APIs will oftentimes fall back to their earlier policy implementations which do not fully differentiate between reader, member and manager.

This results in more elevated permissions for users possessing the reader role than its role description suggests.
If this standard cannot mandate or expect the use of the aforementioned oslo.policy options due to their current compatibility issues as stated above, the usefulness of the reader role would be limited and unexpected behavior would be introduced when using it.
In such case, the standard should omit the reader role in its current state.

#### Barbican Role Set

The Key Manager component Barbican [established a set of dedicated roles](https://docs.openstack.org/barbican/2024.1/admin/access_control.html#default-policy):

- key-manager:service-admin
- creator
- observer
- audit

This set of roles is Barbican-specific and not used by any other API.
It became deprecated during the RBAC rework of OpenStack[^2].

Due to its deprecation it is possible to enable Barbican's use of the already established reader, member and admin roles instead.
This however requires the olso.policy options `enforce_scope` and `enforce_new_default` to be enabled.

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
This would require the new defaults and scope-enforcing options.

### Key Manager Role Model

The OpenStack policy defaults for the Key Manager service Barbican establish service-specific roles as documented above.
Unless the new scoping defaults (`enforce_new_defaults`) are used, this leads to users possessing the generic "member" role being unable to access the Key Manager API to create and manage secrets.
This in turn renders encryption features like the volume encryption of OpenStack's volume service unusable for customers unless the corresponding users are assigned the Barbican-specific "creator" role in projects additionally.
This creates unnecessary management overhead on the CSP side and ambiguity for users since the role is only useful in Barbican but its name does not communicate this.

To improve user experience and make the encryption features easily accessible, this standard should demand using the new role model and scoping defaults for the Key Manager API.

### Inclusion of the "manager" role

The current RBAC rework in upstream OpenStack[^2] describes a "project-manager" persona utilizing a new "manager" role on project scope to perform more privileged operations than "member" (see "Phase 3" of the document).
This role is intended to be used across various OpenStack services.
As of the OpenStack release 2024.1 this role is not implemented in any of the core services yet, only in Ironic with `enforce_new_defaults` enabled[^3].

On the other hand, the SCS project is making use of this role to implement a Domain Manager persona (see the [SCS Domain Manager standard under "Related Documents"](#scs-domain-manager-standard)).
This persona will be available as a native upstream feature in Keystone starting with the 2024.2 release of OpenStack.

As a result, the "manager" role has no effect outside of the Keystone Identity API until phase 3 of the RBAC rework is implemented upstream but can be used for identity-related functionality in Keystone.

[^3]: [Implementation of the "manager" role in Ironic for the 2024.1 release](https://github.com/openstack/ironic/blob/stable/2024.1/ironic/common/policy.py#L76-L82)

## Standard

### Roles

This standard establishes the following default roles in SCS clouds.
The roles mentioned below MUST be present in the Identity API at all times.

- reader
- member
- manager
- admin
- service

#### Role Definitions

The following overview will explain the roles' purposes and target scopes.
Roles marked as "internal" are roles only meant to be assigned to technical user accounts intended for internal use by OpenStack services.

Core Roles:

| Role | Primary Target(s) | Purpose |
|---|---|---|
| reader | customer | read-only access to resources in the scope of authentication (e.g. project) |
| member | customer | read and write access to resources in the scope of authentication (e.g. project) |
| manager | customer | identity self-service capability within a domain, to assign/revoke roles between users, groups and projects |
| admin | CSP | cloud-level global administrative access to all resources (cross-domain, cross-project) |
| service | internal | internal technical user role for service communication |

### API configuration

All API services MUST be configured to use the Secure RBAC role model by enabling `enforce_new_defaults` and `enforce_scope` of the oslo.policy library.

If custom policy rules are added to an API by a CSP the `policy_file` option of the oslo.policy library SHOULD be explicitly set to the name of the policy override file and not rely on the corresponding default path.

Example configuration entries:

```ini
[oslo_policy]
enforce_new_defaults = True
enforce_scope = True
policy_file = policy.yaml
```

#### API Policies

The following applies to all APIs that use RBAC policies:

- Custom policy rules MUST NOT extend the privileges of the core roles mentioned in this standard beyond their default permissions.
- If roles with custom permission sets are required, new roles and corresponding policies MAY be added as long as their names differ from the core roles and they do not impact the core roles.

The following applies only to the Octavia v2 LBaaS API:

- The scoping-compatible variant of [OpenStack Default Roles Policy Override File](https://docs.openstack.org/octavia/2024.1/configuration/policy.html#openstack-default-roles-policy-override-file) MUST be used as a base to align the LBaaS API with the standardized reader, member and admin role set.
  As of the 2024.1 release of Octavia, this template is provided as [keystone_default_roles_scoped-policy.yaml](https://github.com/openstack/octavia/blob/stable/2024.1/etc/policy/keystone_default_roles_scoped-policy.yaml).

## Related Documents

### SCS Mandatory and Supported IaaS Services

**Description:** SCS standard that lists mandatory and supported OpenStack APIs for SCS clouds.
This list is decisive for the standard on roles as all applicable services need to be taken into consideration.

**Link:** TBD <!-- https://github.com/SovereignCloudStack/standards/pull/587 -->

### SCS Domain Manager standard

**Description:** SCS standard that describes the Domain Manager role introduced by SCS and its configuration.

**Link:** [SCS Standards: Domain Manager configuration for Keystone](https://docs.scs.community/standards/scs-0302-v1-domain-manager-role)

### Consistent and Secure Default RBAC

**Description:** Upstream rework of the default role definitions and hierarchy across all OpenStack services.
Explains the reasoning for the `enforce_scope` and `enforce_new_defaults` options and the transition process.

**Link:** [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

## Conformance Tests

Conformance tests verify that the roles mandated by the standard exist and the Key Manager API adjustments are implemented.

There is a test suite in [`standard-roles-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iam/iaas-roles/standard-roles-check.py).
The test suite connects to the OpenStack API, queries the role list and verifies the behavior of the Key Manager API.
Please consult the associated [README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iam/iaas-roles/README.md) for detailed setup and testing instructions.
