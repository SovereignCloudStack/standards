title: SSD Flavors
type: Decision Record
status: Draft
track: IaaS
version: v0.1
enhances: scs-xxxx-v1-flavor-naming.md

# Introduction

SCS defines an IaaS Flavor Naming standard that mandates a number of standard flavors
to be available in each SCS-compliant IaaS offering. While offering or exposing
IaaS is not a requirement for SCS-compliant infrastructure offerings -- SCS allows
for platforms only exposing the container layer (plus S3 compatible object storage)
for gen2 (container-based) cloud-native workloads --
the SCS reference implementation does include a complete IaaS implementation that
many providers want to expose as they have customers desiring access at this layer
for gen1 (VM-based) cloud-native workloads or for the virtualization of more
classical (not cloud-native) workloads. The IaaS implementation thus comes with
standards.

This Decision Record is about adding a few mandatory flavors on the IaaS level
that include flavors with local SSD (or better) storage.

# Motivation

The [currently defined standard flavors](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/flavor-naming.md)
(as of v1.1 from 2022-09-08) do not include
flavors that use local storage. For certain workloads such as big data (hadoop),
databases, local storage is highly desirable as replication may be handled at
the application layer, making replication/redudancy in a networked storage solution
(ceph in the SCS reference implementation) an unneeded and undesired property.
Furthermore, write access to networked and replicated storage typically incurs
a certain latency, as the writes can only be acknowledged once all the replicas
have confirmed that the data has hit stable storage. Write latency is critical
for e.g. relational database performance.

The main purpose for the IaaS layer in SCS is to perform as a solid foundation
to provide and manage kubernetes container clusters in a multi-tenant scenario.
As such the standards at the IaaS layer should ensure that all the needed
types of resources are available for the container clusters. This is not
currently the case: In a scenario with multiple k8s control-plane nodes set
up via kubeadm (as part of the k8s cluster-api automation), the control plane
nodes each run an etcd instance and together form an etcd cluster.

etcd is sensitive to scheduling, network and storage latencies. While network
latencies and scheduling latencies have not been observed to be an issue in
clusters within one cloud region, the storage latency is. With remote networked
storage as delivered from ceph, the long tail of write latency causes etcd
to often time out heartbeats, causing a new leader election with a leader
change, preventing control plane changes on k8s for a few seconds. Too many
leader changes can slow down cluster operation and even bring it to a halt.

The etcd requirements [are well documented](https://etcd.io/docs/v3.5/op-guide/hardware/#example-hardware-configurations).
In particular, over a hundred of *sequential* IOPS are recommended. This
requires write latencies in the range of a single-digit ms (or better).

# Design Considerations

## Options considered

### One-node etcd (backed by redundant storage)

If k8s uses only one control plane node, there will only be only one etcd node,
avoiding timed out heartbeats. Single node control planes are typically not
recommended for production workloads though. They are limited with respect
to control plane performance, have a higher chance to fail (as a single node failure
can create cluster control-plane downtime) and can not undergo rolling upgrades.

Though not the normal setup with kubeadm, it is possible to use a multi-node
control plane using a single-node etcd. This shares some of the challenges of
single-node control-planes, although recovery may be faster to perform at least
in scenarios where the etcd backend storage is redundant and not affected by the
single-node outage.

Neither scenario fulfills typical requirements for production workloads.

### RAM (tmpfs) etcd storage

etcd could keep its database in volatile memory (e.g. on a tmpfs filesystem).
For multi-node etcd clusters, this would actually work, as long as at least one
cluster member stays alive. A loss of power affecting all nodes or a hardware
maintenance operation not tracking etcd needs would result in a complete
loss of all cluster state. The control plane nodes would require live migration
to avoid this in the maintenance case. For the power loss scenario, a frequent
backup might mitigate the cluster state loss case.

The etcd database is normally limited to 2GiB in size, which is something
that is realistic to keep in main memory. (Typical database sizes are
much smaller.)

This option requires additional care and may not be suitable for all
production scenarios, but would seem a possible fallback position.

### Heartbeat slowdown

To avoid causing too many failovers by occasional high latencies, the
frqeuency of heartbeats can be lowered from the default 1/100ms.
The reelection timeout should change along with it (typically set to
10 beats).

This will cause etcd to take a bit more time to notice the loss of a node,
which is not typically critical if done within reasonable limits.
This change however is not a silver bullet -- occasional write latencies
above 100ms will still cause failed heartbeats, just less often.

This change has been implemented in SCS's
(k8s-cluster-api-provider)[https://etcd.io/docs/v3.5/op-guide/hardware/#example-hardware-configurations]
reference implementation: The heartbeat has been changed from 1/100ms (10/s)
to 1/250ms (4/s) and the reelection timeout form 1s to 2.5s.

The etcd process also is afforded a higher CPU priority (lower niceness),
resulting in a lower scheduling latency, as high-prio processes preempt lower-prio
ones when they get woken up. The etcd process also gets it's IO priority
increased to get treated preferentially in case the IO scheduler has many
outstanding requests. This has some positive effects with the CFQ IO scheduler.

The slower heartbeat and the priority tweaks do lower the amount of leader
changes but are insufficient to completely address the issue on the tests
performed against networked ceph backed storage.

### Filesystem tuning

Databases must ensure that certain data has hit stable storage before acknowledging
writes -- this is required in order to live up to the [ACID](https://en.wikipedia.org/wiki/ACID)
guarantees in situations when disruptions might happen. Databases typically use
`fsync()` calls to ensure that write buffers are written to real persistent storage
unless they use raw/direct block devices circumventing Linux's page and buffer cachce.

etcd normally uses a write-ahead-log (WOL) file that lives on a Linux filesystem and
uses `fsync` to ensure the correct write ordering. Trouble with fsync is that it
also causes unrelated data to be written out with most existing Linux filesystems,
adding to the latency.

It is possible to tell the Linux filesystems to not wait for all data to have hit
storage before returning from fsync() calls. This avoids the latency caused by
`fsync` but also subverts the very reason for using `fsync`: In case of a disruption
(OS crash, power outage, loss of connection to storage, ...), the state is likely
not consistent, as the kernel has lied to the application about data having been
written out. Recovery from such a scenario can range from smooth to impossible.

In a multi-node cluster, this may not be as bad as it sounds -- if only one
node is affected by a disruption, the crashed node can be recovered by resyncing
the data from other nodes. In practice an inconsistent state would be considered
too risky and it should be preferred to set up a fresh node to join the
existing etcd cluster. This would need to be implemented to make this option
less risky.

The reference implementation has an option to use these unsafe filesystem settings.
However, they are not enabled by default for good reasons.

### Flavors with local storage

disk, ssd, nvme

(nvme can be labeled as ssd to fulfill standard, understatement is allowed)

Implementation via nova, not via cinder (iscsi-tgt)

# Decision

Add two new mandatory flavors: SCS-2V:4:20s and SCS-4V:16:100s.

# Open Questions

QoS for disks to prevent DoS

Implication on live-migration performance / capability

# Connection to other standards

The flavors are added as mandatory flavors to the flavor-naming standard,
which will thus have to be released in a v2.
