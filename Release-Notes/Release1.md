# Release Notes for SCS Release 1
(Release Date: 2021-09-29)

## Scope

Main goals for Release 1 (R1) was the strengthening of our CI test coverage and integration,
the operational tooling (metrics collection, dashboards, logging), latest versions of
upstream software (OpenStack Wallaby, Kubernetes-1.21.4), support for Bare Metal
service, progress on user federation for clouds, and progress on the integration of
the container layer with k8s Cluster API (now in version 0.4.x).


## CI framework

### Zuul-CI

For our internal development workflows we are planning to switch from GitHub Actions to Zuul-CI (mostly). The infrastructure itself is already available, yet most of the repositories in the SovereignCloudStack organisation have not switched over. Reasons for switching include cross-dependencies, scalability and costs. Reasons for using Zuul-CI include the close connection to the OpenStack project and the enormous flexibility in comparison to other similar tools. On top of that you have also gating instead of only CI. A quick example for a Zuul-CI operated repository can be found here: https://github.com/SovereignCloudStack/zuul-sandbox.

## Metrics collection and dashboards

### Prometheus exporters and Grafana dashboards

We provide generic configuration examples and blueprints for prometheus rules and grafana dashboards. The examples need to be understood and adapted to the particular needs of your environment. You can find the examples at <https://github.com/osism/kolla-operations>. 

With R2 we plan to implement a basic set of these alerts and dashboards in the testbed deployment in order to make them even easier consumable for new users. Feel free to give feedback on the examples and contribute your own generic examples. 

We're working on bringing a basic set of prometheus exporters to the OpenStack-kolla upstream community. 

As part of our effort to add more monitoring tooling, we're integrating further prometheus exporters such as [libvirt](https://review.opendev.org/c/openstack/kolla-ansible/+/643568) and [ovn](https://review.opendev.org/c/openstack/kolla/+/762986). Integration is targeted for R2.

More detailed information on monitoring topics will be continously provided in the [corresponding design document](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/monitoring.md).

### openstack-health-monitor

### ...

## Logging

### Central logging

OSISM now enables kolla-ansible centralized logging by default. The default rules need to be further refined to suit your needs. We plan to implement a more generic set of rules for R2.

## Federation

### OIDC support via keycloak

Logging in to Horizon by authenticating with OIDC via Keycloak is now possible.
For details see the [testbed documentation](
https://github.com/osism/testbed/blob/8430afdd36307acc1bf5ebd930ecbd3dd4b1dd22/docs/source/usage.rst#authentication-with-openid-connect).

### non-TLS restrictions (testbed)

Only TLS secured deployments get full support.
Without TLS, certain browsers won't be able to log in.
For deatils see the [testbed documentation](
https://github.com/osism/testbed/blob/8430afdd36307acc1bf5ebd930ecbd3dd4b1dd22/docs/source/usage.rst#ssl-tls-connection-to-keycloak-openid-connect-provider)

### Known Issue with OIDC Logout

After clicking `Sign Out` on the Horizon dashboard doesn't perform
a proper OIDC logout. This is documented in [osism testbed](
https://github.com/osism/testbed/blob/8430afdd36307acc1bf5ebd930ecbd3dd4b1dd22/docs/source/usage.rst#openstack-web-dashboard-horizon-logout),
with some Keycloak settings that can be relevant for alleviating the issue,
but in Release 1 there is no solution for this yet.


## Bare Metal Service


## Container Layer 

### Overview and Goals for R1

The container layer on SCS is implemented as a Self-Service,
leveraging the [Kubernetes cluster API](https://cluster-api.sigs.k8s.io/)
technology. This was provided as a technical preview from the
[SCS k8s-cluster-api-provider](https://github.com/SovereignCloudStack/k8s-cluster-api-provider)
repository for R0 back in July.

The focus for R1 was to make it ready for production, so DevOps teams can
use this to create and manage their k8s clusters in self-service for
development, testing, deployment and production.

To achieve this, a lot of work has been invested, updating the
cluster API to 0.4 along the way, fixing snapshot classes, enabling
optional metrics and ingress services, using application credentials
and much improved management scripts. The sonobuoy test automation has
been included and successfully used to validate the created clusters.
Real-world testing has happened though the Gaia-X Hackathon #1, where
clusters were provided on the fly for the various work streams.

The detailed list of changes for R1 is covered in the
[k8s capi provider Release Notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/master/Release-Notes-R1.md).

Still in technical preview, but very promising are the helm charts
based k8s cluster management templates also documented there.

### Beyond CAPI

Some of our partners are using [Gardener](https://gardener.io) as a layer to manage
large fleets of (optionally cross-cloud) k8s clusters. While there is a bit of
overlap in functionality, they do happily coexist and our partner is actually
using k8s capi to bootstrap clusters on SCS clouds for Gardener management.

## Standardization


## SBOM and Links


## List of known issues & restrictions in R1

* [OIDC Logout doesn't work properly](#Known-Issue-with-OIDC-Logout).

* OIDC Login is meant to be used with TLS, on
[non-TLS setups it only works with restrictions](#non-TLS-restrictions-testbed).


