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

- Avoid mandating features specific to certain CNI plugins (like CiliumClusterwideNetworkPolicy)

### Options considered

#### NetworkPolicy API

- Should be a requirement
- We need to be specific about which API version to require and reference the upstream definition
- Only recommend recent additions like AdminNetworkPolicy

#### Ingress API

- Some CNI plugins (specifically Cilium) have builtin support for the Ingress and Gateway API
- Those can also be provided by separate ingress controllers (like ingress-nginx)
- Ingress controllers seem to be regularly requested by managed k8s users
- some users may prefer to deploy their own ingress controllers

### Open questions

RECOMMENDED

## Standard

CSPs MUST provide a network plugin that supports the basic NetworkPolicy API
CSPs SHOULD provide a network plugin that implements the AdminNetworkPolicy and BaselineAdminNetworkPolicy resources.

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
