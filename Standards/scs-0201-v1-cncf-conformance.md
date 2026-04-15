---
title: CNCF Kubernetes conformance
type: Standard
status: Draft
track: KaaS
description: |
  SCS-0201 describes conformance testing of Kubernetes environments using the upstream CNCF Kubernetes e2e suite.
---

## Introduction

Interoperability, consistency, and traceability play a crucial role in the deployment and use of a Kubernetes environment. Testing ensures this conformance across different Kubernetes environments.

The SCS project always intended to reuse existing standards whenever possible. For this reason, the upstream tooling of the [Certified Kubernetes Conformance Program](https://github.com/cncf/k8s-conformance) is used for conformance testing.

## Motivation

As an operator as well as an user, I want to check the conformance of a Kubernetes environment in order to ensure the interoperability, consistency, and traceability of it.

## Regulations

The conformance testing is performed as part of the [SCS compliance check suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests) executing the standard set of conformance tests defined by the `[Conformance]` tag in the [Kubernetes e2e suite](https://github.com/kubernetes/kubernetes/tree/master/test/e2e). All conformance tests MUST be passed successfully.

We allow exceptions from the Kubernetes e2e tests if it is reasonable, e.g. [bugs in certain tests][https://github.com/SovereignCloudStack/standards/blob/d07ee9f2e00b9d316d001cfe041dac36fde530ee/Tests/kaas/scs-sonobuoy-config-v1.yaml#L12]. Please note that exceptions may be added and/or removed in such reasonable cases and thereby allowing the standard to be updated without the need for a new version of it. If the reason for an exception goes away, so does the exception and it will therefore be removed.

The exceptions are listed under the key `okToFail` in
[Tests/kaas/scs-sonobuoy-config-v1.yaml](https://raw.githubusercontent.com/SovereignCloudStack/standards/refs/heads/main/Tests/kaas/scs-sonobuoy-config-v1.yaml).
