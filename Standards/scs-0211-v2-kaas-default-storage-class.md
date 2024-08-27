---
title: SCS KaaS default storage class
type: Standard
status: Draft
replaces: scs-0211-v1-kaas-default-storage-class.md 
track: KaaS
description: |
  The SCS-0211 standard ensures that a default StorageClass with specific characteristics is available to KaaS users.
---

## Introduction

This is the standard v2 for SCS Release 7.

Cluster consumers can request persistent storage via [`PersistentVolumeClaims`][k8s-pvc], which is provisioned
automatically by cloud-provided automation.
Storage requirements may vary across use cases, so there is the concept of storage classes (`StorageClass`).
Storage classes define some set of storage properties and consumers can choose one of these depending on the use case.

## Motivation

A lot of third-party software, such as Helm charts, assume that a default storage class is configured.
Thus, for an out-of-the-box working experience, a SCS compliant Kubernetes cluster should come
preconfigured with a sensible default storage class providing persistent storage.

## Decision

A freshly provisioned Kubernetes cluster MUST have a default storage class, i.e., a `StorageClass`
object that is annotated with `storageclass.kubernetes.io/is-default-class=true` as described in the
[Kubernetes documentation][k8s-default-sc].
The name of this storage class is not standardized.

The persistent volumes (PV) provisioned by the provided default storage class MUST fulfill all
of the following properties:

- MUST support the `ReadWriteOnce` [access mode][k8s-accessmode].
- MUST NOT be backed by local or ephemeral storage.
- MUST NOT be bound to the lifecycle of a Kubernetes node.

The provisioned storage class MAY support volume expansion (`allowVolumeExpansion=true`).

### Recommended non-performance-related properties

The following recommendations cannot be checked without further ado and therefore do not represent hard requirement criteria.  Nevertheless, they are important prerequisites for ensuring data storage stability:

- `ReadWriteOnce` should be a supported [access mode](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes)
- volume should be protected against data loss due to hardware failures of a single disk or host
- volume should not be bound to the lifecycle of a Kubernetes Node

Hence,

- ...volume should not be backed by local storage on the Kubernetes Node VM itself
- ...volume may be backed by some kind of redundant storage within an AZ, across hosts
- ...volume may be backed by some kind of redundant storage across AZ's

- volumes that are not necessarily required to be failure-safe may be local/node-bound/non-redundant, possibly fast to run applications that take care of data durability and availability on application level

### Required performance-related properties

- _NO_ fixed guarantees regarding latency/bandwidth/IOPS/...
Generally, customers should be able to expect low-tier performance without pricing surprises.

## Previous standard versions

[Version v1 of this standard](scs-0211-v1-kaas-default-storage-class.md) did not enforce the
existence of a default storage class in a newly created cluster.


## Conformance Tests

TBD

[k8s-pvc]: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims
[k8s-default-sc]: https://kubernetes.io/docs/tasks/administer-cluster/change-default-storage-class/
[k8s-accessmode]: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes
