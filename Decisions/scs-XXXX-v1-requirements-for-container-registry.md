---
title: Requirements for container registry
type: Decision Record
status: Draft
track: KaaS
---

# Introduction  

A container registry is an infrastructure service to enable storing and accessing container
images. Images can be pushed to the registry by e.g. Continuous integration pipelines and
be pulled from by runtime environments like Kubernetes clusters.

Container registries could be publicly accessible e.g. Docker Hub, could be
self-hosted or hosted by cloud service providers (CSP). These container registries may
apply various access control mechanisms to restrict public access and make them private.
Both solutions offer a wide range of features that may or may not attract potential
users and CSPs.

# Motivation

This proposal is motivated by use cases in which CSPs would like to offer
private container registries to their customers. The specific use cases should be
discussed, but overall CSP could offer a private container registry as a service or
CSP could offer a recipe (maintained by SCS) for customers to deploy the private
registry themselves utilizing CSP infrastructure. In both cases, the private
container registry should fulfill a set of needed requirements e.g. for security and
privacy.

The idea and purpose of this document is to specify what requirements a
specific technical container registry implementation (i.e. software solution) needs to 
fulfill in the context of SCS.

Another purpose is the selection of an appropriate container registry
implementation that meets all defined requirements to make architectural
decision on what implementation will be used by the SCS.

# Design considerations

There are numerous features to look for when evaluating a container registry solution.
Our decision process goes through two main stages:

