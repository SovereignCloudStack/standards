---
status: draft
---

# Implement Machine Identities

## Context and Problem Statement

Using a cloud means using cloud services like S3 storage, DBaaS, container registries and many more.

*Sometimes*, such services are accessed directly by an human administrator. AuthN/AuthZ for this use case is covered by existing user management.

But: *Most of the time*, during normal operation, not humans, but machines/workloads access the cloud services.
This kind of access is the topic of this ADR.

### AuthN

The usual implementation not based on identity is this: Human operators (mostly from customer side) fetch static application credentials and place them manually alongside the workload.

Effectively, this drives operators to maintain long lived, hard to rotate secrets. This not only means a lot of manual work, it also has a negative impact on the overall security posture.
While this is true even for a small number of workloads, the problem becomes worse with each workload and secret there are. [^1]

### AuthZ

The usual implementation not based on identity is this: Undefined. Each service may have different kinds of authorization systems in place, but it is not possible to manage access in one place.

If machine/workload identities can be used for AuthN equally to user identities, further streamlining of AuthZ would become easier/possible, but this is not topic of this ADR.

### Possible Implementations

#### Federation of `ServiceAccounts` from Kubernetes Workload Clusters

Kubernetes itself offers to use K8s `ServiceAccounts` identities outside of K8s itself: [Docs](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-issuer-discovery).
This way, Kubernetes Pods could use their native identity for AuthN towards cloud services.

With Kubernetes as primary means of deploying workloads, this most likely is the most important (partially user-facing) use case.

#### Make VM instances have some identity

Any secure means of passing down an identity document from the infrastructure layer to a virtual machine should be enough to satisfy most use-cases [^2].

Options to evaluate:

* Using cloud-init to provision a bootstrapping document, allowing the VM renewal of its identity document.
* Always serve a recent identity document via OpenStack metadata service
* Always serve a recent identity document via a file system mount

## Considered options

* Implement Machine/Workload identity (also settling wording, appending to SCS glossary)
    - Details may be determined in other ADR's
* Do not plan to implement such concept

[^1]: This process may be streamlined with tooling like Terraform or Ansible, but generally, the process remains the same. If renewal is kind-of automated by such tooling, it is mission critical to run it constantly, which is usually not what it is designed for.

[^2]: Use cases including: (1) Customers running their workloads on VM's instead of Kubernetes, (2) let Kubernetes nodes access PaaS container registry, (3) let Kubernetes nodes fetch [cluster certificates](https://github.com/SovereignCloudStack/issues/discussions/114)
