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

The currently defined standard flavors (as of v1.1 from 2022-09-08) do not include
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
latencues and scheduling latencies have not been observed to be an issue in
cluster within one cloud region, the storage latency is. With remote networked
storage as delivered from ceph, the long tail of write latency causes etcd
to often time out heartbeats, causing a new leader election with a leader
change, preventing control plane changes on k8s for a few seconds. Too many
leader changes can slow down cluster operation and even bring it to a halt.

TODO: Add link to upstream etcd requirements docs

# Design Considerations

## Options considered

### One-node etcd (backed by redundant storage)

One etcd (SPOF) for multiple control plane nodes or just one control plan node.

### RAM (tmpfs) etcd storage

Reboot / Cold migration impossible.

### Heartbeat slowdown

Done.

### Filesystem tuning

Unsafe.

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
