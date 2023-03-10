---
title: Harbor deployment
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

Various container registry open-source solutions have been evaluated in the architectural
decision record [Requirements for container registry](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0212-v1-requirements-for-container-registry.md).
It specified requirements for the container registry implementation that need to be
fulfilled in the context of SCS and also made an architectural decision on what
implementation should be used by the SCS for e.g. reference installation. As a result,
Harbor project has been selected as an appropriate container registry implementation for
the SCS ecosystem.

## Motivation

This proposal is motivated by use cases in which cloud service providers (CSP) would
like to offer private container registries to their customers. The specific use cases
should be discussed (see [Open questions](#open-questions)), but our assumption is that
there are use cases, where CSP offers a recipe (maintained by SCS) for customers to
deploy the private registry themselves utilizing CSP infrastructure or CSP offers
container registry as a service. In both cases, the target platform is the Kubernetes
cluster that operates on top of CSP IaaS.

The purpose of this document is to investigate Harbor deployment possibilities (for the
Kubernetes cluster as a target platform), compare their supported features, and then
make an architectural decision on what Harbor deployment strategy will be recommended by the SCS.

## Design Considerations

### Options considered

#### Harbor Helm Chart

[Harbor Helm][harbor-helm] project contains a helm chart for Harbor deployment to the
target Kubernetes cluster. Harbor helm chart package contains collections of template
files that describe the installation of Harbor fundamental services and related components
(e.g. databases) (see [Architecture-Overview-of-Harbor](https://github.com/goharbor/harbor/wiki/Architecture-Overview-of-Harbor) for further details).

The repository is located under the [goharbor](https://github.com/goharbor) GitHub
organization and the official Harbor documentation mentions it as a way to deploy
[Harbor on Kubernetes](https://goharbor.io/docs/edge/install-config/harbor-ha-helm/).
The project is driven and maintained by the Harbor community, and it is
up-to-date with the latest Harbor releases. Its ability to deploy and manage Harbor
components are listed below:

- Deploy Harbor fundamental services (e.g. portal, core, jobservice, etc.)
- Deploy Harbor fundamental services in HA mode
- Deploy Harbor data access layer (PostgreSQL, Redis). Object store
  deployment is not supported.
- Deploy Harbor services exposed with a load balancer
- Ability to upgrade the Harbor registry version

#### Harbor Operator

[Harbor Operator][harbor-operator] project provides a solution to deploy and manage a
full Harbor service stack including both Harbor fundamental components and their
relevant dependent services such as database, cache, and storage services to the target Kubernetes
cluster.

The repository is located under the [goharbor](https://github.com/goharbor) GitHub
organization. The project is driven and maintained by the Harbor's community, and it is
up-to-date with the latest Harbor releases. Its aim is to simplify the installation and
mainly Day 2 operations of Harbor. Its ability to deploy and manage Harbor
components are listed below:

- Deploy Harbor fundamental services (e.g. portal, core, jobservice, etc.)
- Deploy Harbor fundamental services in HA mode
- Deploy Harbor data access layer (PostgreSQL, Redis, object store)
- Deploy Harbor data access layer in HA mode
- Ability to upgrade the Harbor registry version
- [Day2 configurations](https://github.com/goharbor/harbor-operator/blob/master/docs/day2/day2-configurations.md),
  i.e. use custom resources (CR) to configure Harbor, e.g. auth mode, robot token duration,
  storage size per project, etc.

The current list of Day2 configuration options does not contain managing (e.g.
creation) of Harbor projects (tenants), but this feature and more are mentioned in the [roadmap](https://github.com/goharbor/harbor-operator/#future-features).

## Open questions

There are still some container registry related open questions that are currently under
discussion and should be answered by the SCS community. These open questions are
highly connected with this ADR.

1. [Which container registry use cases are relevant for CSPs?](https://github.com/orgs/SovereignCloudStack/discussions/295)

  Note: The following use cases have been proposed, and it seems that all of them are
  relevant for CSPs:

- As a CSP, I would like to offer a recipe (maintained by SCS) for my customers
  to deploy the private registry themselves utilizing the CSP infrastructure
- As a CSP, I would like to offer the whole container registry instance as-a-service per
  tenant. An administrative user for the registry is then provided for the tenant so that
  the requester can use said user to gain admin access to the container registry instance
- As a CSP, I would like to offer a dedicated container registry project
  as-a-service per user, i.e. a single multi-tenant capable container registry
  instance is shared across multiple tenants (users). The user is then
  an administrator of the container registry project

1. [Is the shared-storage model in Harbor a limitation for CSPs?](https://github.com/orgs/SovereignCloudStack/discussions/294)

## Decision

As the comparison [Helm-vs-Operators](./Helm-vs-Operators.md) pointed out,
the general advantage of the helm chart over the operator is that the helm chart only
depends on the helm tool and does not run its own code (beyond the template files). This
reduces the scope for bugs and the number of resources required to run them.
The operator could be prioritized if we need to manage many instances of software or
the operator allows managing operational tasks, i.e. Day2 tasks.

Ergo, the final decision highly depends on use cases we want to support.

In the case of use cases like:

- As a CSP, I would like to offer a recipe (maintained by SCS) for my customers
  to deploy the private registry themselves utilizing the CSP infrastructure
- As a CSP, I would like to offer a dedicated container registry project
  as-a-service per user, i.e. a single multi-tenant capable container registry
  instance is shared across multiple tenants (users). The user is then
  an administrator of the container registry project

, the **Harbor helm chart** is a recommended option, as we can expect a few instances of
Harbor. In addition, the operator does not currently support Harbor project (tenant)
management via CR, and in general the helm chart is the preferable option.

In the case of use cases like:

- As a CSP, I would like to offer the whole container registry instance as-a-service per
  tenant. An administrative user for the registry is then provided for the tenant so that
  the requester can use said user to gain admin access to the container registry instance

, the **Harbor operator** is a recommended option, as we can expect many instances of
Harbor and supported Day2 operational tasks may be beneficial here.

<!-- Frequently used references -->

[harbor-helm]: https://github.com/goharbor/harbor-helm
[harbor-operator]: https://github.com/goharbor/harbor-operator
