---
title: "SCS end-to-end testing: Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0128-v1-e2e-tests.md
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

## How to run Tempest against your cluster

_TODO_ provide step-by-step walkthrough here
