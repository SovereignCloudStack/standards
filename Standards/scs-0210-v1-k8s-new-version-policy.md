---
title: SCS K8S Version Policy for new Kubernetes versions
type: Standard
stabilized_at: 2023-02-07
obsoleted_at: 2024-02-08
status: Deprecated
track: KaaS
description: |
  The SCS-0210 standard outlines the expected pace at which providers should adopt new Kubernetes versions, aiming
  for alignment with the rapid development cycle of Kubernetes. Providers must offer the latest minor version within
  four months of its release and the newest patch version within a week, ensuring users have timely access to security
  updates, bug fixes, and features. The standard emphasizes the need for expedited updates for critical CVEs and
  expects providers to thoroughly test new versions before deployment.
---

## Introduction

Here we will describe how fast providers need to keep up with the upstream Kubernetes version.

To create a informed decision we summarize here the Kubernetes rules regarding versioning at the time of writing (2023-01-16):

Kubernetes usually provides about **3 minor** releases per year (see [Kubernetes Release Cycle][k8s-release-cycle]).

Patch release cadence is typically monthly. However, the first patches after the first minor release usually arrive 1-2 weeks after the first minor release
(see [Patch Release Cadence][k8s-release-cadence]).

As stated in [Kubernetes Support Period][k8s-support-period], in general the latest 3 minor versions are maintained by the Kubernetes project.
Every release will be maintained for about 14 months.
The first 12 months are the standard support period.
The remaining 2 months are only for:

- CVEs (under the advisement of the Security Response Committee)
- dependency issues (including base image updates)
- critical core component issues

## Motivation

Kubernetes is a fast-paced project.
We want to achieve that providers keep up to date with upstream and do not fall behind Kubernetes releases.
This ensures that users are able to upgrade their clusters to address security issues, bug fixes and new features when using SCS compliant clusters in regards of Kubernetes.
However, providers should have reasonable time to implement the new Kubernetes versions and test them.

## Decision

- Must provide latest minor version no later than 4 months after release
- Must provide latest patch version no later than a week after release
- Should be faster for critical CVEs (CVSS >= 8)
- Should be tested

## Related Documents

All important documents regarding versioning, releases, etc. for the official Kubernetes project can be found on the [Kubernetes Releases page][k8s-releases].

## Conformance Tests

The conformance test is written in the 'k8s-version-recency-check.py' script. The script requires the path to a valid
kubeconfig file, which should describe the k8s cluster under test. This can either be done by creating a config from
the also provided 'config.yaml.template' or by calling the test script with its cli arguments.

[k8s-releases]: https://kubernetes.io/releases/
[k8s-release-cycle]: https://kubernetes.io/releases/release/#the-release-cycle
[k8s-release-cadence]: https://kubernetes.io/releases/patch-releases/#cadence
[k8s-support-period]: https://kubernetes.io/releases/patch-releases/#support-period
