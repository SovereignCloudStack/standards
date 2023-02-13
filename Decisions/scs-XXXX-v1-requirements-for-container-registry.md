---
title: Requirements for container registry
type: Decision Record
status: Draft
track: KaaS
---

# Introduction  

A container registry is a repository or collection of repositories used to store and 
access container images. Container registries are used by the teams to store the 
results of build processes and to maintain freely available images. They're acting as 
the intermediary for sharing container images between systems. They could be connected 
directly to the container orchestration platforms like Docker and Kubernetes.

There are 2 types of container registries: public and private. Public registries are 
commonly used by individuals and smaller teams. However, once teams begin to scale up,
this can bring more complex security issues, e.g. privacy, and access control. 
A private container registry often comes with security scanning capabilities, 
role-based access control, and advanced management. These private registries could be
either hosted remotely or on-premises.

# Motivation

Our motivation is that there are use cases, where cloud service providers (CSP) would 
like to be able to offer customers to store and access their container images using 
the SCS-compliant private container registry. The specific use cases should be discussed,
but overall the CSPs could offer a private container registry as a service or the CSPs 
could offer a recipe for customers to deploy the private registry themselves utilizing 
the CSP infrastructure. In both cases, the private container registry should be 
SCS-compliant and should fulfill a set of needed requirements e.g. for security and 
privacy. 

The idea here and the purpose of this document is to specify what requirements a 
specific technical container registry implementation (i.e. software solution) needs to 
fulfill in the context of SCS.

The purpose of this document is also to select an appropriate container registry 
implementation that meets all defined requirements and makes an architectural 
decision on what implementation is fully SCS-compliant and recommended by the SCS.

# Design considerations

There are numerous features to look for when evaluating a container registry solution.
Our decision process goes through two main stages. 

1. [OSS health check](#oss-health-check)
2. [Required and desirable features check](#required-and-desirable-features-check)

The open-source software (OSS) health check does the first filter stage. This stage is 
crucial in the context of SCS and container registry implementation should pass it to 
promote itself to the second consideration stage. The second stage does an overview over
the feature set of open source container registry implementations and map out 
requirements (and nice-to-haves) against it to have a well-documented decision.

Note: Keep in mind that at the time of writing this document, we’ve made our best effort 
 to survey the container registry landscape based on publicly available materials.
 If you find something outdated (with respect to the time of writing this document) or
 outright erroneous, please submit a PR or raise an issue, and we’ll fix it right away.

## OSS health check

This section evaluates the health of the open-source projects that were selected from 
the currently available solutions. SCS-compliant software must fulfill all OSS health 
checks defined by the [OSS-Health](https://github.com/SovereignCloudStack/standards/blob/main/Design-Docs/OSS-Health.md) 
document. The main health checks are:
- Four Opens (code is fully open source, community is open and diverse, development 
  process is open, design process is open)
- Maturity
- Security
- Activity
- Lock-in risk assessment

Each selected OSS project is evaluated based on the above checks, and it is classified 
to one of three categories as follows:

- :heavy_check_mark: The project passed all OSS health checks and will be considered 
  further as a valid candidate.

- :grey_question: The project passed almost all OSS health checks. 
  There is a place for improvement, but the missing points are not crucial from the OSS 
  health check perspective. The project will be considered further as a valid candidate.

- :x: The project does not pass the OSS health checks. Some OSS health check 
  showstoppers have been found (e.g. open core software, not actively maintained). 
  The project is filtered at this stage and won't be considered further.

Refer to the list of evaluated projects with their classified categories and comments.

- :heavy_check_mark: [Harbor][harbor]
  - Harbor project meets all "four opens"
    - Source code is open and available under the [Apache 2 license](https://github.com/goharbor/harbor/blob/main/LICENSE)
    - Community is [open](https://github.com/goharbor/harbor#community, structured and 
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
    CNCF graduated project is considered stable, widely adopted and production-ready
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
      maintainers/contributors that differ over various companies, therefore the single 
      point of failure is not a case here
  
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

This section does an overview of the feature set of open source container registry 
implementations (which passed the OSS health stage above) and map out requirements 
(and nice-to-haves) against it. SCS-compliant software must be robust enough, to be able 
to operate under heavy load (e.g. high availability (HA) mode, federation, etc.) and 
the crucial feature is security.
We defined a set of required features that the container registry implementation must 
have and also a set of desirable (nice to have) features are defined and evaluated here. 


**Required features**

- Audit Logs
  - Ability to record use in auditable logs so that activity can be traced to a single user
- Authentication
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
  - Container registry is able to serve multiple tenants (projects, teams, namespaces)
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

Refer to the table of evaluated projects with their features. Note that only container
registry implementations that passed the OSS health stage (Harbor, Quay, and Dragonfly)
are evaluated here.

| Features                       | Harbor                                        | Quay                                                                | Dragonfly                |
|--------------------------------|-----------------------------------------------|---------------------------------------------------------------------|--------------------------|
| Audit Logs                     | ✓                                             | ✓                                                                   | ✗                        |
| Authentication                 | ✓ Local database, LDAP, OIDC, UAA             | ✓ Local database, LDAP, Keystone, JWT                               | ✓ Local database         |
| Authorization                  | ✓                                             | ✓                                                                   | ✓                        |
| Automation                     | ✓ Webhooks                                    | ✓ Webhooks, building images                                         | ✗                        |
| Vulnerability scanning         | ✓ Trivy, Clair                                | ✓ Clair                                                             | ✗                        |
| Content Trust and Validation   | ✓ Notary, Cosign                              | ✓ Cosign                                                            | ✗                        |
| Multi-tenancy                  | ✓                                             | ✓                                                                   | ✓                        |
| Backup and restore             | ✓                                             | ✓                                                                   | ✗                        |
| Monitoring                     | ✓ Prometheus metrics                          | ✓ Prometheus metrics                                                | ✓ Prometheus metrics     |
| HA mode                        | ✓                                             | ✓                                                                   | ✗                        |
| Registry replication           | ✓                                             | ✓                                                                   | ✓                        |
| Proxy cache                    | ✓                                             | ✓ Feature is in the technology preview stage (non production ready) | ✗                        |
| Quota management               | ✓ Based on storage consumption or image count | ✓ Based on storage consumption                                      | ✗                        |
| Garbage collection             | ✓                                             | ✓                                                                   | ✗                        |
| Retention policy               | ✓ Multiple tag retention rules                | ✓ Only tag expiration rules                                         | ✗                        |
| Additional supported artifacts | ✓ non-OCI Helm charts (ChartMuseum)           | ✗ (only OCI artifacts)                                              | ✓ Maven, YUM             |
| Integration possibilities      | ✓ Dragonfly (P2P), Kraken (P2P)               | ✗                                                                   | ✓ Harbor, Nydus, eStargz |

## Conclusion

A wide range of open-source container registry projects (Quay, Harbor, Dragonfly, 
Keppel, Portus, Kraken, etc.) has been carefully evaluated based on the two main 
factors that reviewed their open-source health as well as their range of supported 
features.

TODO 

# Decision

_Decision_


<!-- Frequently used references -->

[harbor]: https://github.com/goharbor/harbor
[dragonfly]: https://github.com/dragonflyoss/Dragonfly2
[projectquay]: https://github.com/quay/quay
