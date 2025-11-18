---
title: Container registry for SCS standard implementation
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

A container registry is an infrastructure service to enable storing and accessing container
images. Images can be pushed to the registry by e.g. Continuous integration pipelines and
be pulled from by runtime environments like Kubernetes clusters.

In the standard document ["Requirements for container registries"], requirements for a
registry in the context of SCS were introduced. These are based on the principals, that
a usable project should be open source, active and feature-rich, especially with regard
to security.

## Terminology

Cloud Service Provider (abbr. CSP)
  Entity that provides scalable computing resources

Cloud Native Computing Foundation (abbr. CNCF)
  Organization that hosts and develops open source projects for cloud native computing

## Motivation

In order to provide a usable, complete experience for the SCS reference implementation, it must be decided
on a registry in accordance with requirements set by the ["Requirements for container registries"] standard
as well as other dependencies set by the SCS project, including the [OSS requirements](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/OSS-Health.md).

This document should finally lead to a decision about the container registry used as a reference implementation of the SCS container registry.

### Evaluated projects

A few open source projects were evaluated for this document in order to find suitable candidates
for the SCS reference implementation. These projects can be found in the following list of
evaluated projects with their classified categories and comments. An initial assessment was
done with the checks for [OSS healthiness](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/OSS-Health.md)
and a general overview of the features described in ["Requirements for container registries"], which enables
classifying the projects into one of three categories as follows:

- :heavy_check_mark: The project passed all OSS health checks and will be considered
  further as a valid candidate.

- :grey_question: The project passed almost all OSS health checks.
  There is place for improvement, but the missing points are not crucial from the OSS
  health check perspective. The project will be considered further as a valid candidate.

- :x: The project does not pass the OSS health checks. Some OSS health check
  showstoppers have been found (e.g. open core software, not actively maintained).
  The project is filtered at this stage and won't be considered further.

The following list contains these projects with a small assessment listed below them:

