---
title: SCS K8S Version Policy
type: Standard
status: Draft
track: KaaS
---

## Introduction

The Kubernetes project maintains multiple release versions including their patched versions.
In the project, the three most recent minor releases are actively maintained, with a fourth
version being in development. As soon as a new minor version is officially released,
the oldest version is dropped out of the support period.
Kubernetes supports its releases for around 14 months. 12 of these are the standard
support period. The remaining 2 months are the end-of-life support period for things like:

- CVEs (under the advisement of the Security Response Committee)
- dependency issues (including base image updates)
- critical core component issues

More information can be found under [Kubernetes Support Period].

The Kubernetes release cycle is set around 4 months, which usually results in about
**3 minor** releases per year [Kubernetes Release Cycle](https://kubernetes.io/releases/release/#the-release-cycle).

Patches to these releases are provided monthly, with the exception of the first patch,
which is usually provided 1-2 weeks after the initial release [Patch Release Cadence](https://kubernetes.io/releases/patch-releases/#cadence).

## Motivation

Kubernetes is a living, fast-paced project, which follows a pre-defined release cycle.
This enables forward planning with regards to releases and patches, but also implies a
necessity to upgrade to newer versions quickly, since these often include new features,
important security updates or especially if a previous version falls out of the support
period window.

We want to achieve an up-to-date policy, meaning that providers should be mostly in
sync with the upstream and don't fall behind the official Kubernetes releases.
This is achievable, since new versions are released periodical on a well communicated
schedule, enabling providers and users to set up processes around it.
Being up to date ensures that security issues and bugs are addressed and new features
are made available when using SCS compliant clusters.

It is nevertheless important to at least support all Kubernetes versions that are still
inside the support period, since users could depend on specific versions or may need
longer to upgrade their workloads to a newer version.

The standard therefore should provide a version recency policy as well as a support
window period.

## Decision

In order to keep up-to date with the latest Kubernetes features, bug fixes and security improvements,
the provided Kubernetes versions should be kept up to date with the upstream.

- The latest minor version MUST be provided no later than 4 months after release.
- The latest patch version MUST be provided no later than 1 week after release.
- This time period MUST be even shorter for patches that target critical CVEs (CVSS >= 8).
  It is RECOMMENDED to provide a new patch version in a 2 day time period after their release.
- New versions MUST be tested before being rolled out on productive infrastructure;
  at least the CNCF E2E tests should be passed beforehand.

At the same time, providers must support Kubernetes versions at least as long as the
official sources as mentioned in the [Kubernetes Support Period](https://kubernetes.io/releases/patch-releases/#support-period).

- Kubernetes versions MUST be supported as long as the official sources support them.
  The current support period can therefore be found in [Kubernetes Support Period].
- It is RECOMMENDED to not support versions after this period in order to not encourage
  usage of out-of-date versions.

## Related Documents

All documents regarding versioning, releases, etc. for the official Kubernetes projects can be found here:
[Kubernetes Releases](https://kubernetes.io/releases/)
[Kubernetes Support Period](https://kubernetes.io/releases/patch-releases/#support-period)
[Kubernetes Release Cycle](https://kubernetes.io/releases/release/#the-release-cycle)
[Patch Release Cadence](https://kubernetes.io/releases/patch-releases/#cadence)

## Validation / Conformance

*This section will be updated when the conformance tests are written.*
