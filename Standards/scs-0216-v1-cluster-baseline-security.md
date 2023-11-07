---
title: Kubernetes cluster baseline security
type: Standard
status: Draft
track: KaaS
---

## Introduction

A Kubernetes instance is provided as a cluster, which consists of a set of machines,
so called nodes. These clusters are configured depending on the needs of its users, which
is possible due to the flexibility of Kubernetes.
Due to the regular changes, there are always new security features to deploy and use in Kubernetes.
Nevertheless, a provider (or even a customer) needs to take action in order to achieve a
hardened, secure cluster due to the myriad of configurations possible. This is especially
the case since Kubernetes ships with insecure features and configurations out of the box,
which will need to be mitigated by an administrator with the proper knowledge.
Hardened Kubernetes clusters are desirable regardless of the possible thread model, since
higher security doesn't necessarily mean higher complexity in this case.

## Motivation

Kubernetes clusters are highly configurable to fit a wide array of use-cases and setups.
This makes them flexible and scalable to a certain extent, which is probably also why they
found such a wide adoption. But its also obvious, that security problems can arise if a
cluster isn't configured properly to mitigate them.
These security risks can potentially be exposed in many different parts of a cluster, e.g.
different APIs, authorization and authentication procedures or even Pod privilege mechanisms.
In order to mitigate these problems, different hardening and prevention steps and mechanisms
could be used to increase the security of a Kubernetes setup.

## Design Considerations

### External CA

Kubernetes provides an API to provision TLS certificates that can be signed by a CA.
This CA can be controlled by the cluster provider, which enables much more tight control
over the clusters communication and therefore also better controllable security.

In order to do this, the CA certificate bundle needs to be added to the trusted certificates
of the server.
To provide a certificate, the following steps need to be undertaken:

1. Create a CSR
2. Send the CSR manifest to the k8s API
3. Approve the CSR
4. Sign CSR with your CA
5. Upload the signed certificate to the server

This certificate could now be used by a user in a pod in order to provide a trusted certificate.

It is also possible for the Kubernetes controller manager to provide the signing functionality.
To enable this, `--cluster-signing-cert-file` and `--cluster-signing-key-file` need to be set with
a reference to the CA keypair, which was used in the previous example to sign a CSR.

### Protected Kubernetes endpoints

In order to secure a Kubernetes cluster, the protection and hardening of endpoints is important.
To do this, different approaches can be taken.

#### TLS for all internal/API traffic

It is already expected by Kubernetes, that all API communication internally is encrypted with TLS.
Nevertheless, some endpoints of internal components could be/will be exposed without the necessary
encryption, which could lead to weak points in the system.
A list of the default service endpoints can be seen in the following table

Protocol | Port Range | Purpose
— | — | —
TCP | 6443- | Kubernetes API Server
TCP | 2379-2380 | etcd server client API
TCP | 10250 | Kubelet API
TCP | 10251 | kube-scheduler
TCP | 10252 | kube-controller-manager
TCP | 10255 | Read-Only Kubelet API

Protocol | Port Range | Purpose
— | — | —
TCP | 10250 | Kubelet API
TCP | 10255 | Read-Only Kubelet API
TCP | 30000-32767 | NodePort Services

#### Authentication and Authorization

All API clients should authenticate and authorize in order to be able to access an API or even
specific functions of this API. This is the case for users as well as internal components.

Most internal clients (like proxies or nodes) are typically authenticated via service accounts or
x509 certificates, which will normally be created automatically during the setup of a cluster.
External users can authenticate via an access pattern of choice, which is typically decided by
the cluster provider.

Authorization is (normally) done by he Role-Based Access Control (RBAC), which matches a request
by a user with a set of permissions, also called a role. Kubernetes deploys some roles out-of-the-box;
additional roles needs to be carefully checked, since some permissions for specific resources allow
modification of other resources.

This whole process is especially important for the Kubelet, which allows anonymous requests in its
default configuration. This is obviously a security risk, since everybody with access to its endpoint
could manipulate resources that are managed with the Kubelet.

To disable anonymous requests, the Kubelet should be started with `--anonymous-auth=false`.
Authentication can be provided either through x509 client certificates or API bearer tokens.
How to setup both approaches can be found in the [Kubelet Authentication and Authorization](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/).

Kubelet authorization is set to `AlwaysAllow` as a default mode. This can be quite problematic,
since all authenticated users can do all actions. To mitigate this, it is possible to delegate
authorization to the API server by:

- enabling the `authorization.k8s.io/v1beta1` API group
- starting the Kubelet with the `--authorization-mode=Webhook` and the `--kubeconfig` flags

After that, the Kubelet calls the `SubjectAccessReview` API in order to determine the authorization of a request.

## Decision

This standard tries to increase security for a Kubernetes cluster and harden it in order
to provide a high security setup. For this to work, multiple measures need to be undertaken.
It is important to note that this standard is not REQUIRED for all clusters,
but instead gives best practices for increasing security. Nevertheless, if a cluster is
provided on the basis of high security, this standard MUST be applied.

A self-controlled CA SHOULD be used in order to be in control of the TLS certificates, which
enables the operator to provide and revoke certificates according to the requirements.

All internal endpoints found in the section [TLS for all internal/API traffic] should be
encrypted with TLS in order to secure internal traffic.

The Kubernetes API (kubeAPI) MUST be secured by authenticating and authorizing the users
trying to access its endpoints. How a user is authenticated is up to the provider of the
cluster and/or the wishes of the customer. Authorization MUST be done by providing
fine-grained RBAC.
This whole process also MUST be applied to the Kubelet, which in its default configuration
doesn't enable authentication or authorization. A way to do this can be found in the
section [Authentication and Authorization].

## Related Documents

[Managing TLS in a cluster](https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/)
[Securing a cluster](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/)
[Controlling access](https://kubernetes.io/docs/concepts/security/controlling-access/)
[Kubelet Authentication and Authorization](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/)
[Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
[Kubernetes Security](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)

## Conformance Tests

Conformance Tests will be written in another issue
