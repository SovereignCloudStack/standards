---
title: Requirements for SSO identity federation
type: Decision Record
status: Draft
track: IAM
---

# Introduction

Our assumption is that there are use cases, where CSPs would like to be able to
let customers access their SCS based services by identifying themselves with
credentials that are stored and managed external to the CSP's SCS installation.

This is based on the observation that prospective customers of a SCS based CSP
sometimes already come equipped with an IAM solution of their choice, either on
premises or e.g. as an external 3rd party cloud service. To ease onboarding of
customer employees (or e.g. customer contracted 3rd party admin staff) as SCS
users, it would be good to be able to consume these external identities in SCS.

For customers this avoids the neccessity to explicitly maintain an additional
dedicated account in SCS and this also reduces what SCS needs to do with
respect to taking care of persisting user account information.

To put it in other words, in SCS we would like to be able to delegate
authentication to external identity providers and map those users to roles in
SCS that can be used for authorization decisions when users access SCS services.

# Motivation for this document

SCS has multiple service layers, like IaaS and CaaS, both of which running their
own technological stack with specific internal models of accounts and
authorization. OTOH there are also specific services like the "Status Page"
application that require consumption of identities.

One thing these services have in common, is that they are able
to use SSO protocols like OAuth 2.0 or OpenID Connect (OIDC) on top of it to
delegate authentication. They are service providers (SAML terminology) and can
be relying parties (OIDC terminology) of a protocol compliant identity provider
(IdP).

So the idea is, to run a SSO IdP as part of SCS to provide a dedicated point
of entry for identites, which the SCS service layers can use as a common
interface to consume external user identities.

The purpose of this document is to specify what requirements a specific
technical IdP implementation (i.e. software solution) needs to fulfill
in the context of SCS.

# Design Considerations

As a central service for identity handling, the IdP
service needs to be really, really robust.

Customers shall be able to access self service, so that
they can make reasonable adjustments e.g. to role mapping.
At the time of writing this document it's still undecided
if SCS has the requirement of a decicated "self service"
that serves as a frontend to provision and re-configure
customer specific data, abstracting e.g. from IdP specific
user interface particularities.

## Options considered

### Keycloak

Keycloak is a commonly used IdP solution implemented in Java.
It is developed as an open source community project.
Red Hat uses it as upstream source for their Red Hat SSO product
and is also listed as sponsor of the project.
Starting with version 17 the default distribution is based on
Quarkus instead of WildFly/JBoss.

The project maintains several means of community contributions
as listed on the [community section](https://www.keycloak.org/community)
of the project website. It uses [Github issues](https://github.com/keycloak/keycloak/issues)
to track development.

It offers a REST API for administration and there's a separately maintained
3rd party python module as well as ansible support for it. Both of these are
downstream of Keycloak itself and may thus not always be feature complete and
suffer latency with respect to getting adjusted to upstream changes.

It offers support for commonly used SSO protocols and is "reasonably" fast
in adopting to protocol standard changes and extensions. This has been
observed in the case of logout support (backend and frontend variants) in OIDC.

It offers a concept of "Identity Brokering", where Keycloak is not just IdP
but also "client" to other IdPs. This allows daisy chaining of identity
federation. In this configuration it can work as a point of protocol
transition between different supported SSO protocols (SAML, OAuth 2.0, etc.).

Beyond this capability of using other IdPs as identity sources, it also supports
using classic LDAP based IAM services as backend (OpenLDAP and Active Directory,
e.g.).

Keycloaks implementation makes some design decisions, that are specific
to it and have consequences for clients of the service. E.g. Keycloak
has a concept of management "Realms", which have their own specific
set of HTTP API entrypoints, both for administration as well as for IdP
requests.

Commonly Keycloak realms can be used to map them 1:1 to user domains,
but since Keycloak supports configuring multiple backend IdPs in a
realm to be used for "Identity Brokering", there is always the
possibility to create a kind of "proxy" realm to provide a single
standard set of HTTP API endpoints for SSO clients (service providers)
to avoid the need to frequently extend/reduce client service configuration
whenever a new IdP federation needs to be added to Keycloak to onboard
a new customer. This is relevant for services like OpenStack Keystone,
which currently cannot be easily reconfigured for new SSO endpoints
without restarting the service, making the service unavailable for
a short span of time and increasing risk connected with service restarts.

Since version 17, Keycloak claims that it's capability for
"cloud native" deployments on Kubernetes has improved.

[Keycloak is offering a REST API](https://www.keycloak.org/docs-api/20.0.1/rest-api/index.html)
for all aspects of its administration interface.

For storage of Keycloak configuration and local user metadata
(e.g. from which external IdP a user account originally came from)
Keycloak supports several SQL backends through JDBC. Thus
it can be hooked up to a Postgres Database or to a
MariaDB/Galera cluster e.g..

Keycloak is currently being deployed as part of the OSISM testbed.
Technically this IdP component shall be shifted from the management
plane to be run on the basis of a "minimal" Kubernetes (e.g. K3S),
e.g. to make use of the "self healing" and scaling features achievable
with that. As a central service for identity handling, the IdP
service needs to be realy really robust.

### Zitadel

Zitadel is a newer implementation of a SSO IdP. It is implemented
in Go and under active development.

It came to attention of the SCS project because it offers a
fresh take of an organization focussed data model, which has
the potential to simplify IdP federation to SCS customer domains
in the following areas:
* For client services (single set of HTTP API endpoints).
* For SCS operators for provisioning customer [organizations](https://zitadel.com/docs/concepts/structure/organizations)
  and robust configuraton by using templated client, role and mapping
  configuration.
* For SCS customers for a robust user experience for self servicing.

[Zitadel is offering REST APIs](https://zitadel.com/docs/apis/introduction)
for multiple areas of use and configuration.

In comparison to Keycloak it currently lacks support for the
[Device Authorization Grant](https://github.com/SovereignCloudStack/issues/issues/221),
which, at time of writing, is a feauture that is relevant
for SCS to be able use OpenStack CLI and APIs with federated
identities. At Zitadel there are at least two [Github issues](https://github.com/zitadel/oidc/issues/141)
proposed to implement this feature.

Currently it still lacks support to consume identity data from LDAP backends.
This may become relevant in the context of SCS in case we would choose
an LDAP compliant service to store and retrieve SCS local accounts (or
account metadata) for example to have ephemeral workload identities in
the CaaS layer or to track life cycle of SCS artefacts for federated identities.

At time of writing an PoC "spike" is done to assess and verify the hopes
connected with Zitadel in the context of the SCS testbed.

# Open questions

* How would we implement testbed deployment support for Zitadel?
    * e.g. `wsgi-keystone.conf` would need to look different. One template covering both options?
    * e.g. steps like `openstack federation protocol create` would probably be different.
* Should we support both as options?
    * What's the benefit?
    * How would we allow SCS operators to choose?
* Do we need some kind of SWOT analysis to come to a decision?

# Decision

_Decision_

# Related Documents

* https://github.com/SovereignCloudStack/standards/tree/main/Design-Docs/IAM-federation

# Conformance Tests

_Conformance Tests, OPTIONAL_
