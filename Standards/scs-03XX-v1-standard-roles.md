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
| IaaS | Infrastructure-as-a-Service |
| IAM | Identity and Access Management |
| RBAC | Role-Based Access Control[^1] established by OpenStack Keystone |

[^1]: [OpenStack Documentation: Role-Based Access Control Overview](https://static.opendev.org/docs/patrole/latest/rbac-overview.html)

## Motivation

The permission settings of OpenStack RBAC roles are configured in service-specific deployment configuration files (usually the respective "`policy.yaml`") in a rather static way and have to be carefully managed.
In contrast to many of OpenStack's IAM and IaaS resources, these settings cannot be changed via its API at runtime.
For this reason it is important to have a secure and sensible default configuration in SCS clouds that is both intuitive and flexible enough to cover all necessary use cases of permission models desired by CSPs and customers.

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
Due to their currently unresolved compatibility issues, they cannot be freely adopted without consequences.
If adoption proves to be unfeasible, role models dependent on the those oslo.policy options could not be considered and the service-specific role sets would need to be preserved for the time being.
The affected services and roles are documented below.

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
It became deprecated during the RBAC rework of OpenStack[^2] but is still included per default in recent OpenStack releases (as of the 2024.1 release).

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

To improve user experience and make the encryption features easily accessible, this standard should adjust the Key Manager API policies to extend permissions referencing the Barbican-specific "creator" role by the "member" role.
This offers users easy access to the Key Manager API and aligns the permission set with the future rework (as per `enforce_new_defaults`), because it will later replace the "creator" role by the "member" role entirely.

The "creator" role will be kept for compatibility reasons concerning service integration.
For example, the block storage service Cinder usually has a technical user in Keystone possessing the "creator" role in the "service" project.
Moving such service accounts to the "member" role could introduce undesired access patterns in other APIs that otherwise don't accept the "creator" role but offer a lot of functionality to the "member" role by default.

### Classification of the "manager" role

The current RBAC rework in upstream OpenStack[^2] describes a "project-manager" persona utilizing a "manager" role on project scope to perform more privileged operations than "member" (see "Phase 3" of the document).
This role is intended to be used across various OpenStack services.
As of the OpenStack release 2024.1 this role is not implemented in any of the core services yet, only in Ironic with `enforce_new_defaults` enabled[^4].

On the other hand, the SCS project is making use of this role to implement a Domain Manager persona (see the [SCS Domain Manager standard under "Related Documents"](#scs-domain-manager-standard)).

As a result, the "manager" role has no effect outside of the Keystone Identity API until phase 3 of the RBAC rework is implemented upstream and this standard is migrated to the proper use of `enforce_new_defaults`.
As such, it will be handled as a service-specific role for Keystone in this standard, not as a core role.
This is to ensure that the effective scope of the role in SCS clouds is clearly documented and communicated to users.
It might be elevated to a core role in future iterations of the standard when it is implemented in other services.

[^4]: [Implementation of the "manager" role in Ironic for the 2024.1 release](https://github.com/openstack/ironic/blob/stable/2024.1/ironic/common/policy.py#L76-L82)

### Open questions

#### Incorporating future upstream defaults into this standard

Due to the ongoing RBAC rework in upstream OpenStack[^2], not all changes which are to be introduced by it will be included in the first iteration of this standard to avoid prematurely adopting role and policy definitions which might still change before being stabilized or have unresolved compatibility issues with certain services.

This results in a need of keeping this standard in sync once the upstream rework finishes.
It is currently unknown when the upstream rework will conclude exactly and how this standard will need to be adjusted as a result.

This primarily concerns the new scoping and defaults in `oslo.policy`:

```ini
[oslo_policy]
enforce_new_defaults = True
enforce_scope = True
```

Not all OpenStack services enable these options yet.
Once those options default to `True` for additional services in a future OpenStack release, this standard must be updated to properly account for the resulting changes in policy and role defaults.
Due to the fact that the details on how the remaining compatibility issues will be addressed upstream are still unknown, the full implications on when and how this standard will need to be updated specifically remains an open question.
However, at the very least this will most likely result in the following changes to this standard:

- mandate the use of the new olso.policy options in all APIs
- remove the service-specific roles of Barbican and Octavia from the standard
- add the reader role to the core roles of this standard
- move the manager role from service-specific roles to core roles
- remove the design considerations sections related to the above
- if applicable, update any policy generation workflows to use the new role model

[^2]: [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

[^3]: [Current parameter defaults in `oslo_policy/opts.py` (2023-12-11)](https://github.com/openstack/oslo.policy/blob/a1e76258180002b288e64532676ba2bc2d1ec800/oslo_policy/opts.py#L26-L51)

## Standard

### Roles

This standard establishes the following roles in SCS clouds.
**Core Roles** MUST be present in the Identity API at all times.
**Service-specific Roles** MUST be present in the Identity API as long as the corresponding service (denoted in parentheses) is part of the infrastructure.

**Core Roles:**

- member
- admin
- service

**Service-specific Roles:**

- manager (Keystone)
- key-manager:service-admin (Barbican)
- creator (Barbican)
- observer (Barbican)
- audit (Barbican)
- load-balancer_observer (Octavia)
- load-balancer_global_observer (Octavia)
- load-balancer_member (Octavia)
- load-balancer_quota_admin (Octavia)
- load-balancer_admin (Octavia)
- ResellerAdmin (Swift + Ceilometer)
- heat_stack_user (Heat)

#### Role Definitions

The following overview will explain the roles' purposes and target scopes.
Roles marked as "internal" are roles only meant to be assigned to technical user accounts intended for internal use by OpenStack services.

Core Roles:

| Role | Primary Target(s) | Purpose |
|---|---|---|
| member | customer | read and write access to resources in the scope of authentication (e.g. project) |
| admin | CSP | cloud-level global administrative access to all resources (cross-domain, cross-project) |
| service | internal | internal technical user role for service communication |

Service-specific Roles:

| Service | Role | Primary Target(s) | Purpose |
|---|---|---|---|
| Keystone | manager | customer, CSP | slightly more elevated privileges than *member*, able to manage core resources or settings of a project or domain; currently this is limited to managing identity resources within a domain |
| Barbican | audit | customer | allows read-only access to metadata of secrets within a project; does not allow secret retrieval or decryption |
| Barbican | observer | customer | allows read-only access to secrets within a project, including retrieval and decryption |
| Barbican | creator | customer | allows access to, creation and deletion of secrets within a project, including retrieval and decryption, equal to the member role |
| Barbican | key-manager:service-admin | CSP | management API access for the cloud administrator, e.g. for project quota settings |
| Octavia | load-balancer_observer | customer | access to read-only APIs |
| Octavia | load-balancer_global_observer | CSP | access to read-only APIs including resources owned by others |
| Octavia | load-balancer_member | customer | access to read and write APIs |
| Octavia | load-balancer_quota_admin | CSP | admin access to quota APIs only, including quota resources owned by others |
| Octavia | load-balancer_admin | CSP | admin access to all LB APIs including resources owned by others |
| Swift | ResellerAdmin | Ceilometer (internal) | assigned to technical users of Ceilometer to integrate with Swift for access privileges in the object storage API to store statistics for metering |
| Heat | heat_stack_user | internal | assigned to technical user accounts resulting from other resources' creation in Heat templates |

### API Policies

TODO: what does the CSP need to adhere to when it comes to API policy configuration?

#### Key Manager API

For the Key Manager API, the policy rule called "creator" MUST be adjusted to incorporate the "member" role as shown below.
This can be achieved by adding the following entry to a `policy.yaml` for Barbican (usually located at "`/etc/barbican/policy.yaml`"):

```yaml
"creator": "role:creator or role:member"
```

Exemplary contents of a "`/etc/barbican/barbican.conf`":

```ini
[oslo_policy]
enforce_new_defaults = False
enforce_scope = False
policy_file = policy.yaml
```

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
