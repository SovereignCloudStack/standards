---
title: SCS K8S Node Software Recency
type: Standard
status: Draft 
track: KaaS
enhances: scs-0210-v2-k8s-version-policy.md
---

## Introduction

In [scs-0210](https://docs.scs.community/standards/scs-0210-v2-k8s-version-policy),
we require that latest patch versions for Kubernetes (k8s) to be
delivered soon after they are released. The motivation behind this is that the
latest k8s patches regularly address security-relevant issues, so the
availability of patch releases helps users to keep their clusters secure.

Current k8s patch versions are typically delivered via new node images which
contain the needed kubernetes components (kubelet etc.). However, while it is
best practice to keep node images lean and small, they necessarily contain
software beyond kubernetes which may create security risks for users. When
writing scs-0210, the assumption was that the new k8s patch version would be
delivered through a new node image that would contain the latest relevant
security patches for all other included components, especially the Operating
System kernel (typically Linux).

This expectation was not explicit and thus left room for interpretation and
was not a real requirement. Rather than adding it to the scs-0210 standard,
we capture it as a hard requirement in this new standard.

## Decision

In order to keep Kubernetes clusters safe, the node images need to contain
current patches for all relecvant security issues as they are available from
the upstream communities or Linux distributions. Users have the expectation
that moving to the latest Kubernetes patch version brings them not only all the
(security) fixes of the K8s patch but also all relevant available (security)
fixes at that point in time of other system components used on the k8s nodes.
SCS-compatible KaaS Operators need to fulfill this expectation.

In particular this means that SCS-compatible KaaS Operators need to ensure
that:

- Node images built and provided by them MUST only include software
  projects or Linux distributions that receive security maintenance.
- Node images MUST be rebuilt or otherwise patched when (or after) a new
  k8s patch version is provided by the KaaS operator and MUST include
  at least all relevant security fixes available at the point in time of
  the k8s patch release.

We RECOMMEND that SCS-compatible KaaS Operators are prepared to deliver fixes
to node images also outside of new k8s patch versions for urgent cases.

## Implementation notes

<!--This could be moved to a separate document-->

This requirement can be fulfilled by rebuilding node images for each new
k8s patch version and basing the build on a Linux distribution that is
under security manintenance, including all released (security) fixes
and avoiding including packages that are unmaintained. In general, it
is a good idea to avoid the inclusion of unnecessary software and provide
minimal and hardened node images.

If node images are registered as public or community images on an
SCS-compatible IaaS, the `build_date` property indicates that (at least)
all (security) fixes up to that date are included, see
[scs-0102](https://docs.scs.community/standards/scs-0102-v2-image-metadata).

Note that the qualifier "relevant" was used when requiring all released
security fixes to be included - this leaves the door open to prove that
a specific software vulnerability can not affect the security of the node
image and thus may be excluded without violating this standard. We would
require that the reasoning is done publicly to provide transparency towards
the customers and undergo the scrutiny of the IT security community, so
this should only really be used in very exceptional circumstances.

If the software on the K8s nodes is not delivered through images, the
operator still needs to ensure that the patches are applied and activated
no later than when the k8s patch version is applied.

## Related Documents

- SCS Kubernetes version policy standard [scs-0210](https://docs.scs.community/standards/scs-0210-v2-k8s-version-policy).
  This standard has a few references to the k8s lifecycle.
