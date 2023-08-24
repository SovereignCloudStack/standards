---
title: Kubernetes Nodes Anti Affinity
type: Decision Record
status: Draft
track: KaaS
---

## Introduction

A Kubernetes instance is provided as a cluster, which consists of a set of worker machines,
so called nodes. A cluster is composed of a control plane and at least one worker node.
The control plane manages the worker nodes and therefore the pods in the cluster by making
decisions about scheduling, event detection and global decisions. Inside the control plane,
multiple components exist, which can be duplicated and distributed over multiple machines
inside the cluster. Typically, no user containers are run on these machines in order to
separate the control plane from the live system.

## Motivation

In a productive environment, the control plane usually runs across multiple machines and
a cluster usually contains multiple worker nodes in order to provide fault-tolerance and
high availability.

In order to ensure availability and scaling of workloads, even if some machines in the cluster
could fail, they should be distributed over multiple nodes on different machines.
This can be steered with the Affinity or Anti Affinity features, which are separated by
Kubernetes into two features:

Node Affinity
The Node Affinity feature allows to match pods according to logical matches of
key-value-pairs referring to labels of nodes.
These can be defined with different weights or preferences in order to allow fine-grained
selection of nodes. The feature works similar to the Kubernetes nodeSelector.
It is defined in the PodSpec using the nodeAffinity field in the affinity section.

Pod Affinity
Pod Affinity or Pod Anti Affinity allows the constraint of pod scheduling based on the
labels of pods already running on a node.
This means the constraint will match other pods on a node according to their labels key-value-pairs
and then either schedule the pod to the same (Affinity) or another (Anti Affinity) node.
This feature is also defined in the PodSpec using the podAffinity field in the affinity section.

Both features allow the usage of "required" or "preferred" keywords, which create
"hard" or "soft" affinities. By using a hard affinity, a pod would need to be scheduled
according to the rules set. If this possibility is not given, the pod can't be scheduled.
A soft affinity would allow scheduling even if the requirements are not fulfilled, but
they would be preferred if possible.

These features allow efficient resource usage (e.g. by scheduling workloads to evenly
distribute across nodes) and provide fault-tolerance and therefore high availability.
But they also require more work during the setup of a service architecture, since nodes
and pods need to be labelled and described consistently.

In the case of SCS, affinity of the workloads themselves is not relevant, since this
feature is mostly used by the customers of the providers.
Instead, the expected standard should enable the Kubernetes cluster to handle Anti Affinity
rules with a real physical separation as well as distributing the control plane over
multiple machines in order to provide fault-tolerance during system outages.
If the control plane survives an outage, a Kubernetes cluster can recover later on.

## Design considerations

SCS plans to require a Hard Anti Affinity and/or Redundancy for the control plane and
a Soft Anti Affinity for workers. This means, that Anti Affinity would be required for
the control planes and their pods and only optional (but encouraged) for workers.

In order to achieve the goals for these components, meaning availability and fault tolerance
for the control plane, in order to achieve an outage resistant cluster, and the availability
promise given with Anti Affinity for pods on the worker nodes, a separation of nodes
on the hardware or hypervisor level would need to be achieved. Since running multiple
hypervisors on the same machine is in most cases not feasible and this approach
wouldn't change availability for outages of individual machines, this should not be recommended.

For the control plane, a reference to the "Kubernetes High Availability" [1]
can be useful, since it provides two ways to set up a highly available cluster.
Both approaches are very similar. The "Stacked Control Plane" requires less infrastructure,
but also runs the risk of failed coupling, where if one node fails, the redundancy could be
compromised due to the loss of a complete control plane instance.
The "External ETCD" solves this problem, but also requires double the infrastructure, due
to the externally incorporated etcd clusters.

This also shows, that the wording "anti affinity" as used with Kubernetes pods is probably
slightly misleading in the context of a Kubernetes control plane. It may consist of multiple
pods with individual tasks, but distributing them over different nodes through Anti Affinity
would probably still cascade the whole control plane into a complete failure, if one of
the used nodes goes down. It could be possible to replicate specific important pods and
assign them to different nodes, but at this point, a redundant setup like presented in [1] could be used.
So Anti Affinity in this context probably means more like distribution over multiple
physical machines, which needs to be planned beforehand on the machine/server level.

Therefore would it be preferred for the control plane to use a redundant setup, which
is separated over different physical machines, meaning at least half of the control plane
nodes runs on a different physical machine as the rest.

For worker nodes, the whole idea of Anti Affinity is more of a preferable situation.
The nodes themselves should at best be distributed over different machines, but this
is not a requirement, especially since smaller providers wouldn't have the capacity to
provide enough machines for these distributed Kubernetes clusters. Since customers that
use the Affinity feature would be especially interested in the worker nodes that host
their workloads, it should be achieved that a good labeling system is provided for the
nodes in order to see if two nodes are hosted on the same machine.

## Decision

The future standard should define a few important things in order to provide a solid base
for the usage and advantages of workloads with Anti Affinity rules.

Control planes SHOULD be made redundant in order to provide fault-tolerance and security
against fatal errors on this layer, in the case of node failures. How this redundancy
is achieved SHOULD be left to the providers, but since failure must be avoided, it is
REQUIRED to at least duplicate control plane components. Half of every component SHOULD
also be located on a different node on a different physical machine than the other half
of them. This should provide at least the minimum requirements for a fault-tolerant control plane.

The worker nodes are RECOMMENDED to be distributed over different machines. In order to
provide clear information to the users, the nodes should be labeled to reflect the
mapping to the underlying clusters. It should be noted, that it is NOT REQUIRED to have
this anti affinity for the worker nodes due to the requirements of infrastructure and
complexity associated with this.

## Documents

Kubernetes High Availability Documentation [1](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
