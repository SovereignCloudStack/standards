# Proposal for documentation for Keycloak to Keycloak Federation (WebSSO)

The followig section is a reasonably detailed hands on description of how
to configure a federation between two separate SCS compliant domains by means
of Keycloak `Identity Brokering`. If we decide to use Keycloak as a component
to allow self service by tenants, then this documentation may be a useful addition
to some tenant facing documentation (or for the SCS operators too).

OTOH one could probably also script pretty much everything of this to allow
tenants to use a CLI tool to automate the setup. For that purpose the documentation
may be useful to guide the implementation of such a scripted solution.

## Detailed tutorial on how to configure Federation (OpenID Connect) between two Keycloak instances in two separate SCS domains

Assume you have two CSPs using SCS. The first one wants to grant access to users of the other.
So let's call the first domain "resource domain" and the second one "accounts domain".
Both domains need to agree upon a name for the "OIDC RP" (which Keycloak calls `Clients`).
The Keycloak in the "resource domain" will be the OIDC RP and the Keycloak in the "accounts domain" will be the OIDC OP.
Assuming the "resource domain" is called `foo` and the "accounts domain" is called bar, the name for the "OIDC RP" could be `oidc-rp-foo`.

1. In the accounts domain (`bar`) open Keycloak realm `osism`, click on `Clients` in the sidebar and click on `Create client`.
   Leave the client type as `OpenID Connect` and enter the `Client ID`, e.g. `oidc-rp-foo`.
   Turn on `Client authentication` for it and click `Save`.

   On the `Client details` page open the tab `Credentials` and copy the `Client secret`. Communicate this to the operato of the "resource domain" `foo` via a secure channel.

2. In the resource domain (`foo`) open Keycloak realm `osism`, click on `Identity providers`
   and create a new provider definition of type `OpenID Connect v1.0`. As `Alias` choose a name,
   e.g. `oidc-op-bar`. Don't copy the `Redirect URI` given at the top yet, because is will change depending
   on the chosen `Alias`. Instead, scroll down to the mandatory field `Discovery endpoint` and paste
   the OpenID Connect metadata URL of the KEycloak realm `osism` in the "accounts domain" (`bar`).
   The operator of the "accounts domain" (`bar`) may easily copy that URL from the `Realm Settins` in the
   sidebar of his Keycloak instance, where the `Endpoints` are listed on the bottom of that form.
   The URL may have the format `https://bar.com/auth/realms/osism/.well-known/openid-configuration`.
   Once you leave that input field, Keycloak will attempt to fetch the metadata and extract the required
   details about protocol enspoints from the retrieved document. If this shows an error, it will give you
   an HTTP status code. If this shows an error code of 500, then this may be caused by a failure in
   certificate verification. In that case you may want to check the output of `docker logs keycloak` for
   java stack traces. If you find any, the top of those stack traces may indicate what kind of problem
   occurred to the java code. From here we will assume that the emtadata URL could be fecthed without
   any issues.

   Now, go to the bottom of that form and insert tjhe `Client ID` (`oidc-rp-foo`) and the
   `Client secret` that was provided by the operator of the "accounts domain" (`bar`).
   Finally click on `Add`. From the `Provider Details` page on the top for the `Settings` tab copy the value of the
   `Redirect URI` and communicate it back to the operator of the "accounts domain" (`bar`).

3. In the accounts domain (`bar`) open Keycloak realm `osism`, click on `Clients` in the sidebar and click
   on the name of the OIDC RP clinent that you created for domain `foo` (e.g. `oidc-rp-foo`).
   On the `Client details` page on the tab `Settings` fill in the field `Valid redirect URIs` with the value
   obtained from the resource domain (`foo`), which should look similar to
   `https://foo.com/auth/realms/osism/broker/oidc-op-bar/endpoint`. Additionally the
   `Valid post logout redirect URIs` need to be set to something like `https://foo.com/auth/realms/osism/*`.

4. To test federated login in the "resource domain" (`foo`) open the URL of the Keycloak admin console for
   the realm `osism`: `https://foo.com/auth/admin/osism/console` (or `https://foo.com/auth/realms/osism/protocol/openid-connect/auth?client_id=security-admin-console`).
   Ignore the top section of the login form titled
   `Sign in to your account` and choose one of the OIDC OP federation choises below the line `Or sign in with`.
   In this example it would be `oidc-op-bar`. This should redirect your browser to the authentication endpoint
   of the "accounts domain" (`https://bar.com/auth/realms/osism/protocol/openid-connect/auth?scope=openid&...`)
   where you should be able to log in with credentials that are valid in the "accounts domain" (`bar`).
   After successull authentication your broser should be redirected to admin console of the "resource domain",
   which may offer you a "first login flow" form where you can choose a username, email, firstname and lastname.
   The details depend on the `Mappers` that have been configured for the Identity Provider `oidc-op-bar`.
   After that you will be presented with a Keycloak themed page with the error message `Request failed with status code 403`,
   which is normal because the test account is not authorized to access any elements of the Keycloak admin console.
