---
title: KaaS Networking Standard
type: Standard
status: Draft
track: KaaS
---

## Introduction

Kubernetes defines a networking model that needs to be implemented by a separate CNI plugin.
Beyond basic connectivity within the cluster, however, there are many networking features that are specified but optional.
Some of these optional features provide vital functionality, such as the NetworkPolicy API and the Ingress API.

This standard specifies a minimal set of networking features that users can expect in clusters created by an SCS-compliant KaaS provider.

## Terminology

The following terms are used throughout this document:

| Term | Meaning |
|------|---------|
| KaaS, managed Kubernetes | Kubernetes as a Service, automated on-demand deployment of Kubernetes clusters. |
| CSP | Cloud Service Provider, the provider of the KaaS infrastructure. |
| CNI | Container Network Interface, a standardized networking interface for container runtimes. |
| CNI plugin, networking plugin | Kubernetes bindings for a CNI implementation, translates Kubernetes API concepts into more basic container networking concepts. |
| network policy | A set of rules to restrict network traffic in a Kubernetes cluster. |

## Motivation

KaaS providers will typically support aditional networking functionality beyond basic Kubernetes networking.
The specific range of features depends on the used CNI plugin, but may also be extended by additional operators.
Users may expect certain optional functionality, so we should define a baseline feature set that has to be available in an SCS-compliant KaaS cluster.

## Design Considerations

The Kubernetes API can be extended arbitrarily.
Many CNI plugins will define custom resources to enable functionality that is not covered in the official [API specification](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.31/).
Sometimes they will even reuse names from different API groups, such as `NetworkPolicy`, which exists in the basic `networking.k8s.io/v1` API, but also in `projectcalico.org/v3`.

To avoid any ambiguity, we should therefore be explicit about the API groups and versions of resources.
We should also avoid mandating third-party API extensions, to avoid dependencies on specific third-party software and keep the standard as generic as possible.

### Options considered

#### NetworkPolicy API

Kubernetes network policies are used to restrict network traffic between pods in a cluster, but also between pods and external network resources.
The policy rules can filter based on port and address ranges, but also on Kubernetes-specific target attributes such as namespaces and labels.
They must be implemented by the CNI plugin, and though they are widely supported, they are still technically optional, and there are some lightweight networking plugins, such as Flannel, that are not enforcing them.

Nonetheless, network policies are widely used and most users will expect them in a managed Kubernetes cluster.
The wide, but varying support among CNI plugins makes them a good target for SCS standardization.

#### Default Network Policies in Namespaces

Basic network policies are namespaced resources, and can only filter traffic to and from pods in their own namespace.
In a newly created namespace without policies the default behavior will apply, which is to not restrict traffic at all.

It can be desirable to automatically create default network policies in new namespaces, using a policy operator such as Kyverno.
A CSP could provide such an operator and offer a number of default policies, like blocking connections to other namespaces by default, or blocking access to the OpenStack metadata service.

Any user with permissions to manage their own network policies in a namespace will of course be able to remove or modify any default network policies in that namespace.
CSP-provided network policies should thus only be viewed as a safety default, and should only be deployed if they are actually beneficial to users.

#### AdminNetworkPolicy API

An alternative to automatically created default network policies are API extensions that allow cluster-wide networking rules.
Some CNI plugins have implemented such extensions, e.g. Calico's `GlobalNetworkPolicy` and Cilium's `CiliumClusterwideNetworkPolicy`.

The Kubernetes Network Special Interest Group is currently working on an [official API extension](https://network-policy-api.sigs.k8s.io/api-overview/) to cover this functionality.
This API extension introduces the new `AdminNetworkPolicy` and `BaselineAdminNetworkPolicy` resources, which represent cluster-wide network policies with respectively higher or lower precedence than namespaced network policies.

This API is also a good candidate for standardization because it consolidates a number of vendor-specific workarounds to limitations of the NetworkPolicy API.
It has not been stabilized yet, so currently we can at most recommend CNI plugins where there is ongoing work to support these features.

#### Ingress API

The Ingress API allows the external exposure of HTTP/HTTPS-based services running in the cluster.
Unlike the L3/L4-based LoadBalancer Service type, Ingress provides L7 load balancing, HTTP routing, and TLS termination for services.
This functionality can be provided within the cluster by a pod-based ingress controller such as `ingress-nginx`, that exposes Ingress resources as Services.

However, there are also Ingress controllers that integrate with underlying infrastructure and may help to reduce overhead.
Examples for this are the Cilium CNI plugin, which comes with built-in Ingress support, and the Octavia Ingress controller, which may be a good choice if OpenStack Octavia is already used to provide L3/L4 load balancing.

The CSPs that manage the underlying infrastructure can of course make the best choice for such an integrated Ingress controller, so they should be encouraged to do so.
Even with a CSP-provided default Ingress controller present, users will be able to use alternative Ingress controllers by creating a new `IngressClass`, which can then be referenced in Ingress resources.

## Decision

CSPs MUST provide a network plugin that fully supports `NetworkPolicy` resources in the API version `networking.k8s.io/v1`.
CSPs SHOULD provide a network plugin that supports or is working on support for the `AdminNetworkPolicy` and `BaselineAdminNetworkPolicy` resources of the `policy.networking.k8s.io` API group, in their latest version, up to `v1`.

CSPs SHOULD offer the option for a managed, `networking.k8s.io/v1`-compliant Ingress controller and a default `IngressClass` resource for this controller.

CSPs MAY add default networking restrictions, using either `networking.k8s.io/v1`-compliant `NetworkPolicy` resources with a policy operator, or alternatively any cluster-wide network policy extensions provided by the CNI plugin.

## Conformance Tests

Required support for network policies will be tested using the upstream e2e tests via Sonobuoy.
