---
title: "SCS KaaS default storage class: Implementation and Testing Notes"
type: Supplement
track: KaaS
status: Draft
supplements:
  - scs-0211-v1-kaas-default-storage-class.md
---

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

### Implementation

The script [`k8s-default-storage-class-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-default-storage-class/k8s-default-storage-class-check.py)
connects to an existing K8s cluster and checks for the availability of a default storage class.
This can also be done via Sonobuoy.

## Manual tests

None.
