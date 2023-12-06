---
title: SCS KaaS default storage class
type: Standard
status: Stable
stabilized_at: 2023-02-13
track: KaaS
description: |
  The SCS-0211 standard outlines the properties required for the default StorageClass in Kubernetes as a Service (KaaS).
  The standard ensures that the default StorageClass, identified by the "storageclass.kubernetes.io/is-default-class"
  annotation, supports the ReadWriteOnce access mode and protects volume data against loss due to single disk or
  host hardware failures.
---

## Introduction

Cluster consumers can request persistent storage via [`PersistentVolumeClaims`](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#persistentvolumeclaim-v1-core) which is provisioned automatically by cloud-provided automation.
Storage requirements may vary across use cases, so there is the concept of `StorageClasses`. `StorageClasses` define some set of storage properties. So, consumers can choose one of these depending on the use case.

[Kubernetes documentation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## Motivation

While often times, consumers will choose a `StorageClass` explicitly, usually, there is also a default `StorageClass` to fall back on in case it is _not_ chosen explicitly (that is, when `storageClassName` is not set on the `PersistentVolumeClaim`).

This document attempts to define the properties this default `StorageClass` should have.

## Decision

The default `StorageClass` is made default using the `storageclass.kubernetes.io/is-default-class` annotation, following [Kubernetes upstream](https://kubernetes.io/docs/tasks/administer-cluster/change-default-storage-class/). Hence, standardizing its name is not required for the intents of this standard.

### Required non-performance-related properties

- `ReadWriteOnce` must be a supported [access mode](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes)
- volume must be protected against data loss due to hardware failures of a single disk or host
- volume must not be bound to the lifecycle of a Kubernetes Node

Hence,

- ...volume must not be backed by local storage on the Kubernetes Node VM itself
- ...volume may be backed by some kind of redundant storage within an AZ, across hosts
- ...volume may be backed by some kind of redundant storage across AZ's

### Required performance-related properties

- _NO_ fixed guarantees regarding latency/bandwidth/IOPS/...

Generally, customers should be able to expect low-tier performance without pricing surprises.

## Related Documents

This document does not describe performance related properties.
This will be done in another document which is yet to be created.

## Conformance Tests

TBD
