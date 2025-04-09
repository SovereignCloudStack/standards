---
title: "Provider Network Standard: Implementation Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-0126-v1-provider-networks.md
---

### Policy adjustment for restricting Networking RBAC

Per default, OpenStack's Networking API allows all user, regardless of role to change the accessibility of networking resources (e.g. networks, routers, security groups) to other projects.
Such shared resources are, without knowledge of the respective project IDs, indistinguishable from resources shared by the CSP, allowing malicious users to present networking resources to other client as coming from the provider.
The Provider Network Standard states that CSPs SHOULD restrict this functionality to administrators, which requires the following change to the `policy.yaml` file of the Neutron API[^rbac]:

```yaml
"create_rbac_policy": "rule:admin_only"
```

[^rbac]: [RBAC](https://docs.openstack.org/neutron/2024.1/admin/config-rbac.html#preventing-regular-users-from-sharing-objects-with-each-other)
