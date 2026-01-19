---
sidebar_label: Tempest Testing Project
---

# Tempest Testing Project

Tempest is the OpenStack Integration Test Suite. It is a set of integration tests to be run against a live OpenStack cluster. Tempest has batteries of tests for OpenStack API validation, scenarios, and other specific tests useful in validating an OpenStack deployment.

## Official documentation

The official Tempest documentation is located on <https://docs.openstack.org/tempest/latest/>.

## Releases

The current Tempest releases and their supported OpenStack releases and python versions can be found on <https://docs.openstack.org/tempest/latest/supported_version.html>.

## OpenStack Powered Compute test cases

As SCS conformance tests are expected to be executable without admin privileges (see §2 of
[Regulations for achieving SCS-compatible certification](https://docs.scs.community/standards/scs-0004-v1-achieving-certification#regulations)), passing the following subset of OpenStack Powered Compute tests is sufficient to achieve _[SCS-compatible IaaS](https://docs.scs.community/standards/scs-compatible-iaas)_ compliance.

- [List of OpenStack Powered Compute non-admin tests](./tempest-tests-non-admin.lst)

## How to run Tempest against your cluster

_TODO_ provide step-by-step walkthrough here
