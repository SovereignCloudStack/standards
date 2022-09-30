---
type: Decision Record
status: draft
track: Global
version: 0
---

# Introduction

Granted that it is accepted to establish machine identities, settling on...

- an standard operation on how to verify identity at attestation time prior to issuing of "Verifiable Identity Document"
- the form of an "Verifiable Identity Document"
- an standard operation on how to obtain such "Verifiable Identity Document"

...is required.

Given that cloud services ("resource API's") need to consume/verify such "Verifiable Identity Document" and implementing distinct authentication mechanisms for human users as well as for machines would make things more complex, this choice also most likely affects how human users authenticate themselves.

# Motivation

Implementation of previous decision record. See its "Motivation" section.

# Design considerations

## Use of SVIDs ([Secure Production Identity Framework for Everyone](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE.md)(SPIFFE) Verifiable Identity Document)

**How to verify Identity at attestation time:**
Depends on implementation; E.g. SPIRE integrated with Kubernetes

**Form of "Verifiable Identity Document":**
[SVID](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE-ID.md) (See also the other documents `X509-SVID.md`, `JWT-SVID.md`)

**How to obtain "Verifiable Identity Document":**
[SPIFFE Workload API](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE_Workload_API.md)

**How to verify "Verifiable Identity Document" at resource API side:**
Using SPIFFE trust bundle

**Assessment of suitability:**
SPIFFE (along with its reference implementation SPIRE) is a CNCF graduated project defining how machines can authenticate towards other services.
As such, it is not designed to cover user identities, even there is most probably no technical reason to not use SVIDs for users as well - maybe even the "Workload API".
Hence, if adopting SPIFFE, either (1) resource API's need to accept different means of authentication for users and for machines or (2) non-workload identities need to get SVIDs as well - stretching the scope of SVIDs quite a bit.

## Access Tokens (OIDC-ish style):

**How to verify Identity at attestation time:**
(1) In Case of K8s `ServiceAccounts`: K8s takes care of this (2) In case of users: Password/FIDO2/... (3) In case of virtual machine: Infrastructure-level checks

**Form of "Verifiable Identity Document":**
JWT with some common claims identifying entity

**How to obtain "Verifiable Identity Document":**
(1) In case of K8s `ServiceAccounts`: Configure [Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection), read it from file system (2) In case of users: Some kind of API call to IdP? (3) In case of virtual machines: Pre-provision it or make it available via host-only API (HTTP/UNIX-Socket/...)?

**How to verify "Verifiable Identity Document" at resource API side:**
(1) In case of K8s `ServiceAccounts`: Validate access tokens using JWKS from K8s OpenID Discovery endpoints [^1] (2) In case of users: Validate access tokens using e.g. JWKS from IdP (3) In case of virtual machines: ?

**Assessment of suitability:**
While e.g. Kubernetes offers a pragmatic approach to use `ServiceAccount` identities outside of Kubernetes, access tokens are not standardized.
As such, access tokens from different sources may look fundamentally different and may need to be harmonized by an extra layer.

# Decision

Ultimately, the decision is to use DIDs.

## DIDs (Decentralized Identifiers)

**How to verify Identity at attestation time:**
Depending on type of entity having identity

**Form of "Verifiable Identity Document":**
[Verifiable Credentials](https://www.w3.org/TR/vc-data-model/) containing ["Decentralized Identifier" aka DID](https://www.w3.org/TR/did-core/)

**How to obtain "Verifiable Identity Document":**
Depending on type of entity having identity

**How to verify "Verifiable Identity Document" at resource API side:**
Universally in the same manner for all identity types.

**Assessment of suitability:**
DIDs, being defined by the W3C, are propagated by [GXFS](https://www.gxfs.eu/ssi-whitepaper/) for SSI ("Self Sovereign Identity"). The linked white paper explicitly says that SSI is applicable for humans as well as for machines.
As such, it seems a good fit, even if the "Decentralized" bit may feel a bit alien and there are more simple, more established methods for narrower use cases.

[^1]: Not sure whether these projected tokens should be considered an OIDC "ID token" which according to usual OIDC terms, should **not** be sent to resource API's.
