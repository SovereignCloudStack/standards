---
title: "SCS Standard for the security of IaaS service software: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-XXXX-v1-security-of-iaas-service-software.md
---

## Testing or Detecting security updates in software

It is not always possible to automatically test, whether the software has the newest security updates.
This is because software versions may differ or some CSPs might have added downstream code parts or using other software than the reference.
Also vulnerabilites and their fixes are quite different in testing, some might not be testable while others are.
Additionally testing might be perceived as an attack on the infrastructure.
So this standard will rely on the work and information CSPs must provide.
There are different cases and procedures which are addressed in the following parts, that lead to compliance for this standard.

### Procedure to become compliant to the security of IaaS service software Standard

This is the procedure when a new deployment wants to achieve scs-conformancy.
There are two states such a deployment can be in:

1. When a deployment is newly build or installed it usually uses software which includes all the latest security and bug fixes.
Such deployments should be considered compliant to the standard.

2. When a CSP wants to make an older deployment compliant to the scs standards and thus also to this standard, it should be checked, whether the running software is up to date.
Any updates or upgrades to even newer versions should be done before the scs-compliance is checked.
Information about such updates or upgrade should be provided by the CSP.

### Procedure when new Vulnerabilites are discovered

Whenever there are new vulnerabilities discovered in IaaS service software like OpenStack there is either an internal discussion ongoing or it is just a smaller issue.
In the first case CSPs should have someone following such discussions and may even help preparing and testing patches.
From the moment on the vulnerability is announced it will be used by attackers.
So CSPs MUST watch out for announcements like in the OSSAs and OSSNs and when they are affected, update their deployment as soon as possible.

Afterwards CSPs MUST provide proof, that they are not or not anymore affected by the vulnerabilty.
This can be done through either a manual test or through showing the updated software service version or showing configuration that renders the attack impossible.
It could also be provided a list of services, when the affected service is not used in that deployment.
