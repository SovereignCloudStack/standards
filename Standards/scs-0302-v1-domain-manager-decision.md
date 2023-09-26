---
title: Domain Manager Decision Record
type: Decision Record
status: Draft
track: IAM
---

## Design Record

### Change the naming of the Domain Manager role

Decision Date: 2023-08-04

Decision Maker: SIG IAM

Decision: Role should be named "domain-manager" not "domain-admin".

Rationale: To avoid confusion with the unscoped admin role and to be inline with the upstream plan https://specs.openstack.org/openstack/keystone-specs/specs/keystone/2023.1/default-service-role.html

Links / Comments / References:

- [SIG IAM meeting protocol entry](https://input.scs.community/2023-scs-sig-iam#Domain-Admin-rights-for-SCS-IaaS-Customers-184)
- [issue commment about decision](https://github.com/SovereignCloudStack/issues/issues/184#issuecomment-1670985934)

### Extend domain management functionality to Keystone groups

Decision Date: 2023-08-04

Decision Maker: SIG IAM

Decision: The Domain Manager Standard configuration should cover the groups functionality of Keystone, allowing domain manager to manage groups in domains.

Rationale: The groups functionality is a desired IAM feature for customers.

Links / Comments / References:

- [SIG IAM meeting protocol entry](https://input.scs.community/2023-scs-sig-iam#Domain-Admin-rights-for-SCS-IaaS-Customers-184)
- [action item issue](https://github.com/SovereignCloudStack/issues/issues/383)

## Related Documents

- [Domain Manager Standard](https://github.com/SovereignCloudStack/standards/Standards/scs-0302-v1-domain-manager-role.md)
