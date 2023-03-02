---
title: SCS K8S Version Policy for new Kubernetes versions
type: Standard
status: Stable
stabilized_at: 2023-02-07
track: KaaS
---

# Introduction

Here we will describe how fast providers need to keep up with the upstream Kubernetes version.

To create a informed decision we summarize here the Kubernetes rules regarding versioning at the time of writing (2023-01-16):

Kubernetes usually provides about **3 minor** releases per year.
[Kubernetes Release Cycle](https://kubernetes.io/releases/release/#the-release-cycle)

Patch release cadence is typically monthly. However, the first patches after the first minor release usually arrive 1-2 weeks after the first minor release.
[Patch Release Cadence](https://kubernetes.io/releases/patch-releases/#cadence)

In general the latest 3 minor versions are maintained by the Kubernetes project.
Every release will be maintained for about 14 months.
The first 12 months are the standard support period.
The remaining 2 months are only for:
- CVEs (under the advisement of the Security Response Committee)
- dependency issues (including base image updates)
- critical core component issues

[Kubernetes Support Period](https://kubernetes.io/releases/patch-releases/#support-period)

# Motivation

Kubernetes is a fast paced project.
We want to achieve that providers keep up to date with upstream and do not fall behind Kubernetes releases.
This ensures that users are able to upgrade their clusters to address security issues, bug fixes and new features when using SCS compliant clusters in regards of Kubernetes.
However, providers should have reasonable time to implement the new Kubernetes versions and test them.

# Decision

- Must provide latest minor version no later than 4 months after release
- Must provide latest patch version no later than a week after release
- Should be faster for critical CVEs (CVSS >= 8)
- Should be tested

# Related Documents

All important documents regarding versioning, releases, etc. for the official Kubernetes project can be found here: [Kubernetes Releases](https://kubernetes.io/releases/)

# Conformance Tests

TBD
