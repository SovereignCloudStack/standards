# Release Notes for SCS Release 2
(Release Date: 2022-03-23)

## Scope

Main goals for Release 2 (R2) were massive improvements in bare
metal deployment and our cluster management layer gaining the
ability to handle many clusters independently with a number
of optional services.

## Component Versions and User-visible improvements (highlights)

* We support the latest [Kubernetes 1.22](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.22.md) and 
  [1.23](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.23.md) releases.
* The Kubernetes Cluster API is now available in a stable v1beta1
  [release 1.0.x](https://github.com/kubernetes-sigs/cluster-api/releases)
  with the corresponding [cluster-api-provider-openstack 0.5.x](https://github.com/kubernetes-sigs/cluster-api/releases).
* There are a number of new standard services available for the
  [k8s capi](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/)
  managed clusters, amongst which cert-manager and flux. The clusters
  have better default settings for the nginx-ingress, anti-affinity
  for the nodes and the ability to chose cilium over calico and
  to have stable multi-controller node setups on clouds without
  low-latency local storage.
  Please consult the
  [k8s capi provider release notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/master/Release-Notes-R2.md)
  for more details.
* [OpenStack Xena release](https://releases.openstack.org/xena/highlights.html)
  - We have also enabled SPICE support in addition to noVNC to
    access the graphical console of VMs.

* The base infrastructure is provided by
  [OSISM 3.0.0](https://github.com/osism/release/blob/main/notes/3.0.0/NOTES.md)
  which in turn build on top of kolla and kolla-ansible.

## New Features (Highlights)

### Operator focused improvements

* The Cluster Management Node is now well prepared to manage numerous
  clusters with independent settings and different feature sets by
  creating default settings and then keeping track of various workload
  clusters in own directories. Documentation has been vastly improved.

* The Cluster Management node now gets its artifacts directly from
  git, making incremental updates to it a lot easier, thus also
  avoiding to disrupt workload clusters through redeployed management
  nodes to roll out updates.

* Added dashboards for the operators:
  - Homer
  - Flower
  - Grafana dashboards

* Work is underway to supersede [openstack-health-monitor](https://github.com/SovereignCloudStack/openstack-health-monitor)
  with a solution that is using tempest and rally. The health-monitor
  has received improvements though and is at this point still fully
  supported and recommended -- it has surfaced a number of issues with
  test clouds, especially failed metadata services.

* User federation has been prepared to be ready for Gaia-X federation integration
  - Keystone can consume users from Keycloak via OpenID-Connect
  - Keycloak uses the highly-available Galera database cluster now
  - mod_oauth2 support for Keystone

* Vast improvements in the SCS Deployment automation
  - Full automation of bare metal deployment with Bifrost and Ironic
  - Using NetBox as central source of truth for the complete setup

* New services available (opt-in)
  - ClamAV, dnsdist, cgit, FRRouting, Nexus, Tang

* Traefik centrally routes the connections to Nexus, NetBox, phpMyAdmin, Homer, Flower, ARA, cgit

### SCS Developer focused improvements (testbed)

We now have scripts that allow us to connect to the workload cluster node network
for debugging purposes.

The configuration of the testbed was minimized and the deployment was made more production-oriented.

Further noteworthy improvements to testbed:
* TLS is implemented throughout the services also in testbed
* Virtual BMC in testbed
* Public DNS for testbed (`testbed.osism.xyz`)

We have a Zuul CI framework running and started migrating CI testing from github actions to
using our Zuul infrastructure.

Renovate is being used to keep the pinned versions up-to-date and consistent across the
many repositories.

An overview over the used software versions is available from the
[OSISM release](https://github.com/osism/release) repository as input
for a complete SBOM. This allows to e.g. investigate the contents of the
used (v3.0.0) images.


## Upgrade/Migration notes

### Cluster Management

The names of a few settings have changed since R1 -- if you have diverged from the defaults,
this may require adjusting the `environment.tfvars` or the `clusterctl.yaml` files.
See [k8s-cluster-api-provider Release Notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/master/Release-Notes-R2.md#incompatible-changes)
for more details.

The updating approach has fundamentally changed:
If you were used to deploy fresh management nodes regularly to
benefit from the upstream improvements, this need has been vastly reduced now,
allowing for long-living management nodes and workload clusters managed by them.

### OSISM

* Playbook generic-configuration.yml was deprecated. From now on, please use the playbook of
the same name in the manager environment (manager-configuration.yml). All configuration
parameters from environments/configuration.yml should be moved to environments/manager/configuration.yml.

* In kolla-ansible the HAProxy role was renamed to loadbalancer. Accordingly, loadbalancer must now be
used for the deployment of HAProxy.

## Removals

* OpenStack Victoria images are no longer built and thus no longer kept updated
* Support for Zabbix has been removed, Prometheus will be used as the only monitoring stack in the future
* Heimdall as a service was removed, as an alternative Homer is now available

## Deprecations

Deprecations happen according to our [deprecation policy](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Release-Policies.md#deprecation).

* Cockpit is deprecated in favor of Boundary by HashiCorp or Teleport
* ceph-ansible is deprecated in preparation for cephadm
* All osism- scripts on the manager are deprecated and will be replaced by the new OSISM CLI. The scripts will be removed in the next release
* The following services are currently not used and are deprecated and scheduled for removal as of now: Falco, Jenkins, Rundeck, Lynis, Trivy
* Heat will no longer be offered by default in the testbed in the future
* The docker-compose CLI will be removed and replaced by the new compose plugin for Docker.
docker-compose is then no longer available and docker compose must be used instead

## Security Fixes

* The Elasticsearch container included in OSISM testbed was exposed to the log4j
  issue -- new images were provided for addressing this. See the
  [security advisory](https://scs.community/de/security/2021/12/13/advisory-log4j/)

## Resolved Issues

* The nginx-ingress loadbalancer could run into name conflicts before.
  The loadbalancer now uses a health monitor to avoid routing to the wrong
  nodes, which typically resulted in 10s delays when connecting to the service
  behind the ingress controller.

* cAdvisor has now reduced number of Prometheus metrics and labels exported by
  default - this will ease the load on the system.
  This implies that corresponding time series data will no longer be created.

## Standards Conformance

The clusters created with our cluster-API cluster management solution pass
the [CNCF conformance tests](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Image-Properties-Spec.md)
as reported by [sonobuoy](https://sonobuoy.io/).

The [OpenStack](https://openstack.org/) layer passes the
[OIF](https://openinfra.dev/) trademark tests, so cloud providers
leveraging the stack should easily be able to achieve the
["OpenStack powered compute"](https://www.openstack.org/brand/interop/)
trademark certification.

Our partner PlusServer has [achieved](https://www.openstack.org/brand/interop/)
a [BSI C5](https://www.bsi.bund.de/EN/Topics/CloudComputing/Compliance_Criteria_Catalogue/Compliance_Criteria_Catalogue_node.html)
security certification for their SCS implementation pluscloud open.

We are working within [Gaia-X](https://gaia-x.eu/) to further the power
of Gaia-X self-descriptions and are closely working with the
[GXFS project](https://gxfs.de/)
to jointly deliver a standard toolbox for Gaia-X conformance
infrastructure and service offerings.

The SCS standards for [flavor naming](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/flavor-naming.md) and
[image metadata](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Image-Properties-Spec.md)
are largely unchanged since R1. We have however
made progress in our reference implementation fully implementing
them without any further tweaks.

## Release Tagging

See [Release Numbering scheme](../Design-Docs/Release-Numbering-Scheme.md) -- unchanged from R0.
We have added the tag `v3.0.0` to the relevant repositories to designate the `SCS_RELEASE_R2`.

Note that we will release R3 (v4.0.0) in September 2022 and stop providing maintenance
updates for R2 at the end of October.

## List of known issues & restrictions in R2

## Future directions (selected Highlights)

Alongside with R2 we published a blog post on some first thoughts on
[future directions towards R3](https://scs.community/tech/2022/03/23/r2-and-future-directions/).

## Contributing

We appreciate contribution to strategy and implementation, please join
our community -- or just leave input on the github issues and PRs.
Have a look at our [contributor guide](https://scs.community/docs/contributor/).
We also have worked on a [Code of Conduct](https://github.com/SovereignCloudStack/Docs/pull/26)
to document the expected behavior of contributors and how we deal with
cases where individuals fail to meet the expectation.
