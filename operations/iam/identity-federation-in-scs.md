---
title: Identity Federation in SCS
type:
status: Draft
track: Global
---

SovereignCloudStack wants to make it possible for operators to delegate
administration of user identities to the organizational entities that the
users are part of. Usually that's customer organizations but it could also
be the operator itself. Federation protocols like OpenID Connect can be used
to achieve that goal. To simplify connecting the different parts of SCS
to customer owned IAM solutions, SCS deploys Keycloak as central Identity
Provider (IdP) service.

The following sections describe how this is done.

## 1. IaaS / OpenStack

To provide Infrastrucure as a Service SCS builds upon
OpenStack. See the `openstack-federation-via-oidc` document
in [the iam section of this documentation](https://docs-staging.scs.community/docs/iam/)
for more details on identity federation for OpenStack.

## 2. CaaS

To provide Container as a Service SCS builds upon
Kubernetes. There is
[work in progress](https://github.com/SovereignCloudStack/issues/issues/373)
to optionally connect Kubernetes to Keycloak and to
map authorization decisions based on claims via cluster role bindings.
