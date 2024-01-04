---
title: Requirements for container registries
type: Standard
status: Draft
track: KaaS
---

## Introduction

A container registry is an infrastructure service to enable storing and accessing container
images. Images can be pushed to the registry by e.g. Continuous integration pipelines and
be pulled from by runtime environments like Kubernetes clusters.

Container registries come in various forms, e.g. publicly accessible ones like Docker Hub or
self-hosted and cloud-hosted services. The latter examples may apply various access control
mechanisms to restrict access. Both solutions offer a wide range of features that may or may not
attract potential users and CSPs.

## Terminology

Cloud Service Provider (abbr. CSP)
  Entity that provides scalable computing resources

Identity Provider (abbr. IdP)
  System that creates, maintains, and manages identity information

## Motivation

This standard is motivated by different use cases identified through the topics in the SCS project.
One use case would be the offering of private registries for customers by CSPs, which means that a CSP could
offer private container registries either as a service or as a provided "recipe" to deploy a private registry
utilizing the CSPs infrastructure.
Another use case would be the selection of a registry for the SCS reference implementation.

The idea and purpose of this document is to specify what requirements a specific technical container
registry implementation (i.e. software solution) needs to fulfill for an SCS-compliant registry.

## Design considerations

There are numerous features that should be evaluated for a container registry solution.
It is important to assess the registries based on the requirements of the OSS health checks and
desired features defined by the SCS. The following two subsections show these requirements.

### OSS health check

It is important to evaluate the health of a project before even evaluating the project for its feature set.
A project should therefore fulfill all OSS health checks be defined by the
[OSS-Health](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/OSS-Health.md) document.
This document evaluates the health of the open-source projects that were selected from
the currently available solutions. The container registry software must fulfill all OSS
health checks defined below:

- Four Opens (code is fully open source, community is open and diverse, development process is open, design process is open)
- Maturity
- Security
- Activity
- Lock-in risk assessment

### Required and desirable features check

A container registry provides a specific feature set, which can be mapped out against the requirements
described in this section. The registry should generally be robust (e.g. operate under heavy load) and
secure in order to be acceptable for the SCS standard. Therefore, a required and optional feature set
were defined, to which a container registry must abide and be evaluated against.

#### Required features

- Audit Logs
  - ability to record use in auditable logs so that activity can be traced to a single user
- Authentication of system identities
  - support for authenticating system identities like Kubernetes clusters
  - possibly support for dynamic identity tokens from some IdP
- Authentication of users
  - support for multiple authentication systems (IdM integration)
  - user and user account management
- Authorization
  - role-based access control to ensure strict access controls
- Automation
  - integration with CI/CD tools e.g. via webhooks
- Vulnerability scanning
  - reveal security vulnerabilities in container images
- Content Trust and Validation
  - verify image authenticity before running
  - image signing
- Multi-tenancy
  - container registry is able to serve multiple tenants (projects, teams, namespaces)
  - implementation on the storage level, see e.g. [Keppel](https://github.com/sapcc/keppel#overview), which uses
    multi-tenant-aware storage drivers
- Backup and restore
  - possible strategies for disaster recovery and data migration scenarios
- Monitoring
  - observability is a key feature for operating a service in production so the container registry should expose key metrics
- HA mode
  - enable the possibility of system uptime, even if a failure of some sort could occur
- Registry replication
  - replication allows users to replicate container images between registries of the same instances and between registries of different instances as well
- Proxy cache (pull-through cache)
  - Proxy cache enables the use of a container registry to proxy and cache images from a target public or private registry
- Quota management
  - ability to control resource use of components or the whole registry
- Garbage collection
  - removing blobs from the filesystem when they are no longer referenced by a manifest
- Retention policy
  - reduce the number of image tags, many of which might not be required after a given time or once a subsequent image tag has superseded them

#### Desirable features

- Additionally supported artifacts
  - Additional artifacts that the registry is able to store in addition to OCI artifacts, e.g. Java, Node.js, or Python packages
- Integration possibilities
  - Ability to cooperate with another software solution in order to improve own feature set (e.g. integration of P2P solution for improving container image distribution (download speed and stability, high scalability, ...))
- Deployment capabilities
  - ways to deploy a container registry (only "official" ways are mentioned)
- Administration capabilities "as a code"
  - ability to manage container registry via "as a code" solutions, e.g. Ansible role

## Standard

It is very unlikely, that every Container registry can fulfill every requirement defined by this document, and probably
not all deployments require every feature listed here. The required feature set should therefore be carefully considered
by the provider of the registry. We nevertheless RECOMMEND using most of the feature set provided in this document.

If the features mentioned above are all considered, a possible registry solution SHOULD fulfill the majority of
the required features. But this is again dependent on the specific use case and the surrounding architecture.

## Related Documents

[OSS-Health](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/OSS-Health.md)
