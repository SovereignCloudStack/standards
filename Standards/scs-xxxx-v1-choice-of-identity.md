---
type: Decision Record
status: draft
track: Global
version: 0
---

# Introduction

Granted that it is accepted to establish machine identities, settling on...

- an standard operation on how to verify identity at attestation/login time prior to issuing of "Verifiable Identity Document"
- the form of an "Verifiable Identity Document"
- an standard operation on how to obtain such "Verifiable Identity Document"

...is required.

Given that cloud services ("resource API's") need to consume/verify such "Verifiable Identity Document" and implementing distinct authentication mechanisms for human users as well as for machines would make things more complex, this choice also most likely affects how human users authenticate themselves.

# Motivation

Implementation of previous decision record. See its "Motivation" section.

# Design considerations

## Use of SVIDs ([Secure Production Identity Framework for Everyone](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE.md) (SPIFFE) Verifiable Identity Document)

**How to verify Identity at attestation/login time:**
Depends on implementation; E.g. using SPIRE (being SPIFFE's reference implementation) integrated with Kubernetes.

**Form of "Verifiable Identity Document":**
[SVID](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE-ID.md) (See also the other documents `X509-SVID.md`, `JWT-SVID.md`)

**How to obtain "Verifiable Identity Document":**
[SPIFFE Workload API](https://github.com/spiffe/spiffe/blob/064d6faece28cfd500faffaee2cb6f9d1423e31d/standards/SPIFFE_Workload_API.md)

**How to verify "Verifiable Identity Document" at resource API side:**
Using SPIFFE trust bundle.

**Assessment of suitability:**
SPIFFE (along with its reference implementation "SPIRE") is a CNCF graduated project defining how machines can authenticate towards other services.
As such, it is not designed to cover user identities, even there is most probably no technical reason to not use SVIDs for users as well - maybe even the "Workload API".
Hence, if adopting SPIFFE, either (1) resource API's need to accept different means of authentication for users and for machines or (2) non-workload identities need to get SVIDs as well - stretching the scope of SVIDs quite a bit.

## OIDC ID tokens

**How to verify Identity at attestation/login time:**
(1) In Case of K8s `ServiceAccounts`: K8s takes care of this (2) In case of virtual machine: Infrastructure-level checks.

**Form of "Verifiable Identity Document":**
[OIDC Spec](https://openid.net/specs/openid-connect-core-1_0.html#IDToken) compliant JWT

**How to obtain "Verifiable Identity Document":**
(1) In case of K8s `ServiceAccounts`: Configure [Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection), read it from file system (2) In case of virtual machines: Pre-provision it or make it available via host-only API (HTTP/UNIX-Socket/...)?

**How to verify "Verifiable Identity Document" at resource API side:**
(1) In case of K8s `ServiceAccounts`: Validate ID tokens using JWKS from K8s OpenID Discovery endpoints [^1] (2) In case of virtual machines: Validate id tokens using JWKS from IdP OpenID Discovery endpoint

**Assessment of suitability:**
While e.g. Kubernetes offers a pragmatic approach to use `ServiceAccount` identities outside of Kubernetes, OIDC ID tokens generated via a web based OIDC flow (e.g. for users) should not be used directly on resource API's [^2].
Hence, using OIDC ID tokens as authentication tokens may be alright in some areas, but it does not provide a generally applicable solution.

## RFC9068 Access Tokens:

**How to verify Identity at attestation/login time:**
Depending on type of entity having identity.

**Form of "Verifiable Identity Document":**
[RFC9068](https://datatracker.ietf.org/doc/html/rfc9068) compliant JWT 

**How to obtain "Verifiable Identity Document":**
Complete an OAuth2 flow supported by IdP.

**How to verify "Verifiable Identity Document" at resource API side:**
Verify bearer token according to [RFC9068](https://datatracker.ietf.org/doc/html/rfc9068)

**Assessment of suitability:**
While details have to be determined for each type of entity having an identity, this approach might work for a wide spectrum of entities.

# Decision

Ultimately, the decision is to use DIDs.

## DIDs (Decentralized Identifiers)

**How to verify Identity at attestation/login time:**
Depending on type of entity having identity.

**Form of "Verifiable Identity Document":**
[Verifiable Credentials](https://www.w3.org/TR/vc-data-model/) containing ["Decentralized Identifier" aka DID](https://www.w3.org/TR/did-core/)

**How to obtain "Verifiable Identity Document":**
Depending on type of entity having identity.

**How to verify "Verifiable Identity Document" at resource API side:**
Universally in the same manner for all identity types.

**Assessment of suitability:**
DIDs, being defined by the W3C, are propagated by [GXFS](https://www.gxfs.eu/ssi-whitepaper/) for SSI ("Self Sovereign Identity"). The linked white paper explicitly says that SSI is applicable for humans as well as for machines.
As such, it seems a good fit, even if the "Decentralized" bit may feel a bit alien and there are more simple, more established methods for narrower use cases.
Another advantage: "Federating" is not implemented as after-thought, but is "built-in".

[^1]: Not sure whether these projected tokens should be considered an OIDC "ID token" which according to usual OIDC terms, should **not** be sent to resource API's. The implementation in Kubernetes and documentation of e.g. [Vault](https://www.vaultproject.io/docs/auth/jwt/oidc-providers/kubernetes) do suggest that this is alright.
[^2]: See https://auth0.com/blog/id-token-access-token-what-is-the-difference/#What-Is-an-ID-Token-NOT-Suitable-For
