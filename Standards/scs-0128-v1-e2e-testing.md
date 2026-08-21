---
title: SCS end-to-end testing
type: Standard
status: Draft
track: IaaS
description: |
  SCS-0128 describes standardized end-to-end testing. It was created to succeed
  the retired "OpenStack-powered Compute".
---

## Introduction

From the beginning of the SCS project, it was always intended to reuse and include
existing standards wherever appropriate, such as the Cloud-Native Computing Foundation's
"Certified Kubernetes Conformance Program" or the OpenStack Interop working group's
regulations regarding "OpenStack-powered Compute". Unfortunately, [the latter has been
retired in September 2025](https://opendev.org/openinfra/interop).
This standard is meant to carry on the torch.

## Motivation

SCS operators as well as SCS users want to be sure that the infrastructure services
work as expected.

## Regulations

The end-to-end testing is performed using [Tempest](https://docs.openstack.org/tempest/latest/index.html).

The required tests are listed in
[Tests/iaas/scs_0128_e2e_testing/tempest-tests-non-admin.lst](https://raw.githubusercontent.com/SovereignCloudStack/standards/refs/heads/main/Tests/iaas/scs_0128_e2e_testing/tempest-tests-non-admin.lst).

Tempest MUST NOT report any _failed_ test cases.

## Rationale

In continuation of the original OpenStack-powered Compute, the list of Tempest test cases [was extracted](https://gist.github.com/toothstone/9bf21ea1863ca94da39c0e970f3ad88b#file-refstack-to-tempest-py)
from [2022.11.json](https://opendev.org/openinfra/interop/src/commit/2a71585700b4141910dbd4139805e2c0e9c49a8e/guidelines/2022.11.json),
the latest available guidelines file.

The following well-founded alterations were made:

- testcases that require admin privileges were removed in line with general SCS principles,
- `tempest.api.identity.v3.test_users.IdentityV3UsersTest.test_user_account_lockout` was removed
  because it is irrelevant in the most common scenario with an external identity provider.
  ([decision](https://github.com/SovereignCloudStack/minutes/blob/main/sig-standardization/20260723.md))
