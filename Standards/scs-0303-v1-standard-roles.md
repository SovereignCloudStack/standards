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

### Limited scope of OpenStack services covered by this standard

Currently, SCS does not enforce a list of OpenStack components/services it covers and/or supports exactly.
This poses a challenge to this standard since each OpenStack service API has their own policy configuration where the role model of this standard must be applied to properly to be effective.
Due to this reason, this standard is limited to a generic approach and defining guidelines without addressing each applicable OpenStack service individually with detailed policy templates.

This leaves a bit of vagueness in the actual implementation of the standard by the CSP, who is left responsible for aligning the role model correctly for all deployed services. This limits the scope and reliability of the standard.
How this can be addressed in future iterations of the standard is still uncertain.

### Incorporating the new upstream defaults into this standard

Due to the ongoing RBAC rework in upstream OpenStack[^1], not all changes which are to be introduced by it will be included in the first iteration of this standard to avoid prematurely adopting role and policy definitions which might still change before being stabilized.
This results in a need of keeping this standard in sync once the upstream rework finishes.
It is currently unknown when the upstream rework will conclude exactly and how this standard will need to be adjusted as a result.

This primarily concerns the new scoping and defaults in `oslo.policy`:

```ini
[oslo_policy]
enforce_new_defaults = True|False
enforce_scope = True|False
```

As of the time of writing this standard, these options currently default to `False`[^4] for the most OpenStack services.
Once these options default to `True` for a list of all scs-supported services, the standard should be updated.
This standard should provide a unified usage of policies over all OpenStack services.

[^4]: [Current parameter defaults in `oslo_policy/opts.py` (2023-12-11)](https://github.com/openstack/oslo.policy/blob/a1e76258180002b288e64532676ba2bc2d1ec800/oslo_policy/opts.py#L26-L51)

## Decision

This standard establishes a set of roles consisting of current OpenStack defaults and the stable parts of the ongoing OpenStack RBAC rework[^1].
Since the stable parts of the rework are already included in recent OpenStack releases, they can be used as-is.

On a per-service basis, a CSP applying this standard MUST either
**a)** not configure a `policy.yaml` or `policy.json` file for the OpenStack service at all (i.e. using its defaults) or
**b)** use a custom `policy.yaml` file that adheres to the rules specified below.

If deploying custom `policy.yaml` files for individual OpenStack services, the CSP must adhere to the following rules:

- the default OpenStack roles (`admin`, `manager`, `member`, `reader`) MUST NOT be changed regarding their permissions
- for custom permission sets a new role MUST be added and the name of the role MUST NOT match with any of the existing default role defined by OpenStack (`admin`, `manager`, `member`, `reader` etc.) or the name `domain-manager`
- in case of Keystone, a `domain-manager` role MAY be added; in this case its definition MUST adhere to the Domain Manager SCS standard
- if at any point in time the OpenStack release is upgraded, the CSP MUST make sure that all custom policy overrides which affect the default roles (`admin`, `manager`, `member`, `reader` etc.) in the `policy.yaml` files are up-to-date and do not deviate from the defaults of the target OpenStack release

Adhering to these rules ensures a consistent and secure set of roles and permission sets a customer can expect across SCS-compliant infrastructures.

Furthermore, the CSP MUST ensure that the new defaults and scoping behavior of `oslo.policy` are disabled.
For this, the following entries in each OpenStack service configuration file (e.g. `keystone.conf` for Keystone) must be set to `False`:

```ini
[oslo_policy]
enforce_new_defaults = False
enforce_scope = False
```

### Policy default reference

To help with aligning custom policy overrides with an OpenStack release's defaults and avoiding any deviations when creating or updating policy adjustments, a CSP can use the following process to generate OpenStack policy templates using the `oslo.policy` library:

```bash
VIRTUALENV_PATH="/tmp/oslo_policy.venv"
OPENSTACK_RELEASE="2023.2"
OPENSTACK_SERVICE="keystone"

virtualenv --clear "${VIRTUALENV_PATH}"
source "${VIRTUALENV_PATH}/bin/activate"
pip3 install oslo.policy
GIT_URL="https://opendev.org/openstack/${OPENSTACK_SERVICE}.git"
pip3 install git+${GIT_URL}@stable/${OPENSTACK_RELEASE}

oslopolicy-policy-generator --namespace "${OPENSTACK_SERVICE}" \
    --output-file "${OPENSTACK_SERVICE}-policy.yaml"
```

(The variables `OPENSTACK_RELEASE` and `OPENSTACK_SERVICE` need to be adjusted according to the target OpenStack release and service the policy template is to be generated for. The directory specified by `VIRTUALENV_PATH` may be removed after using the generator.)

CSPs MAY take the entirety or a subset of the rules from these templates as a basis for custom policies as long as they adhere to the guideline specified by this standard.

### Roles

Applying the standard will result in the following roles being available:

| Role | Purpose |
|---|---|
| admin | CSP-exclusive cloud administrator possessing all privileges. |
| domain-manager\* | Manager within customer-specific domains. Is allowed to manage groups, projects and users within a domain. Used for IAM self-service by the customer. |
| manager[^5] | Allows access to administrating APIs for resources within projects. |
| member | Read/write access to resources within projects. |
| reader | Non-administrative read-only access to resources within projects. |

\* Roles that are currently specific to an SCS standard and diverge from the default set of OpenStack or its RBAC rework are marked with an asterisk.
Their existence in the infrastructure may depend on the application of the respective standard.

[^5]: [Introduced in the 2024.1 release](https://review.opendev.org/c/openstack/keystone/+/822601)

## Related Documents

### SCS Domain Manager standard

**Description:** SCS standard that describes the Domain Manager role introduced by SCS and its configuration.

**Link:** [SCS Standards: Domain Manager configuration for Keystone](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0302-v1-domain-manager-role.md)

### Consistent and Secure Default RBAC

**Description:** Upstream rework of the default role definitions and hierarchy across all OpenStack services (ongoing as of 2023).

**Link:** [OpenStack Technical Committee Governance Documents: Consistent and Secure Default RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html)

## Conformance Tests

This standard does not yet define conformance tests of its own due to the alignment with OpenStack defaults and the undefined scope of supported services.

OpenStack Keystone and its default roles can be tested using the RBAC tests of the [keystone-tempest-plugin](https://pypi.org/project/keystone-tempest-plugin/) for the [Tempest Integration Test Suite](https://opendev.org/openstack/tempest/).

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
