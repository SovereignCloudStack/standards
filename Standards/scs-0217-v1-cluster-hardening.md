---
title: Kubernetes cluster hardening
type: Standard
status: Draft
track: KaaS
---

## Introduction

Due to the regular changes and updates, there are always new security features to deploy and use in Kubernetes.
Nevertheless, a provider (or even a customer) needs to take action in order to achieve a
baseline-secure cluster due to the myriad of configurations possible. This is especially
the case since Kubernetes ships with insecure features and configurations out of the box,
which will need to be mitigated by an administrator with the proper knowledge.
Secure Kubernetes clusters are desirable regardless of the possible threat model,
since higher security doesn't necessarily mean higher complexity in this case.

## Terminology

| Term | Meaning                        |
|------|--------------------------------|
| TLS  | Transport Layer Security       |
| CA   | Certificate Authority          |
| JWT  | JSON Web Token                 |
| ABAC | Attribute-based access control |
| RBAC | Role-based access control      |

## Motivation

Kubernetes clusters are highly configurable, which also gives rise to different security
problems, if the configuration isn't done properly.
These security risks can potentially be exposed in many different parts of a cluster, e.g.
different APIs, authorization and authentication procedures or even Pod privilege mechanisms.
In order to mitigate these problems, different steps and hardening mechanisms could be used
to increase the security of a Kubernetes setup.
Due to the focus of the SCS KaaS standards on the providers, best practices for security
that are more focused on user environments aren't described here, e.g., the possibility for
network traffic control between pods. This could theoretically be set up by a provider,
but isn't very practical for the user, since he would probably need to request changes
regularly in this case.

## Hardening Kubernetes

This section is non-authoritative and only describes concepts and design considerations.

### Regular updates

Due to the risk associated with running older versions of software, e.g. known security vulnerabilities,
bugs or missing features as well as the difficulty of tracking or identifying attack vectors,
it is advised to first and foremost keep the version of the Kubernetes components up-to-date.
It should be especially important to keep on track with the patch-level [versions of Kubernetes][kubernetes-releases],
since they include bugfixes and security patches, which are also backported to the previous
three minor-level versions, depending on their severity and the feasibility. It is also recommended
to refer to the version skew policy for more details about [component versions][kubernetes-version-skew].

### Securing etcd

The etcd database is the storage for Kubernetes, containing information about cluster workloads, states and secrets.
Gaining access to this critical infrastructure part would enable a bad actor to read the aforementioned information;
write access would be equivalent to administrative access on the Kubernetes cluster and information could be manipulated
while ignoring any restrictions or validations put in place by other Kubernetes components.

Securing etcd can be done through different or a combination of
many mechanisms, including strong security credentials for the etcd server, the isolation of the etcd servers behind a firewall, separate etcd
instances for components beside the API-server, ACL restrictions for read-write-access to subsets of the keyspace and
a separate CA for etcd communication, which limits the trusted partners of the etcd database to clients with a certificate from this CA.
These strategies will be explained a bit more in-depth in the following subsections.

#### Strong authentication

If an etcd instance wasn't secured correctly, it could be possible that a bad actor would try to authenticate against
the database.
It is therefore advised to use strong security credentials (see e.g. [the strong credentials requirements by NIST][strong-credentials]) for
all user accounts on the etcd server as well as the machines running this critical component.
This is obviously a fact for all possibly accessible components, but especially true for etcd, since it contains
the complete cluster state.

#### Multiple etcd instances

