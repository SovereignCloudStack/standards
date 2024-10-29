---
title: KaaS Networking Standard
type: Standard
status: Draft
track: KaaS
---

## Introduction

Kubernetes defines a networking model that needs to be implented by a separate CNI plugin.
Beyond basic connectivity within the cluster, however, there are many networking features that are specified but optional.
Some of these optional features provide vital functionality, such as the NetworkPolicy API and the Ingress API.

This standard specifies a minimal set of networking features that users can expect in clusters created by an SCS complient KaaS provider.

## Terminology

Example (abbr. Ex)
  This is the description for an example terminology.

## Motivation

KaaS providers will typically support aditional networking functionality beyond basic Kubernetes networking.
The specific range features depends on the used CNI plugin, but may also be extended by additional operators.
Users may expect certain optional functionality, so we should define a baseline feature set that has to be available in an SCS-compliant KaaS cluster.

## Design Considerations

The Kubernetes API is arbitrary extensible.
Many CNI plugins will define custom resources to enable functionality that is not covered in the official API specification [^spec].
We should avoid mandating third party API extensions, such as Cilium's `CiliumClusterwideNetworkPolicy`, to keep the standard as generic as possible and avoid dependencies on specific implementations.
We should also be explicit about the required versions of the APIs.

### Options considered

#### NetworkPolicy API

Kubernetes network policies allow the restrict network traffic within a cluster based on labels and namespaces.
They must be implemented by the CNI plugin of the cluster and are technically optional, though they are few CNI plugins that do not support them.

Network policies are an important security feature that allows a separation of components and namespaces on a network level.

- already defacto standard, will be expected by many users, so we should make it explicit

#### AdminNetworkPolicy API

Basic network policies are always bound to a namespace, and only affect connections to and from pods within this namespace.
Restricting certain traffic within the whole cluster requires a policy to be replicated across all namespaces.
There are operators, such as Kyverno, that can handle this replication automatically and will also create policies for newly created namespaces.

Some CNI plugins have implemented their own extensions for cluster-wide networking rules, such as Calico's `GlobalNetworkPolicy` and Cilium's `CiliumClusterwideNetworkPolicy`.
The Kubernetes Network Policy Special Interest Group is currently working on an official API extension to cover this functionality.

- AdminNetworkPolicy replaces CNI-specific APIs
- we can not mandate this until it is stable
- could be required in a future version of this standard
- we can recomend CNIs that are already working on support

#### Default Network Policies in Cluster

- providing defaults is possible even without AdminNetworkPolicy by either operator or CNI-specifics
- what are useful defaults?
- is there actually a demand for CSP-set defaults?

#### Ingress API

The Ingress API allows the external exposure of HTTP(S)-based services running in the cluster.
Unlike the L3/L4-based LoadBalancer Service type, Ingress provides L7 load balancing, HTTP routing, and TLS termination for services.
This functionality can be provided within the cluster by a pod-based ingress controller such as `ingress-nginx`, that is itself exposed as a Service.

However, there are also Ingress controllers that integrate with the underlying infrastructure and may reduce some overhead.
Examples for this are the Cilium CNI plugin, which comes with bhuilt-in Ingress support, and the Octavia ingress controller, which might be a good choice if OpenStack Octavia is already used to provide Service load balancing.

- Ingress controllers seem to be regularly requested by managed k8s users
- managed ingress controller may have better integration in infrastructure
- some users may prefer to deploy their own ingress controllers, e.g. if they have additional requirements such as the gateway API
- CSPs could offer option to set up ingress controller

### Open questions

RECOMMENDED

## Standard

CSPs MUST provide a network plugin that supports the basic NetworkPolicy API.
CSPs SHOULD provide a network plugin that implements, or is working on implementing, the AdminNetworkPolicy and BaselineAdminNetworkPolicy resources.

- add upstream API references and versions
- CSPs should offer option for managed ingress controller
- CSPs may provide default network policies through either an operator or global network policy extensions.

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
