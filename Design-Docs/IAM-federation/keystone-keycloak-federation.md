# Identity Federation in SCS

## Keystone to Keycloak Federation

The Keystone container can be configured via wsgi-keystone.conf
to delegate authentication decisions to external identity providers
like Keycloak. This can be done using OpenID Connect, OAUTH2, SAML
and Shiboleth.  Currently the SCS testbed deploys a configuration
that uses OpenID Connect for WebSSO and oauth2 for openstack CLI.

The idea is to use Keycloak as switch hub for authentication
and to give each tenant his own realm in keycloak, where he can
e.g. configure several aspects, e.g. so called `identity brokering`
out to other SCS compliant domains. This could be done be the
tenant himself (self service).

Please note that the term `Federation` is used to denote different
things in different software contexts. Keystone itself can also do
federation to other Keystone insances but reportedly it has certain
limitations in that regard, e.g. required restarts when adding new
tenants (TODO: Check this argumentation).

Please also note that `Federation` is a 1:1 relation between a
service provider (in this case Keystone) and an identity provider
(in this case Keycloak). There are several different authentication
flows to achieve this, each of which has its own specific use cases.
For WebSSO the "Authorization Code grant" is used
(see e.g. https://oauthlib.readthedocs.io/en/latest/oauth2/grants/authcode.html ).
It's still subject of research, which flow/grant type will
be used for openstacl CLI, but in 2022-02 it was demonstrated in a PoC
that the "Resource Owner Password grant" (keystoneauth plugin `v3oidcpassword`)
can be used for `Federation` between Keystone and Keycloak.

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

### Horizon WebSSO

The SCS testbed deploys horizon, keystone and keycloak configured to support
Horizon login via OpenID Connect against Keycloak. The darwback of this approach
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

As demonstrated in a PoC in 2022-02, the Keystone container in the SCS testbed can
be configured with the help of `mod_oauth2` to support a different kind of authentication
flow, which allows openstack CLI to fetch an auth token directly from Keycloak in the first
step and then pass that auth token to the Keystone container for authorization. This second
step requires verification of the token, which is done by using the `mod_oauth2` module in
apache2. See openstack-v3oidcpassword.drawio for a simple sequence diagram.

