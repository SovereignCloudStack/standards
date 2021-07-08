# Identity and Access Management - Use cases

- Provide identities to consumer payloads
  - **Example:** Provide credentials to access Cortex
  - **Example:** Provide credentials to implement K8s `Service`s with type `LoadBalancer` (e. g. backed by OpenStack load balancer)
- Provide identities to consumer employees
  - **Example:** Provide SSO/OAuth2 to access monitoring dashboards and Cortex
  - **Example:** Provide identity aware access to payload K8s clusters (providing K8s `User`/`Group`)

# To be discussed

- Should payload and employee identities be managed by the same system?
- How to securely provide credentials to payload?
  - Use of K8s `ServiceAccount` tokens? (Maybe providing some more privileged proxy component which proxies "K8s local" authorized requests to the outside)
  - Use of OpenStack Metadata service? (Secret would be plain text in OpenStack database, so they should be used only once initially)
  - Use of Vault/Barbican managing secrets? (Could implement access to other services, but access to the vault service itself is not covered)
- How to securely provide credentials to consumer employees?