etcd is a critical component that needs to be protected from
bad actors as well as outages. Kubernetes recommends a [five-member cluster](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#multi-node-etcd-cluster) for durability and high-availability as well as regular back-ups of the data.
For more information on high-availability, look into the [Kubernetes Node Distribution and Availability Standard](scs-0214-v1-k8s-node-distribution.md).
It would also be possible to use these etcd instances in order to select specific instances
that aren't the current etcd leader for interaction with different components (e.g. Calico), since access to the primary etcd instance could be considered dangerous, because the full keyspace could be viewed without further restrictions (see [here](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html#limiting-access-to-the-primary-etcd-instance) or [here](https://docs.tigera.io/calico/latest/reference/etcd-rbac/kubernetes-advanced)).
This approach should still be paired with [etcd ACL](#acl-restrictions) to better restrict access.

#### etcd isolation

The etcd database should at best be isolated from the rest of a Kubernetes cluster.
Access should only be granted to components that need it, which is in most cases mainly (or only)
the API server. Best practice would be to host etcd on machines separate from the Kubernetes cluster
and block access from machines or networks that don't need access with specific firewall rules.
In most cases, only the API server machines should need access to etcd on ports 2379-2380.

#### ACL restrictions

etcd implements access control lists (ACL) and authentication since version 2.1 [1][etcd-auth].
etcd provides users and roles; users gain permissions through roles. When authentication is enabled,
each request to etcd requires authentication and the transaction is only allowed, if the user has the correct access rights.
etcd can also be launched with `--client-cert-auth=true`, which enables authentication via
the Common Name (CN) field of a client TLS certificate without a password.
This option enables Kubernetes components to authenticate as a user without providing a password,
which is neither possible for Kubernetes components nor planned in future releases.
This method is recommended in order to implement ACL for different Kubernetes components and
not give the Kubernetes API full root access to the etcd instance; instead, a separate user can be created.

#### TLS communication

etcd should use TLS for peer- and cluster-communication, so that traffic between different peered etcd instances as well
as the communication with the Kubernetes cluster can be secured.
etcd provides options for all these scenarios, including `--peer-key-file=peer.key` and `--peer-cert-file=peer.cert`
for securing peer communication and the flags `--key-file=k8sclient.key` and `--cert-file=k8sclient.cert` for securing
client communication (and therefore cluster communication).
Additionally, HTTPS should be used as the URL schema.
It is also possible to use a separate CA for the etcd in order to separate and better control access through client
certificates, since etcd by default trusts all the certificates issued by the root CA [2][nsa-cisa].
More information about authentication via TLS is provided in the chapter [ACL restrictions](#acl-restrictions).

### Securing endpoints

Kubernetes provides a well-defined set of ports in its default configuration. These ports are
used for inter-component communication as well as external access. Due to the distribution of information
about Kubernetes clusters, it is easy for a bad actor to identify a clusters
ports and try to attack them. In order to minimize the attack vector, internal ports (and therefore components)
should not be accessible from external networks, except if there are requirements to enable this behavior.

A good way to restrict access would be a combination of firewalls with port
blocking and the integration of network separation.
How this is done is highly dependent on the specific setup of the provider.
An additional document could be provided in the future to give basic
guidelines for this task.

A list of the default ports used in Kubernetes as well as the components accessing them can be found below:

#### Control plane nodes

| Ports     | Protocol | Purpose                 | Used by               | Access type        |
|-----------|----------|-------------------------|-----------------------|--------------------|
| 6443      | TCP      | API server              | All                   | External, internal |
| 2379-2380 | TCP      | etcd server             | kube-apiserver, etcd  | Internal           |
| 10250     | TCP      | Kubelet API             | Self, Control plane   | Internal           |
| 10255     | TCP      | Read-only Kubelet API   | External applications | External, Internal |
| 10257     | TCP      | kube-controller-manager | Self                  | Internal           |
| 10259     | TCP      | kube-scheduler          | Self                  | Internal           |

Hint: `Self` in the `Used by` context means, that a resource will access its own port for requests.

#### Worker nodes

| Ports       | Protocol | Purpose               | Used by               | Access type        |
|-------------|----------|-----------------------|-----------------------|--------------------|
| 10250       | TCP      | Kubelet API           | Self, Control plane   | Internal           |
| 10255       | TCP      | Read-only Kubelet API | External applications | External, internal |
| 30000-32767 | TCP      | NodePort Services     |                       | External           |

### API security, authentication and authorization

In order to secure Kubernetes against bad actors, limiting and securing access to API requests
is recommended, since requests to those are able to control the entire Kubernetes cluster.
Access control is applied to both human users and Kubernetes service accounts, which goes through
several stages after a request reaches the API.

1. The Kubernetes API server listens on port 6443 on the first non-localhost network interface by default,
protected by TLS [3][controlling-access]. The TLS certificate can either be signed with a private CA or based on a public key
infrastructure with a widely recognized CA behind it.
2. The authentication step checks the request for correct authentication based on different possible
authentication modules like password, plain tokens or JWT. Only one of these methods needs to succeed
in order to allow a request to pass to the next stage.
3. The authorization step authorizes a request, if a user is allowed to carry out a specific operation.
The request must contain the username of the requester, the requested action and the affected object.
Kubernetes supports different authorization modules like ABAC, RBAC or Webhooks. Only one of these
modules need to approve the request in order for it to be authorized.
4. The last step are Admission control modules, which can modify or reject requests after accessing
the objects contents.

#### Authentication

Kubernetes provides different internal authentication mechanisms, that can be used depending
on the requirements of the cluster provider and user. Multiple authentication systems can
be enabled and the [Kubernetes documentation][kubernetes-auth] recommends at least using two methods,
including Service Account Tokens and another method. Methods directly provided by Kubernetes include
the following (a more complete or up-to-date list may be found in the [Kubernetes authentication docs][kubernetes-auth]):

- *Static Token Files*

  This method reads bearer tokens from requests and checks them against a CSV file provided to Kubernetes containing
  three columns named `token`, `username` and `uid`. These tokens last indefinitely and the list can't be changed
  without a restart of the API server. This makes this option unsuitable for production clusters.

- *Service Account Tokens*

  A service account is an authenticator that uses signed bearer tokens for request verification.
  Service accounts can be given to the API server with a file containing PEM-encoded X509 RSA or
  ECDSA private or public keys that verify the Service Account Tokens.
  Service Accounts are normally created automatically by the API server and associated with the
  pods through the `ServiceAccount` admission controller. Tokens are signed JSON Web Tokens,
  that can be used as a Bearer Token or mounted into the pods for API server access.
  Since Service Account Tokens are mainly used to allow workloads accessing the API server,
  they're not really intended to authenticate users in production clusters.

- *X509 client certificates*

  Client certificate authentication can be enabled by providing a `Certificate Authority`
  file to the API server via the `--client-ca-file=` option. The file contains one
  or more CAs that a presented client certificate is validated against.
  In this case the common subject name is used as the username for the request;
  additionally, a group membership can be indicated with the certificates organization field.
  These certificates are unsuitable for production use, because Kubernetes does not
  support certificate revocation. This means user credentials can't be modified or
  revoked without rotating the root CA and re-issuing all cluster certificates.

As outlined, most internal authentication mechanisms of Kubernetes aren't really
usable in productive environments at the current time. Instead, external authentication
should be used in order to provide production-ready workflows.
The Kubernetes documentation lists a few examples for external authenticators, e.g.

- [OpenIDConnect][openidconnect]
- Bearer Tokens with [Webhook Token Authentication][webhook-token]
- Request Header Authentication with an [Authenticating Proxy][authenticating-proxy]

All of these examples are useful to set up for an organization or can be used with
an already in-place solution. More information can be found in their respective
part of the Kubernetes documentation.
Most of these are good solutions for productive setups, since they enable easy
user management, access revocation and things like short-lived access tokens.
What will be used by your organization depends on the present setup and the use case.

#### Authorization

Authorization is done after the authentication step in order to check the rights
of a user within the system. Kubernetes authorizes API requests with the API server,
which evaluates requests against all policies in place and then allows or denies these requests.
By default, a request would be denied.

Kubernetes provides several authentication modes to authorize a request:

- *Node*

  The [Node authorization mode][node-authorization] grants permission to a Kubelet
  based on the scheduled pods running on them. It allows a Kubelet to perform specific
  API operations. The goal is to have a minimal set of permissions to ensure
  the Kubelet can operate correctly.
  Each Kubelet identifies with credentials belonging to the `system:nodes` group and
  a username `system:nodes:<node>` against this authorizer.

- *ABAC (Attribute-based access control)*

  ABAC grants access rights based on policies dependent on attributes like
  user attributes, resource attributes or environment attributes.
  An example would be the `resource` attribute, which could limit access for a user
  to only `Pod` resources.

- *RBAC (Role-based access control)*

  RBAC is a method of regulating access to the resources based on the roles of
  individual users. A user therefore must have the ability to perform a specific set
  of tasks with a set of resources based on his role.
  Kubernetes implements `Role`s to accomplish this and binds these with `Role Binding`s
  to a user in order to specify his permission set.

- *Webhook*

  Webhook authorization uses an HTTP callback to check the authorization of a user
  against a URL provided for this mode. This externalises the authorization part
  outside of Kubernetes.

Most organizations and deployments work with RBAC, most often due to organizational or
customer-owner-relationship-like structures in place.
Nonetheless, neither ABAC, RBAC nor Webhook authorization can be recommended over the
other, since this all depends on the use case and required structure of a deployment.
Using at least one of these modes is recommended.

It is also recommended to enable the Node authorizer in order to limit Kubelet
permissions to a minimum operational state.

#### Admission Controllers

Admission controllers intercept requests to the Kubernetes API after the
authentication and authorization step, which validate and/or mutate the request.
This step is limited to `create`, `modify` and `delete` objects as well as custom
verbs, but other requests are not blocked.
Kubernetes provides multiple admission controllers, some of which are enabled by default.

One recommended admission controller is the [`NodeRestriction` controller][node-restriction],
which limits the `Node` and `Pod` objects a Kubelet is allowed to modify to their own `Node` or
objects that are bound to them. It also disallows updating or removing taints and prevents changing
or adding labels with a `node-restriction.kubernetes.io/` prefix.
Be aware that Kubelets will only be limited by this admission controller, if the user credentials
in the `system:nodes` group begin with a `system:node:<nodeName>` username. Administrators must therefore
configure their Kubelets correctly, if the `NodeRestriction` controller should be fully functional.

### Dynamic Admission Controllers

Policy engines such as [Kubewarden](https://kubewarden.io) & [OPA
Gatekeeper](https://www.openpolicyagent.org/ecosystem/entry/gatekeeper) use
Kubernetes' [dynamic admission
control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
feature. The Kubernetes API server exposes validating and mutating webhooks, to
which these policy engines connect to. The API server waits for responses from
these webhooks before processing resource requests. While policy engines
provide powerful policy, compliance, and logging capabilities that extend
Kubernetes, they also increase the attack surface of the cluster; if a policy
engine is misconfigured or exploited, attackers could cause general denial of
service (DoS), or exfiltrate data from the cluster.

SIG security provides a [threat model for Kubernetes Admission
Control](https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/admission-control/kubernetes-admission-control-threat-model.md).
Policy Engines usually provide their mitigations to this threat model in their
documentation. The majority of scenarios are mitigated by the Policy Engines
themselves or by cluster operators when using NetworkPolicies and therefore are
out of scope for this standard.

However, for some threats, such as threat 8, _"attacker carries out a MITM
attack on the webhook"_, and threat 9, _"attacker steals traffic from the webhook
via spoofing"_, NetworkPolicies and policy engine configuration doesn't suffice.

These threats involve intercepting traffic between the Kubernetes API server
and the dynamic admission controller webhooks of the Policy Engine. To mitigate
this, the Kubernetes API server MUST be configured with mutual TLS
authentication for the Validating and Mutating Webhooks (see [Kubernetes
docs](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#authenticate-apiservers))
. The Policy Engine MUST be able to authenticate the API server and MUST be
configured with mutual TLS authentication for the
webhooks as well.

### Kubelet access control

The Kubelet is the node agent that runs on each node. It registers with the API
server and ensures, that pods handed over to it are running and healthy according
to the specification provided to it. The HTTPS endpoint of a Kubelet exposes APIs
with varying access to sensitive data and also enables various levels
of performant operations enabling manipulation of node data and containers.
There is also a read-only HTTP endpoint that was used for monitoring a Kubelet and
its information. This port was also used by applications like `kubeadm` to check
the health status of the Kubelet.
This port is still available, but it is planned to be [removed][ro-port-removal]
in a future version. At the moment, the port is disabled by default since [Kubernetes 1.10][ro-port-disabled]
and shortly later also in [`kubeadm`][ro-port-disabled-kubeadm].
Different sources recommend disabling this port [4][ro-port-s1] [5][ro-port-s2] due to possible
security risks, but since this standard recommends restricting accessibility of internal ports,
this port wouldn't be accessible from external networks.
It is nevertheless recommended to keep this port disabled, since Kubernetes also acknowledged
its risks and plans to remove it.

By default, the API server does not verify the Kubelets serving certificate and
requests to the HTTPS endpoint that are not rejected by other authentication
methods are treated as anonymous requests with the combination of name `system:anonymous`
and group `system:unauthenticated`.
This can be disabled by starting the Kubelet with the flag `--anonymous-auth=false`,
which return `401 Unauthorized` for unauthenticated requests.
It is also possible to enable internal authentication methods for the Kubelet.
Possibilities include X509 client certificates as well as API bearer tokens to
authenticate against the Kubelet; details for these methods can be found in the [Kubernetes docs][kubelet-auth].

After a request is authenticated, the authorization for it is checked, with the default
being `AlwaysAllow`. Requests should at best be authorized depending on their source,
so differentiation of access makes sense for the Kubelet; not all users should have
the same access rights. How access can be configured and delegated to the Kubernetes
API server can be found in the [Kubernetes docs][kubelet-auth]. The process works like the API request
authorization approach with verbs and resources being used as identifiers in roles and role bindings.

### Pod security policies

Pod security plays a big part in securing a Kubernetes cluster, since bad actors could use pods to gain
privileged access to the systems underneath. The security risk here is mainly influenced by the capabilities
and privileges given to a container. It is therefore recommended to apply the principal of "least privilege",
which should limit the security risk to a minimum.

Kubernetes defines the [*Pod security standards*][pod-security-standards]
in the form of three policies that try to cover the range of the security spectrum.
These policies can be found in the following list and define a list of restricted fields that can only be
changed to a set of allowed values. An up-to-date list of these values can be found [here][pod-security-standards].

- *Privileged*

  Unrestricted policy, providing the widest possible level of permissions.
  This policy allows for known privilege escalations.

- *Baseline*

  Minimally restrictive policy which prevents known privilege escalations.
  Allows the default (minimally specified) Pod configuration.

- *Restricted*

  Heavily restricted policy, following current Pod hardening best practices.

Kubernetes also offers the *Pod security* admission controller, which enforces
the *Pod security standards* on a namespace level during pod creation.
The admission controller defines the standard to be used with the three levels
`privileged`, `baseline` and `restricted`. Each namespace can be configured to enforce
a different control mode, which defines what action the control plane takes
after a violation of the selected *Pod security* is detected.

- `enforce`

  Policy violations will cause the pod to be rejected.

- `audit`

  Policy violations will trigger the addition of an audit annotation to the event
  recorded in the audit log, but are otherwise allowed.

- `warn`

  Policy violations will trigger a user-facing warning, but are otherwise allowed.

Be aware, that `enforce` is not applied to workload resources, only to the pods created from their template.

### Further measurements

While researching this topic, further measurements were considered such as container image verification,
distroless images, usage of `ImagePolicyWebhook`, network policy enforcement,
container sandboxing and prevention of kernel module loading.
Most of these were taken out of the document during writing due to either being the responsibility
of the clusters' user (and therefore not possible to implement for the provider), being more relevant
for high security clusters or changing the expected cluster environment too much, so that normally
expected operations could potentially not work in such a modified cluster.
These measurements will possibly be introduced in a future document about higher security clusters.

## Standard

This standard provides the baseline security requirements for a cluster in the SCS context.

Kubernetes clusters MUST be updated regularly in order to receive bugfixes and security patches.
For more information refer to the [SCS K8s Version Policy](scs-0210-v2-k8s-version-policy.md),
which outlines the version update policies of the SCS.

Hardening etcd is important due to it being a critical component inside a Kubernetes cluster.
etcd SHOULD be isolated from the Kubernetes cluster by being hosted on separate (virtual) machines.
If this is the case, access to these instances MUST be configured, so that only the API server and
necessary cluster components requiring access can access etcd.
Communication with etcd MUST be secured with TLS for both peer- and cluster-communication.
It is RECOMMENDED to use a CA separate from the one used for the Kubernetes cluster for etcd in
order to better control and issue certificates for clients allowed to access etcd.
ACL MUST be enabled for etcd, which allows better control of the access rights to specific key sets
for specific users. Authentication MUST be done via the Common Name (CN) field of the TLS client
certificates (since normal username-password-authentication isn't implemented for Kubernetes).

Kubernetes' endpoints MUST be secured in order to provide a small attack surface for bad actors.
It MUST NOT be possible to access Kubernetes ports from outside the internal network hosting the
Kubernetes cluster except for the ports of the API server (default 6443) and the NodePort Services
(default 30000-32767). The read-only Kubelet API port (default 10255), which is mostly used for monitoring,
SHOULD be disabled altogether if it isn't in use, mainly because the port is HTTP-only
and can deliver sensitive information to the outside.
Endpoints MUST be secured via HTTPS.

Securing Kubernetes via authentication and authorization is another important topic here.
Authentication is possible through multiple mechanisms, including Kubernetes-provided systems as well as external
authentication processes.
A cluster MUST implement at least two methods for authentication. One of these MUST be *Service Account Tokens*, in order
to provide full functionality to Pods. A second authentication mechanisms can be chosen depending on the requirements
of the provider and/or customer.

Authorization also can be provided through multiple mechanisms.
A cluster MUST activate at least two authorization methods, one of which MUST be *Node authorization* and another one
consisting of either ABAC, RBAC or Webhook authorization depending on the required use case.
We RECOMMEND RBAC due to it fitting most use cases and being very well documented, but your setup might require another solution.

In order to harden Kubelet access control, a Kubelet SHOULD only be accessible internally via HTTPS. This is already the
case for the Kubelet API, except for the read-only port, which is only available as HTTP. As mentioned earlier, this port
should be disabled.
Kubelets MUST disable anonymous request authentication to disallow non-rejected requests to go through as anonymous requests.
OPTIONALLY, X509 client certificate authentication or API bearer token authentication can be enabled.
Request authorization for the Kubelet MUST be delegated to the API server via `Webhook` authorization as it is recommended
by the [Kubernetes documentation][kubelet-auth].
Additionally, the `NodeRestriction` admission controller MUST be activated in order to limit interactions between
different Kubelets by disallowing modification of `Pod` objects, if they're not bound to the Kubelet requesting the modification.

At last, *Pod security standards* in the form of policies MUST be activated for the cluster. The SCS REQUIRES at least
the *Baseline* policy with the *Restricted* policy CAN also be used.
The *Pod security* admission controller MUST also be activated in order to enforce these policies on a namespace level.
We RECOMMEND the `enforce` level to be used for this admission controller setup.

## Conformance Tests

Conformance Tests will be written within another issue.

## Related Documents

- [OWASP Kubernetes Security Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)
- [Kubernetes security concepts](https://kubernetes.io/docs/concepts/security/)
- [Securing a cluster](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/)
- [Controlling access](https://kubernetes.io/docs/concepts/security/controlling-access/)
- [Pod security standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [NSA CISA Kubernetes hardening](https://kubernetes.io/blog/2021/10/05/nsa-cisa-kubernetes-hardening-guidance/)
- [Configure etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Google Kubernetes cluster trust](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-trust)

[kubernetes-releases]: https://kubernetes.io/releases/
[kubernetes-version-skew]: https://kubernetes.io/releases/version-skew-policy/
[strong-credentials]: https://pages.nist.gov/800-63-3/sp800-63b.html
[kubernetes-auth]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/
[node-authorization]: https://kubernetes.io/docs/reference/access-authn-authz/node/
[node-restriction]: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction
[kubelet-auth]: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/#kubelet-authorization
[pod-security-standards]: https://kubernetes.io/docs/concepts/security/pod-security-standards/
[openidconnect]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens
[webhook-token]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication
[authenticating-proxy]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#authenticating-proxy
[controlling-access]: https://kubernetes.io/docs/concepts/security/controlling-access/

[ro-port-removal]: https://github.com/kubernetes/kubernetes/issues/12968
[ro-port-disabled]: https://github.com/kubernetes/kubernetes/pull/59666
[ro-port-disabled-kubeadm]: https://github.com/kubernetes/kubeadm/issues/732
[ro-port-s1]: https://www.stigviewer.com/stig/kubernetes/2021-04-14/finding/V-242387
[ro-port-s2]: https://docs.datadoghq.com/security/default_rules/cis-kubernetes-1.5.1-4.2.4/
[nsa-cisa]: https://kubernetes.io/blog/2021/10/05/nsa-cisa-kubernetes-hardening-guidance/
[etcd-auth]: https://etcd.io/docs/v3.3/op-guide/authentication/