- :heavy_check_mark: [Harbor](https://github.com/goharbor/harbor)
  - Harbor project meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/goharbor/harbor/blob/main/LICENSE)
    - Community is [open](https://github.com/goharbor/harbor#community), structured and
      well organized via [workgroups](https://github.com/goharbor/community) and
      various communications channels e.g. Slack, mailing lists, etc.
      (#harbor Slack channel contains 3k+ members)
    - The development process is open via GitHub issues and well described in the
      [contributing](https://github.com/goharbor/harbor/blob/main/CONTRIBUTING.md)
      document
    - The design process is open via GitHub issues. Proposals are [public](https://github.com/goharbor/community/tree/main/proposals).
      The decision process is well described as well. The project's roadmap is
      available in the [roadmap](https://github.com/goharbor/harbor/blob/main/ROADMAP.md) document
  - Maturity is on the CNCF [graduation](https://www.cncf.io/projects/harbor/) level.
    CNCF graduated projects are considered to be stable, widely adopted and production-ready
  - Security
    - The security disclosure and response policy is well described in the project's
      [security](https://github.com/goharbor/harbor/blob/main/SECURITY.md) document
    - The code is reviewed within a standard PR process
  - Activity
    - 250+ contributors, 4k+ forks, 13k+ GitHub stars
    - The project has been [adopted](https://github.com/goharbor/harbor/blob/main/ADOPTERS.md)
      by many companies that run Harbor in their production environments
    - The project collaborates with other communities and projects
      (see [Partners of Harbor](https://goharbor.io/community/) section of the
      project's website)
    - The project is visible and actively contributes to various conferences, e.g.
      [FOSDEM 22](https://goharbor.io/blog/harbor-at-fosdem-2022/),
      [KubeCon Europe](https://www.youtube.com/watch?v=REgvBPH369M), etc.
  - Lock-in risk assessment
    - The project's [maintainers](https://github.com/goharbor/community/blob/main/MAINTAINERS.md)
      document shows that there are a sufficient number of core
      maintainers/contributors that differ over various companies, we therefore deem
      the lock-in risk arising from a single point of failure to be low

- :heavy_check_mark: [Dragonfly](https://github.com/dragonflyoss/Dragonfly2)
  - Dragonfly project meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/dragonflyoss/Dragonfly2/blob/main/LICENSE)
    - Community is [open](https://github.com/dragonflyoss/Dragonfly2#community)
      organized via multiple channels e.g. Slack, mailing lists, etc.
      (#dragonfly Slack channel contains ~50 members)
    - The development process is open via GitHub issues and well described in the
      [contributing](https://github.com/dragonflyoss/Dragonfly2/blob/main/CONTRIBUTING.md) document
    - The design process is open via GitHub issues. The project's roadmap is available in
      the project's [webpage](https://d7y.io/docs/next/) (select 'Roadmap' from menue).
  - Maturity is on the CNCF [incubating](https://www.cncf.io/projects/dragonfly/) level
    CNCF incubating project is considered stable and used in production by users with
    the healthy pool of contributors
  - Security
    - The security disclosure is handled via a dedicated email address
    - The code is reviewed within a standard PR process
  - Activity
    - 30+ contributors, 100+ forks, 1k+ GitHub stars
    - The project has been [adopted](https://github.com/dragonflyoss/Dragonfly2/blob/main/ADOPTERS.md)
      by many companies that run Harbor in their production environments
    - The project is visible and actively contributes to various conferences,
      e.g. [KubeCon North America](https://www.youtube.com/watch?v=LcxBgmmeA80),
      [KubeCon Europe](https://www.youtube.com/watch?v=MGNtPHQYP14), etc.
  - Lock-in risk assessment
    - The list of the project's [maintainers](https://github.com/dragonflyoss/Dragonfly2/blob/main/MAINTAINERS.md)
      includes contributors from various companies and the [companies contributing dashboard](https://dragonfly.devstats.cncf.io/d/7/companies-contributing-in-repository-groups)
      shows that ~10 companies are actively contributing to a repository group

- :grey_question: [Project Quay](https://github.com/quay/quay)
  - Project Quay meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/quay/quay/blob/master/LICENSE)
    - Community is [open](https://github.com/quay/quay#community) organized via mailing
      list and IRC
    - Development process is open via [JBoss JIRA](https://issues.redhat.com/projects/PROJQUAY/issues)
      issues and well described in the [governance](https://github.com/quay/quay/blob/master/GOVERNANCE.md) document
    - Design process is open via [JBoss JIRA](https://issues.redhat.com/projects/PROJQUAY/issues)
      issues. The project's roadmap is available on the project's [webpage](https://www.projectquay.io/#contribute)
  - Maturity
    - Project Quay is an open-source project that started [~9 years ago](https://github.com/quay/quay/commit/0349af754204375d74ac5833713b607398981ff7).
      It powers Red Hat enterprise products Red Hat Quay and Quay.io, which are used in
      a productive way by many. Therefore, the project's maturity is at the good level
  - Security
    - The security disclosure is handled via a dedicated email address
    - The code is reviewed within a standard PR process
  - Activity
    - 50+ contributors, 200+ forks, 2k+ GitHub stars
    - The project has been used by many [companies](https://www.projectquay.io) that
      run Quay in their production environments
  - Lock-in risk assessment
    - The project's owners/maintainers list is not publicly available and is stored in
      the [downstream repository](https://github.com/quay/quay-docs#how-do-i-set-up).
      Therefore, it is hard to distinguish the risk of project failure caused by low
      diversity across the companies. This should be improved.

- :x: [Keppel](https://github.com/sapcc/keppel)
  - The project seems to be not widely used in a productive way and also the activity
    around is currently not on a good level (5+ contributors). The development
    process as well as the design process seem to be open, but neither of them are
    documented yet.

- :x: [Nexus](https://github.com/sonatype/nexus-public)
  - Nexus is an **open core** software that offers paid [pro version](https://www.sonatype.com/products/repository-oss-vs-pro-features) with advanced features

- :x: [JFrog](https://jfrog.com/community/open-source/)
  - JFrog Artifactory is shipped as an **open core** [software](https://jfrog.com/community/open-source/)
    with limited features. The software is primarily offered as a paid [pro version](https://jfrog.com/pricing/#devops-onprem)

- :x: [Kraken](https://github.com/uber/kraken)
  - It seems that the project is not actively maintained as is discussed in the related
    project's [issue](https://github.com/uber/kraken/issues/313)

- :x: [Portus](https://github.com/SUSE/Portus)
  - It seems that the project is not actively maintained as is discussed in the related
    project's [issue](https://github.com/SUSE/Portus/issues/2352)

### Deeper look into selected projects

In the previous section, a wide range of open-source container registry projects (Quay, Harbor, Dragonfly,
Keppel, Portus, Kraken, etc.) has been carefully evaluated based on the two main
factors: the open-source health and range of supported features.

The open-source software health is crucial and container registry implementation should
pass it. It evaluates several important metrics of an open source software like whether the code/community/development/design
is fully open or whether the project's maturity, security, and activity are on the desired
level. This check also evaluates the lock-in risk due to possible single points of
failure or internal project conflicts and several other aspects.
Overall, three projects passed the OSS health checks:

- [Harbor](https://github.com/goharbor/harbor)
- [Project Quay](https://github.com/quay/quay)
- [Dragonfly](https://github.com/quay/quay)

The above projects were then evaluated from the "supported features" perspective.
The document ["Requirements for container registries"] provides a "Required and desirable features check", which
provides desired feature sets for open-source container registry implementations according to
SCS requirements (and nice-to-haves). The list of required features is quite long and contains
features that are primarily focused on security (authentication, vulnerability scanning, content trust, and validation, etc.),
scalability (HA mode, registry replication, p2p integration, etc.) and visibility (monitoring).
These requirements should ensure that the selected container registry implementation
could be offered by CSPs as a secure and enterprise-ready solution.

The following section compares the selected projects Dragonfly, Quay, and Harbor.

[Dragonfly](https://github.com/dragonflyoss/Dragonfly2) is a healthy open-source project with a growing community
and CNCF incubating maturity level. It is considered stable, and widely used by many
companies in their production environments. We currently see that it is not as
feature-rich as Harbor or Quay, hence it is not considered the best choice here.
It seems, that its main aim (currently) is to offer (an efficient, stable, and secure)
container distribution solution based on p2p technology. This improves download
efficiency and saves bandwidth across CSPs. It also offers integration possibilities
that allow one to use it as a p2p distribution network via a "preheat" API. This
integration was implemented in the Harbor project via Dragonfly "preheat" adapter, and
both parties may benefit from the integration. Harbor profits from Dragonfly's p2p
distribution capabilities and on the other hand the Dragonfly project profits from
Harbor's feature-rich container registry "frontend".

[Quay](https://github.com/quay/quay) is an open-source project maintained by Red Hat. Its OSS health is
on a good level, the surrounding community is growing, and we consider it to be quite
mature as it powers enterprise solutions like Red Hat Quay and Quay.io.
Besides this, there is still a place for OSS health improvement. It is hard to
distinguish the risk of project failure caused by low diversity across the companies
because the project's owners/maintainers list is not publicly available and is stored in
the Red Hat private repository.
Its feature set is impressive and this project fulfills all must-haves defined in
this document. Quay gives you security over your repositories with image
vulnerability scanning (Clair integration), content validation (Cosign integration),
and access controls. Harbor stands out here as it allows users to use also project Trivy
for vulnerability scanning. Project Quay also provides a scalable open-source
platform to host container images across any size organization. One drawback in
comparison to Harbor is that the proxy cache feature is still marked as a
[Technology Preview](https://docs.projectquay.io/use_quay.html#quay-as-cache-proxy),
hence this feature may not be completely production-ready yet. On the other hand,
the project Quay supports [building Dockerfiles](https://docs.projectquay.io/use_quay.html#build-support)
using a set of workers on e.g. Kubernetes. Build triggers, such as GitHub webhooks
can be configured to automatically build new versions of repositories when new code is
committed. This feature is not supported by the [Harbor project](https://github.com/goharbor/harbor/issues/6235).

[Harbor](https://github.com/goharbor/harbor) is an outstanding open-source, community-led project with fully open and
well-documented processes. Its large and thriving community powers the fast-growing
feature set and attracts more and more developers and companies to active contributions.
Harbor's CNCF graduation in 2020 made it one of the best choices for enterprise
customers that want to operate container registries securely and in a large scale.
Its community size, landscape, and CNCF graduation make a significant difference in
comparison to Quay's open-source health capabilities.
The list of supported features is also impressive. This project fulfills all must-haves
defined in this document and overcome project Quay with a production-ready proxy cache
feature and more options that the user may use in case of image vulnerability scanning.
In addition, Harbor profits from p2p distribution capabilities via integration of p2p
solutions like Kraken and Dragonfly. It is worth mentioning that Harbor, by design,
operates on a single storage backend (e.g. S3). It means that the storage of container
images is shared even when the Harbor instance serves multiple tenants. The same
approach is used in Quay and Dragonfly projects, but e.g. Keppel uses multi-tenant-aware
storage drivers instead so that each customer gets their own separate storage backend.
CSP that considers offering container registry "as a service" solution based on Harbor
should be aware of this shared storage backend architecture.

In the following table, the feature sets of the evaluated projects that passed the OSS health state
are listed and matched against. This enables a better understanding of the decision-making for this document.

| Features                            | Harbor                                  | Quay                                                                | Dragonfly                     |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------|-------------------------------|
| Audit Logs                          | ✓                                       | ✓                                                                   | ✗                             |
| Authentication of system identities | ✓ Robot Accounts                        | ✓ Robot Accounts                                                    | ✗                             |
| Authentication of users             | ✓ Local database, LDAP, OIDC, UAA       | ✓ Local database, LDAP, Keystone, JWT                               | ✓ Local database              |
| Authorization                       | ✓                                       | ✓                                                                   | ✓                             |
| Automation                          | ✓ Webhooks (HTTP, Slack)                | ✓ Webhooks (HTTP, Slack, E-mail ...), building images               | ✗                             |
| Vulnerability scanning              | ✓ Trivy, Clair                          | ✓ Clair                                                             | ✗                             |
| Content Trust and Validation        | ✓ Cosign                                | ✓ Cosign                                                            | ✗                             |
| Multi-tenancy                       | ✓ (not on the storage level)            | ✓ (not on the storage level)                                        | ✓ (not on the storage level)  |
| Backup and restore                  | ✓                                       | ✓                                                                   | ✗                             |
| Monitoring                          | ✓ Prometheus metrics, Tracing           | ✓ Prometheus metrics, Tracing (only for Clair)                      | ✓ Prometheus metrics, Tracing |
| HA mode                             | ✓                                       | ✓                                                                   | ✗                             |
| Registry replication                | ✓                                       | ✓                                                                   | ✓                             |
| Proxy cache                         | ✓                                       | ✓ Feature is in the technology preview stage (non production ready) | ✗                             |
| Quota management                    | ✓ Based on storage consumption          | ✓ Based on storage consumption                                      | ✗                             |
| Garbage collection                  | ✓ Non-blocking                          | ✓ Non-blocking                                                      | ✗                             |
| Retention policy                    | ✓ Multiple tag retention rules          | ✓ Only tag expiration rules                                         | ✗                             |
| Additional supported artifacts      | ✗ (only OCI artifacts)                  | ✗ (only OCI artifacts)                                              | ✓ Maven, YUM                  |
| Integration possibilities           | ✓ Dragonfly (P2P), Kraken (P2P)         | ✗                                                                   | ✓ Harbor, Nydus, eStargz      |
| Deployment capabilities             | ✓ Docker-compose, Helm chart, Operator  | ✓ Docker-compose, Operator                                          | ✓ Docker-compose, Helm chart  |
| Administration capabilities         | ✓ Terraform, CRDs, Client libraries     | ✓ Ansible, Client libraries                                         | ✓ Client libraries            |

Notes:

- Automation: Harbor should support webhooks following CloudEvents spec in the [next release](https://github.com/goharbor/harbor/issues/17748)
- Content Trust and Validation: Harbor announced the deprecation of [Notary](https://github.com/goharbor/harbor/discussions/16612)
  integration, hence it is not mentioned in the table
- Multi-tenancy: Harbor, Quay, as well as Dragonfly, operates on a single storage
  backend (e.g. S3), i.e. the storage of container images is shared between tenants
- Additional supported artifacts: Harbor announced the deprecation of [Chartmuseum](https://github.com/goharbor/harbor/discussions/15057)
  integration, hence it is not mentioned in the table

## Decision

Based on the requirements laid out in ["Requirements for container registries"], the OSS health check
and the possible software solutions presented in this document, it was decided to use the **Harbor** project
as the container registry for the SCS reference implementation.

## Related Documents

["Requirements for container registries"](scs-0212-v1-requirements-for-container-registries.md)
[harbor](https://github.com/goharbor/harbor)
[dragonfly](https://github.com/dragonflyoss/Dragonfly2)
[projectquay](https://github.com/quay/quay)
