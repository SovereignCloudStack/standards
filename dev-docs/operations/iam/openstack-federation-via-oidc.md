---
title: OpenStack Federation via OpenID-Connect
type:
status: Draft
track: Global
---

Keystone supports federating authentication and authorization decisions via several mechanisms
as [documented by the project](https://docs.openstack.org/keystone/latest/admin/federation/introduction.html).

In SCS OpenID Connect is used for federation between Keystone and the IdP, which is
[currently provided by Keycloak](https://docs.scs.community/standards/scs-0300-v1-requirements-for-sso-identity-federation)
in SCS.

The following sections describe the setup.

## 1. Keystone

[Keystone supports federated identities](https://docs.openstack.org/keystone/latest/admin/federation/federated_identity.html).
To allow SCS to consume identities managed in external IAM solutions,
federation protocols like OpenID Connect or SAML can be used.
Keystone currently makes use of third party apache modules like
[mod_auth_openidc](https://github.com/OpenIDC/mod_auth_openidc),
[mod_oauth2](https://github.com/OpenIDC/mod_oauth2) and
[mod_auth_mellon](https://github.com/UNINETT/mod_auth_mellon) to delegate
authentication to a SSO IdP (i.e. SAML IdP or OpenID Connect provider).

In OpenStack the apache modules are configured using the
[wsgi-keystone.conf template](https://github.com/openstack/kolla-ansible/tree/master/ansible/roles/keystone/templates).

In SCS we make use of the OAuth 2.0 Authorization Code Grant flow between Keystone and Keycloak
and use PKCE (RFC 7636) with the S256 challenge method.

In addition to the usual SSL CA of the environment, Keycloak uses separate certificates to sign the OIDC tokens.

Due to the way the Keystone container image runs apache (in the foreground) and keystone itself (as WSGI module),
reconfiguring the apache URL locations on the fly is not possible currently without a downtime of several seconds.
That is the reason why SCS currently makes use of a single central proxy realm in Keycloak, to which Keystone
connects.

### 1.1 Keycloak IdP realm discovery

Keycloak offers standard OIDC service discovery via `.well-known` documents to advertise its endpoints.

In SCS we want to represent each customer by a separate dedicated Keycloak realm, which can enventually be used
for customer self service and to federate out to customer owned IAM external solutions.

In the SCS testbed we currently experiment with the implications of using a single central proxy realm in Keycloak
and chaining federation from there to customer specific realms, also hosted in the same Keycloak instance.
To make this usable, SCS makes use of the
[Keycloak Home IdP Discovery](https://github.com/sventorben/keycloak-home-idp-discovery)
extension.

### 1.2 Keystone mapping of token claims

Upon login of a user Keystone evaluates the credentials obtained from the ID token that the IdP issued.
These include group memberships and roles, which can be used to assign the user to a certain project.
Keystone maps these external identities to internal (shadow) users.
It can either attempt to map the obtained information to a `local` type user, which needs to be
provisioned before authentication by external tooling, or it can be instructed via the mapping to
generate an `ephemeral` type user. `ephemeral` users are cleaned up automatically after some time
of inactivity and with that, they lose access to projects, iff the access is granted indirectly
via group membership rather than directly to the user itself.

Group memberships for `ephemeral` users are only represented via their tokens, but not stored in the
Keystone backend database.

After successful authorization Keystone issues an OpenStack specific `fernet` token to the user,
which is the currency that is understood by other OpenStack services and can be used to access them.

In SCS we want to represent each customer by a sepatate dedicated OpenStack domain to host
their projects and (shadow) user accounts.

The processing of information from the OIDC tokens is configured by two parts. The first part is the
`rules.json` mapping which is described in the
[OpenStack federation mapping combinations](https://docs.openstack.org/keystone/latest/admin/federation/mapping_combinations.html)
document. This file is used to configure Keystones internal mapping engine
and it needs to be attached to some OpenStack domain, which is named `keycloak` by default in SCS.

The second (static) part is the `[auth]` and `[mapped]` sections in `keystone.conf` (see e.g.
[the overlays currently used in the OSISM testbed](https://github.com/osism/testbed/tree/main/environments/kolla/files/overlays/keystone)
).

### 1.3 Horizon WebSSO for federated users

The Horizon dashboard supports login via OpenID Connect via Keystone endpoint.
SCS adjusted the logout behavior to invalidate both, the OpenID Connect session
with the IdP and the Keystone token.

### 1.4 OpenStack CLI and API access for federated users

To support OpenStack CLI and API access, SCS implemented support for the OIDC Device Authorization Grant
in Keystone. On top we added support for PKCE (RFC 7636) in combination with that.

### 1.5 SSO Federation between to SCS deployments

To show the potential of this approach to federation SCS created a
[Howto for OIDC federation between SCS deployments](https://docs-staging.scs.community/docs/iam/intra-SCS-federation-setup-description-for-osism-doc-operations).
