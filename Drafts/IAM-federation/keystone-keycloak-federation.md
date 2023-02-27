# Identity Federation in SCS

## Keystone to IdP Federation

The Keystone container can be configured via wsgi-keystone.conf
to delegate authentication decisions to external identity providers
like Keycloak. This can be done using OpenID Connect, OAUTH2, SAML
and Shiboleth.  Currently the SCS testbed deploys a configuration
that uses OpenID Connect for WebSSO and oauth2 for openstack CLI.

The idea is to use an IdP as switch hub for authentication
and to give each tenant his own realm in keycloak, where he can
e.g. configure several aspects, e.g. so called "Identity Brokering"
out to other SCS compliant domains or to customer owned IdPs external
to SCS. The tenant shall be offered the option to adjust configuration
of the identity federation and role mapping himself (self service).

Please note that the term "Federation" is used to denote different
things in different software contexts. Keystone itself can also do
federation to other Keystone instances (`k2k`) but reportedly it has
certain limitations in that regard, e.g. required restarts when adding
new tenants (TODO: Check this argumentation).

Please also note that "Federation" is a 1:1 relation between a
service provider (or `relying party` in OAauth terminology,
in this case Keystone) and an identity provider
(IdP, for example Keycloak or Zitadel).

Beyond that Keycloak can do `Identity Brokering`, where,
**if explicitly instructed** to do so, it can delegate an
authentication decision to a **specific** secondary, remote identity
provider (e.g. a Keycloak in a separate remote SCS compliant environment).
This distinction is important as `Identity Brokering` may put additional
restrictions on the type of authentication flow that can be used.
Keycloak supports `Identity Brokering` for the WebSSO case ("Authorization
Code grant"), where the client specifies the desired IdP, either interactively
or via `&kc_idp_hint` URL parameter. See the
[Keycloak documantion](https://www.keycloak.org/docs/latest/server\_admin/#_identity_broker)
for an overview.

There are several different authentication flows possible with OAuth 2.0,
each of which has its own specific use cases:

For WebSSO the `Authorization Code Grant` is used frequently
(see e.g. https://oauthlib.readthedocs.io/en/latest/oauth2/grants/authcode.html ).
This also works for daisy chained federation setups (i.e. "Identity Brokering").

For OpenStack CLI on the other hand this flow cannot be used (without ugly workarouds).
Instead we will use a different OAuth 2.0 flow. See below for more.

Currently the SCS testbed deploys a Keycloak wsgi configuration that uses OpenID Connect for WebSSO:
```
    <LocationMatch /v3/auth/OS-FEDERATION/identity_providers/keycloak/protocols/openid/websso>
      Require valid-user
      AuthType openid-connect
    </LocationMatch>
```
And a second location for `oauth2` clients like openstack cli:
```
    <LocationMatch /v3/OS-FEDERATION/identity_providers/keycloak/protocols/mapped/auth>
      Require valid-user
      AuthType oauth2
      OAuth2TokenVerify jwks_uri https://keycloak.testbed.osism.xyz/auth/realms/osism/protocol/openid-connect/certs
      OAuth2TargetPass prefix=OIDC-
    </LocationMatch>
```

I.e. both login flows use different modules for `AuthType`.

### Horizon WebSSO

The SCS testbed deploys horizon, keystone and keycloak configured to support
Horizon login via OpenID Connect against Keycloak. The drawback of this approach
is, that Horizon shows all selectable tenant realms (Keycloak) in a dropdown box
to select from. This is not business ready, and one would probably need to provide
dedicated login pages per tenant instead. (TODO: Verify this with other members of SIG-IAM).

This kind of federated SSO login uses the standard "Authorization Code grant".
If the Keycloak realm of the specific tenant is configured to itself federate out
(i.e. act as service provider) to a separate remote identity provider, like a
Keycloak in a separate SCS comliant domain, then this can be selected by the
authenticating user. That feature of Keycloak is referred to as `Identity Brokering`.
The "Authorization Code grant" flow of federation and the `Identity Brokering`
both make use of browser redirects, either explicitly via HTTP or via javascript calls
(TODO: back this up with documentation. The latter was only observed in the browser network
console and seems to be described in the standards too).

### Openstack CLI

The Keystone container as deployed by OSISM, which builds on top of kolla-ansible
and is part of the IaaS reference implementation of SCS, is configured to support
authentication flows where openstack CLI fetches an auth token directly from Keycloak
in the first step and then, in a second step, passes that auth token
to the Keystone container for authorization. This second step requires verification
of the token, which is done by using the `mod_oauth2` module in apache2.
See openstack-v3oidcpassword.drawio for a simple sequence diagram.