1. [OSS health check](#oss-health-check)
2. [Required and desirable features check](#required-and-desirable-features-check)

The open-source software (OSS) health check is the first filter stage. This stage is
crucial in the context of SCS and container registry implementation should pass it to
promote itself to the second consideration stage. The second stage provides an overview
over the feature set of open source container registry implementations and map out
requirements (and nice-to-haves) against it to have a well-documented decision.

Note: Keep in mind that at the time of writing this document, we’ve made our best effort 
 to survey the container registry landscape based on publicly available materials.
 If you find something outdated (with respect to the time of writing this document) or
 outright erroneous, please submit a PR or raise an issue, and we’ll fix it right away.

## OSS health check

This section evaluates the health of the open-source projects that were selected from 
the currently available solutions. The container registry software must fulfill all OSS
health checks defined by the [OSS-Health](https://github.com/SovereignCloudStack/standards/blob/main/Design-Docs/OSS-Health.md)
document. The main health checks are:
- Four Opens (code is fully open source, community is open and diverse, development 
  process is open, design process is open)
- Maturity
- Security
- Activity
- Lock-in risk assessment

Each selected OSS project is evaluated based on the above checks, and it is classified
into one of three categories as follows:

- :heavy_check_mark: The project passed all OSS health checks and will be considered 
  further as a valid candidate.

- :grey_question: The project passed almost all OSS health checks. 
  There is place for improvement, but the missing points are not crucial from the OSS
  health check perspective. The project will be considered further as a valid candidate.

- :x: The project does not pass the OSS health checks. Some OSS health check 
  showstoppers have been found (e.g. open core software, not actively maintained). 
  The project is filtered at this stage and won't be considered further.

Refer to the list of evaluated projects with their classified categories and comments.

- :heavy_check_mark: [Harbor][harbor]
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
      [KubeCon Europe](https://www.youtube.com/watch?v=MGNtPHQYP14), etc. 
  - Lock-in risk assessment 
    - The project's [maintainers](https://github.com/goharbor/community/blob/main/MAINTAINERS.md) 
      document shows that there are a sufficient number of core 
      maintainers/contributors that differ over various companies, we therefore deem
      the lock-in risk arising from a single point of failure to be low
  
- :heavy_check_mark: [Dragonfly][dragonfly]
  - Dragonfly project meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/dragonflyoss/Dragonfly2/blob/main/LICENSE)
    - Community is [open](https://github.com/dragonflyoss/Dragonfly2#community)
      organized via multiple channels e.g. Slack, mailing lists, etc.
      (#dragonfly Slack channel contains ~50 members)
    - The development process is open via GitHub issues and well described in the
      [contributing](https://github.com/dragonflyoss/Dragonfly2/blob/main/CONTRIBUTING.md) document
    - The design process is open via GitHub issues. The project's roadmap is available in
      the project's [webpage](https://d7y.io/docs/others/roadmap/#2022-roadmap)
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
    - The list of the project's [maintainers](https://github.com/dragonflyoss/Dragonfly2/blob/main/MAINTAINERS.md
      includes contributors from various companies and the [companies contributing dashboard](https://dragonfly.devstats.cncf.io/d/7/companies-contributing-in-repository-groups)
      shows that ~10 companies are actively contributing to a repository group

- :grey_question: [Project Quay][projectquay]
  - Project Quay meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/quay/quay/blob/master/LICENSE)
    - Community is [open](https://github.com/quay/quay#community) organized via mailing
      list and IRC
    - Development process is open via [JBoss JIRA](https://issues.redhat.com/projects/PROJQUAY/issues)
      issues and well described in the [governance](https://github.com/quay/quay/blob/master/GOVERNANCE.md) document
    - Design process is open via [JBoss JIRA](https://issues.redhat.com/projects/PROJQUAY/issues)
      issues. The project's roadmap is available on the project's [webpage](https://www.projectquay.io/#contribute)
  - Maturity
    - Project Quay is an open-source project that starts [~9 years ago](https://github.com/quay/quay/commit/0349af754204375d74ac5833713b607398981ff7).
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
      diversity across the companies. This should be improved

- :x: [Keppel](https://github.com/sapcc/keppel)
  - The project seems to be not widely used in a productive way and also the activity
    around is currently not on a good level (5+ contributors). The development 
    process as well as the design process seem to be open, but not documented yet

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

## Required and desirable features check

This section provides an overview of the feature set of open source container registry
implementations (which passed the OSS health stage above) and map out requirements 
(and nice-to-haves) against it. The container registry software must be robust enough,
to be able to operate under heavy load (e.g. high availability (HA) mode, federation, etc.) and
the crucial feature is security.
We defined a set of required features that the container registry implementation must 
have and also a set of desirable (nice to have) features are defined and evaluated here. 


**Required features**

- Audit Logs
  - Ability to record use in auditable logs so that activity can be traced to a single user
- Authentication of system identities
  - Support for authenticating system identities like Kubernetes clusters. Ideally supporting dynamic identity tokens from some IdP; Less ideal: Supporting static "system tokens"
- Authentication of users
  - Support for multiple authentication systems (IdM integration). User and user account management
- Authorization
  - Role-based access control to ensure strict access controls
- Automation
  - Integration with CI/CD tools e.g. via webhooks
- Vulnerability scanning
  - Reveal security vulnerabilities in container images
- Content Trust and Validation
  - Verify image authenticity before running - image signing
- Multi-tenancy
  - Container registry is able to serve multiple tenants (projects, teams, namespaces). It can be implemented also on the storage level, see e.g. [Keppel](https://github.com/sapcc/keppel#overview)
- Backup and restore
  - It is important for disaster recovery and data migration scenarios
- Monitoring
  - Observability is a key feature for operating a service in production so the container registry should expose key metrics
- HA mode
  - Ensure system uptime even in the event of a failure
- Registry replication
  - Replication allows users to replicate container images between registries of the same instances and between registries of different instances as well
- Proxy cache (pull-through cache)
  - Proxy cache allows you to use a container registry to proxy and cache images from a target public or private registry
- Quota management
  - Control over resource use
- Garbage collection
  - Removing blobs from the filesystem when they are no longer referenced by a manifest
- Retention policy
  - Reduce the number of image tags, many of which might not be required after a given time or once a subsequent image tag has superseded them

**Desirable features**

- Additionally supported artifacts
  - Additional artifacts that the registry is able to store in addition to OCI artifacts, e.g. Java, Node.js, or Python packages
- Integration possibilities
  - Ability to cooperate with another software solution in order to improve own feature set (e.g. integration of P2P solution for improving container image distribution (download speed and stability, high scalability ...))
- Deployment capabilities
  - How could be a container registry deployed (only "official" ways are mentioned)
- Administration capabilities "as a code"
  - Ability to manage container registry via "as a code" solutions, e.g. Ansible role

Refer to the table of evaluated projects with their features. Note that only container
registry implementations that passed the OSS health stage (Harbor, Quay, and Dragonfly)
are evaluated here.

| Features                            | Harbor                                 | Quay                                                                | Dragonfly                     |
|-------------------------------------|----------------------------------------|---------------------------------------------------------------------|-------------------------------|
| Audit Logs                          | ✓                                      | ✓                                                                   | ✗                             |
| Authentication of system identities | ✓ Robot Accounts                       | ✓ Robot Accounts                                                    | ✗                             |
| Authentication of users             | ✓ Local database, LDAP, OIDC, UAA      | ✓ Local database, LDAP, Keystone, JWT                               | ✓ Local database              |
| Authorization                       | ✓                                      | ✓                                                                   | ✓                             |
| Automation                          | ✓ Webhooks (HTTP, Slack)               | ✓ Webhooks (HTTP, Slack, E-mail ...), building images               | ✗                             |
| Vulnerability scanning              | ✓ Trivy, Clair                         | ✓ Clair                                                             | ✗                             |
| Content Trust and Validation        | ✓ Cosign                               | ✓ Cosign                                                            | ✗                             |
| Multi-tenancy                       | ✓ (not on the storage level)           | ✓ (not on the storage level)                                        | ✓ (not on the storage level)  |
| Backup and restore                  | ✓                                      | ✓                                                                   | ✗                             |
| Monitoring                          | ✓ Prometheus metrics, Tracing          | ✓ Prometheus metrics, Tracing (only for Clair)                      | ✓ Prometheus metrics, Tracing |
| HA mode                             | ✓                                      | ✓                                                                   | ✗                             |
| Registry replication                | ✓                                      | ✓                                                                   | ✓                             |
| Proxy cache                         | ✓                                      | ✓ Feature is in the technology preview stage (non production ready) | ✗                             |
| Quota management                    | ✓ Based on storage consumption         | ✓ Based on storage consumption                                      | ✗                             |
| Garbage collection                  | ✓ Non-blocking                         | ✓ Non-blocking                                                      | ✗                             |
| Retention policy                    | ✓ Multiple tag retention rules         | ✓ Only tag expiration rules                                         | ✗                             |
| Additional supported artifacts      | ✗ (only OCI artifacts)                 | ✗ (only OCI artifacts)                                              | ✓ Maven, YUM                  |
| Integration possibilities           | ✓ Dragonfly (P2P), Kraken (P2P)        | ✗                                                                   | ✓ Harbor, Nydus, eStargz      |
| Deployment capabilities             | ✓ Docker-compose, Helm chart, Operator | ✓ Docker-compose, Operator                                          | ✓ Docker-compose, Helm chart  |
| Administration capabilities         | ✓ Terraform, CRDs, Client libraries    | ✓ Ansible, Client libraries                                         | ✓ Client libraries            |

Notes:
- Automation: Harbor should support webhooks following CloudEvents spec in the [next release](https://github.com/goharbor/harbor/issues/17748)
- Content Trust and Validation: Harbor announced the deprecation of [Notary](https://github.com/goharbor/harbor/discussions/16612)
  integration, hence it is not mentioned in the table
- Multi-tenancy: Harbor, Quay, as well as Dragonfly, operates on a single storage
  backend (e.g. S3), i.e. the storage of container images is shared between tenants
- Additional supported artifacts: Harbor announced the deprecation of [Chartmuseum](https://github.com/goharbor/harbor/discussions/15057)
  integration, hence it is not mentioned in the table


## Conclusion

A wide range of open-source container registry projects (Quay, Harbor, Dragonfly,
Keppel, Portus, Kraken, etc.) has been carefully evaluated based on the two main
factors: the open-source health and range of supported features.

The open-source software health is crucial and container registry implementation should
pass it. The OSS health check evaluates several important metrics
of an open source software like whether the code/community/development/design is
fully open or whether the project's maturity, security, and activity are on the desired
level. This check also evaluates the lock-in risk due to possible single points of
failure or internal project conflicts and several other aspects.
Overall, three projects passed the OSS health checks:
- [Harbor][harbor]
- [Project Quay][projectquay]
- [Dragonfly][dragonfly]

The above projects were then evaluated from the "supported features" perspective.
The [Required and desirable features check](#required-and-desirable-features-check)
investigated the feature set of open-source container registry implementations and
mapped SCS requirements (and nice-to-haves) against it. The list of required features
is quite long and contains features that are primarily focused on security
(authentication, vulnerability scanning, content trust, and validation, etc.),
scalability (HA mode, registry replication, p2p integration, etc.) and visibility
(monitoring), see the full list [here](#required-and-desirable-features-check).
These requirements should ensure that the selected container registry implementation
could be offered by CSPs as a secure and enterprise-ready solution.

The following section compares projects Dragonfly, Quay, and Harbor.

[Dragonfly][dragonfly] is a healthy open-source project with a growing community
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

[Quay][projectquay] is an open-source project maintained by Red Hat. Its OSS health is
on a good level, the community around it is growing, and we consider it to be quite
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

[Harbor][harbor] is an outstanding open-source, community-led project with fully open and
well-documented processes. Its large and thriving community powers the fast-growing
feature set and attracts more and more developers and companies to active contributions.
Harbor’s CNCF graduation in 2020 made it one of the best choices for enterprise
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

# Decision

Based on the research and conclusion above we've decided to use the **Harbor** project
as a container registry implementation for the SCS ecosystem.


<!-- Frequently used references -->

[harbor]: https://github.com/goharbor/harbor
[dragonfly]: https://github.com/dragonflyoss/Dragonfly2
[projectquay]: https://github.com/quay/quay
