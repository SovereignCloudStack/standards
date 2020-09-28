# Identity and Access Management - Use cases

- Provide identities to consumer payloads
  - **Example:** Provide credentials to access Cortex
  - **Example:** Provide credentials to implement K8s `Service`s with type `LoadBalancer` (e. g. backed by OpenStack load balancer)
- Provide identities to consumer employees
  - **Example:** Provide SSO/OAuth2 to access monitoring dashboards and Cortex
  - **Example:** Provide identity aware access to payload K8s clusters (providing K8s `User`/`Group`)
