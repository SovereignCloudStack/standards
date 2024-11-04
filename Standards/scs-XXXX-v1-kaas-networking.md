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

Kubernetes network policies can restrict network traffic within a cluster based on labels and namespaces.
They must be implemented by the CNI plugin of the cluster and are technically optional, though the majority of CNI plugins support them.

Network policies are an important and widely used security feature, and the existing wide support among CNI plugins makes them a good target for SCS standardization.

#### Default Network Policies in Namespaces

Basic network policies are always bound to a namespace, and only affect connections to and from pods within this namespace.
Without them, pods are reachable by any other pod in the cluster and also can connect to any external address.

Automatically creating default network policies in new namespaces can be desirable but requires an operator such as Kyverno.
A CSP could provide such an operator and offer a number of default policies, like blocking connections to other namespaces by default, or blocking access to the OpenStack metadata service.

Any user with permissions to manage their own network policies in a namespace will of course be able to remove or modify any default network policies in that namespace.
CSP-provided network policies should therefore only be viewed as a safety default, and should only be deployed if they are actually beneficial to users.

#### AdminNetworkPolicy API

An alternative to automatically created default network policies are API extensions that allow cluster-wide networking rules.
Some CNI plugins have implemented such extensions, e.g. Calico's `GlobalNetworkPolicy` and Cilium's `CiliumClusterwideNetworkPolicy`.

The Kubernetes Network Policy Special Interest Group is currently working on an official API extension to cover this functionality [^adminnetpol].
This API extension introduces the new `AdminNetworkPolicy` and `BaselineAdminNetworkPolicy` resources, which represent cluster-wide network policies with respectively higher or lower precedence than namespaced network policies.

This API is also a good candidate for standardization because it consolidates a number of vendor-specific workarounds to limitations of the NetworkPolicy API.
It has not been stabilized yet, so currently we can at most recommend CNI plugins where there is ongoing work to support this feature.

#### Ingress API

The Ingress API allows the external exposure of HTTP/HTTPS-based services running in the cluster.
Unlike the L3/L4-based LoadBalancer Service type, Ingress provides L7 load balancing, HTTP routing, and TLS termination for services.
This functionality can be provided within the cluster by a pod-based ingress controller such as `ingress-nginx`, that is itself exposed as a Service.

However, there are also Ingress controllers that integrate with underlying infrastructure and may help to reduce overhead.
Examples for this are the Cilium CNI plugin, which comes with built-in Ingress support, and the Octavia ingress controller, which may be a good choice if OpenStack Octavia is already used to provide L3/L4 load balancing.

The choice for such an externally integrated Ingress controller can of course be best made by the CSP that manages the underlying infrastructure.
While some users may still want to deploy their own ingress controller, many will also use a CSP-provided one if available.

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
