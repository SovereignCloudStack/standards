---
type: Decision Record
status: Draft
track: Global
version: 0
---

# Introduction

Using a cloud means using cloud services like S3 storage, DBaaS, container registries and many more.

*Sometimes*, such services are accessed directly by an human administrator. AuthN/AuthZ for this use case is covered by existing user management.

But: *Most of the time*, during normal operation, not humans, but machines/workloads access the cloud services.

# Motivation

## Situation prior to implementation of machine identities: AuthN

The usual implementation not based on identity is this: Human operators (mostly from customer side) fetch static application credentials and place them manually alongside the workload.

Effectively, this drives operators to maintain long lived, hard to rotate secrets. This not only means a lot of manual work, it also has a negative impact on the overall security posture.
While this is true even for a small number of workloads, the problem becomes worse with each existing workload and consumed service. [^1]

## Situation prior to implementation of machine identities: AuthZ

The usual implementation not based on identity is this: Undefined. Each service may have different kinds of authorization systems in place, but it is not possible to manage access in one place.

If machine/workload identities can be used for AuthN equally to user identities, further streamlining of AuthZ would become easier/possible, but this is not topic of this ADR.

## Use Cases

Essentially, any form of identity document needs to be accessible for workloads. Examples of such workload types include:

### Kubernetes Pods

With Kubernetes as primary means of deploying workloads, this most likely is the most important use case, enabling customers to use identities without the need to roll their own IdP infrastructure.

### (Virtual/Bare metal) machines

* Customers running their workloads on VM's instead of Kubernetes
* let Kubernetes nodes access PaaS container registry
* let Kubernetes nodes fetch [cluster certificates](https://github.com/SovereignCloudStack/issues/discussions/114)

# Considered options

* Implement Machine/Workload identity
    - settling wording, appending it to SCS glossary
* Do not plan to implement such concept
    - instead, try to give advice on non-identity-based best practices

Any details regarding these two options may be discussed in further proposals, but are not topic of this document.

[^1]: This process may be streamlined with tooling like Terraform or Ansible, but generally, the process remains the same. If renewal is kind-of automated by such tooling, it is mission critical to run it constantly, which is usually not what it is designed for.
