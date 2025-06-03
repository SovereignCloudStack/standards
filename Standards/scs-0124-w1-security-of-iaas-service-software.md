---
title: "SCS Standard for the security of IaaS service software: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-0124-v1-security-of-iaas-service-software.md
---

## Testing or Detecting security updates in software

It is not always possible to automatically test whether the software has the newest security updates.
This is because software versions may differ, or some CSPs might have added downstream code parts or be using other software than the reference.
Also vulnerabilities and their fixes are quite different in testing; some might not be testable while others are.
Additionally, testing might be perceived as an attack on the infrastructure.
So this standard will rely on the work and information CSPs must provide.
There are different cases and procedures, which are addressed in the following parts, that lead to compliance for this standard.

### Procedure to become compliant with the security of IaaS service software standard

This is the procedure when a new deployment wants to achieve SCS-conformancy.
There are two states such a deployment can be in:

1. When a deployment is newly built or installed, it usually uses software that includes all the latest security and bug fixes.
Such deployments should be considered compliant with the standard.

2. When a CSP aims to make an older deployment compliant with the SCS standards, it should be checked whether the running software is up-to-date and no known vulnerabilities are present.
Any updates or upgrades to even newer versions should be done before the SCS compliance for every other standard is checked.
Afterwards the CSP may provide information about the used software in an SBOM or otherwise should provide a notice about the deployment having integrated all necessary vulnerability patches.

### Procedure when new vulnerabilities are discovered

Whenever there are new vulnerabilities discovered in IaaS service software like OpenStack there is either an internal discussion ongoing or it is just a smaller issue.
In the first case, CSPs should have someone following such discussions and may even help prepare and test patches.
From the moment on the vulnerability is disclosed publicly, the risk of it being actively exploited increases greatly.
So CSPs MUST watch out for announcements like in the OSSAs and OSSNs and when they are affected, update their deployment within the following timeframes according to the severity of the issue:

1. Critical (CVSS = 9.0 – 10.0): 3 hours
2. High (CVSS = 7.0 – 8.9): 3 days
3. Mid (CVSS = 4.0 – 6.9): 1 month
4. Low (CVSS = 0.1 – 3.9): 3 months

Afterwards CSPs MUST provide a notice to the OSBA, that they are not or not any more affected by the vulnerability.
This can be done through either telling, what patches were integrated or showing configuration that renders the attack impossible.
It could also be provided a list of services, when the affected service is not used in that deployment.

