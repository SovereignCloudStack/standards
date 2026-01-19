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

The end-to-end testing is performed using [tempest](https://docs.openstack.org/tempest/latest/index.html).

The required tests are listed in [Tests/iaas/scs_0128_e2e_test/tempest-tests-non-admin.lst].
