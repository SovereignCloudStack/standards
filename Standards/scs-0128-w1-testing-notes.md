---
title: "SCS end-to-end testing: Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0128-v1-e2e-testing.md
---

## Tempest introduction

Tempest is the OpenStack Integration Test Suite. It is a set of integration tests to be run against a live OpenStack cluster. Tempest has batteries of tests for OpenStack API validation, scenarios, and other specific tests useful in validating an OpenStack deployment.

See also:

- [Official documentation](https://docs.openstack.org/tempest/latest/)
- [Current releases (with OpenStack/Python compatibility)](https://docs.openstack.org/tempest/latest/supported_version.html)

## Test cases

SCS conformance tests are expected to be executable without admin privileges (see §2 of
[Regulations for achieving SCS-compatible certification](https://docs.scs.community/standards/scs-0004-v1-achieving-certification#regulations)).
The list of test cases stated in the standard has been curated accordingly.

### Test cases that may be skipped

In general, test cases must not be skipped. However, well-founded exceptions are possible.
What counts as well-founded has to be decided on a case-by-case basis. So far, the following
exceptions have been agreed upon:

- `tempest.api.compute.servers.test_servers.ServersTestJSON.test_create_server_with_admin_password`
  this test only runs when Nova allows instances to be created with an initial admin password,
  which is not used for typical Un\*x VMs with injected ssh keys.
  It may or may not be necessary for certain non-Un\*x use cases; however, it poses a security risk,
  so we think this feature should not be mandatory.

  Note: Windows users could circumvent this feature by switching to cloud-ready images such as
  the [cloudbase.it](https://cloudbase.it/windows-cloud-images/) ones (no endorsement).

Further exceptions may be made in the future.

## How to run Tempest against your cluster

To support you in running Tempest, the SCS community has included it in the
[compliance check image](https://github.com/SovereignCloudStack/standards/pkgs/container/scs-compliance-check).
The image contains an initialized Tempest workspace at `/tempest`,
so you can mount your configuration files and run the tempest command there like so:
`tempest run --load-list /scs-compliance/iaas/scs_0128_e2e_testing/tempest-tests-non-admin.lst`

### Via the scs-verify Helm chart

[The scs-verify chart](https://gitlab.com/alasca.cloud/focis/experiments/scs-verify)
allows to quickly set up one-shot or recurring Tempest runs against any cloud you have access to,
not just K8s-based ones.

It provides an [opinionated configuration preset](https://gitlab.com/alasca.cloud/focis/experiments/scs-verify/-/blob/devel/values.yaml)
that aims to work on any SCS-compatible IaaS compliant cloud with minimal user input and setup.

You can also use its
[tempest.conf](https://gitlab.com/alasca.cloud/focis/experiments/scs-verify/-/blob/devel/templates/scs-0128-tempest-configmap.yaml?ref_type=heads)
and
[accounts.yaml](https://gitlab.com/alasca.cloud/focis/experiments/scs-verify/-/tree/devel?ref_type=heads#scs-0128-tempest-tests)
templates for your own non-Helm setup.
