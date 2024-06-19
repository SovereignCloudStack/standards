---
title: "SCS KaaS default storage class: Implementation and Testing Notes"
type: Supplement
track: KaaS
status: Proposal
supplements:
  - scs-0211-v1-kaas-default-storage-class.md
---

## Introduction

The standard [SCS Kaas Default storage class](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0211-v1-kaas-default-storage-class.md)
wants to define the properties of a default `StorageClass` a Kubernetes cluster would rely on,
if a `PersistentVolumeClaim` doesn't provide a name for one during its creation.

## Implementation notes

A `StorageClass` is made default by using the `storageclass.kubernetes.io/is-default-class`
annotation; a standardized name is not given. `ReadWriteOnce` must be supported by the volume,
and it must be protected against data loss due to hardware failures.
Therefore, volumes must not be bound to the lifecycle of a Kubernetes node and, at best,
be backed by some kind of redundant storage.
Guarantees for latency, bandwidth, IOPS and so on are not given.

The cost-intensive part of this standard would be the hardware failure protection by binding
the `StorageClass` to redundant, non-lifecycle bound storage, since this would mean that
storage needs to be provided in a higher capacity to achieve the same usable capacity.

## Automated tests

### Notes

The test for the [SCS Kaas Default storage class](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0211-v1-kaas-default-storage-class.md)
checks if a default storage class is available and if this storage class can be used
to create a `PersistentVolume` from a `PersistentVolumeClaim` for a container.

### Errors and warnings

The test will return 0 precisely when it could be verified that the standard is satisfied.
Otherwise, different return codes are provided depending on the type of error.
These are as follows (taken from the test script):

- 1    Not able to connect to k8s api
- 31   Default storage class has no provisioner
- 32   None or more than one default Storage Class is defined
- 41   Not able to bind PersistentVolume to PersistentVolumeClaim
- 42   ReadWriteOnce is not a supported access mode

### Implementation

The script [`k8s-default-storage-class-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-default-storage-class/k8s-default-storage-class-check.py)
connects to an existing K8s cluster and checks for the availability of a default storage class.
This can also be done via Sonobuoy.

## Manual tests

None.
