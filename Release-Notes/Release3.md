# Release Notes for SCS Release 3
(Release Date: 2022-09-21)

## Scope

Main goals for Release 3 (R3) were user federation, increase in deployment and upgrade
velocity by improving automated test coverage as well as bringing disk encryption based on
tang from the state of a technical preview to be fully supported.

## Component Versions and User-visible improvements (highlights)

* We support the latest [Kubernetes 1.24](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.24.md)
  releases.
* The Kubernetes Cluster API is now available in a stable v1beta1
  [release 1.1.x](https://github.com/kubernetes-sigs/cluster-api/releases)
  with the corresponding [cluster-api-provider-openstack 0.6.x](https://github.com/kubernetes-sigs/cluster-api/releases).
* The [Kubernetes Cluster API cluster management service]
  (https://github.com/SovereignCloudStack/k8s-cluster-api-provider/)
  has seen major managability improvements.
  Please consult the
  [k8s capi provider release notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/master/Release-Notes-R3.md)
  for more details.
* [OpenStack Yoga release](https://releases.openstack.org/yoga/highlights.html)
* Ceph Quincy is available, the default release of Ceph is still Pacific.

* The base infrastructure is provided by
  [OSISM 4.0.0](https://github.com/osism/release/blob/main/notes/4.0.0/NOTES.md)
  which in turn builds on top of kolla and kolla-ansible.
* Disk encryption based on Network bound disk encryption (NBDE) is available.

## New Features (Highlights)

### Operator focused improvements

* Work is underway to supersede [openstack-health-monitor](https://github.com/SovereignCloudStack/openstack-health-monitor)
  with a comprehensive approach using scenarios with ansible playbooks
  that has been developed and used by T-Systems for their Open Telekom Cloud.
  Meanwhile, openstack-health-monitor has seen the addition of data
  collection with telegraf and influxdb as well as a good dashboard
  with grafana.

* User federation ...

* Gaia-X self-description generator ...

### SCS Developer focused improvements (testbed)

* Container standardization underway ...

* Container cluster updating and upgrading.

* LUKS encryption is now documented and enabled in the testbed by default.

* Further noteworthy improvements to testbed:
  * Public DNS for testbed is now available (`testbed.osism.xyz`), allowing to access services
    via TLS protected by a wildcard CA certificate.
  * The wireguard VPN service is deployed in the testbed by default.

An overview over the used software versions is available from the
[OSISM release](https://github.com/osism/release) repository as input
for a complete SBOM. This allows to e.g. investigate the contents of the
used (v4.0.0) images.


## Upgrade/Migration notes

### Cluster Management

Upgrade from R2 to R3 for cluster management and clusters.

See [k8s-cluster-api-provider Release Notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/master/Release-Notes-R3.md#incompatible-changes)
for more details.

Per cluster application credentials.

### OSISM

* In ``environments/kolla/secrets.yml`` the parameter ``neutron_ssh_key`` must be
  added.

  ```
  neutron_ssh_key:
    private_key:
    public_key:
  ```

  The ssh key can be generated as follows: ``ssh-keygen -t rsa -b 4096 -N "" -f id_rsa.neutron -C "" -m PEM``

## Removals

* The Cockpit service has been removed.
* All osism- scripts on the manager are deprecated and will be replaced by the new OSISM CLI. The scripts will be removed in the next release

## Deprecations

Deprecations happen according to our [deprecation policy](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Release-Policies.md#deprecation).

* Linux bridge support has been deprecated by the Neutron team and marked as experimental.
  If Linux bridge is used in deployments, migrating to OpenVSwitch is recommended.
* Debian dropped hddtemp (https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1002484),
  therefore the ``hddtemp`` service will be removed from the next OSISM release, as there is
  no package available for Ubuntu 22.04.
* Heat will no longer be offered by default in the testbed in the future
* The following services are currently not used and are deprecated and scheduled for removal as of now: Falco, Jenkins, Rundeck, Lynis, Trivy
* The docker-compose CLI will be removed and replaced by the new compose plugin for Docker.
docker-compose is then no longer available and docker compose must be used instead
* The ``cleanup-elasticsearch`` playbook is deprecated. In the future,
  the ``elasticsearch-curator`` service (part of Kolla) has to be used
  for Elasticsearch cleanup.

## Security Fixes


## Resolved Issues

* certificate rotation in k8s clusters

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
to jointly deliver a standard toolbox for Gaia-X compliant
infrastructure and service offerings.

The SCS standards for [flavor naming](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/flavor-naming.md) and
[image metadata](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Image-Properties-Spec.md)
are largely unchanged since R1. We have however
made progress in our reference implementation fully implementing
them without any further tweaks.

## Release Tagging

See [Release Numbering scheme](../Design-Docs/Release-Numbering-Scheme.md) -- unchanged from R0.
We have added the tag `v4.0.0` to the relevant repositories to designate the `SCS_RELEASE_R3`.

Note that we will release R4 (v4.0.0) in March 2023 and stop providing maintenance
updates for R3 at the end of April.

## List of known issues & restrictions in R3

* Distributed Virtual Routing (DVR) is not officially supported by OSISM, not tested and not recommended.

## Future directions (selected Highlights)


## Contributing

We appreciate contribution to strategy and implementation, please join
our community -- or just leave input on the github issues and PRs.
Have a look at our [How to contribute page](https://scs.community/contribute/).

## Thanks

Thanks to our contributors (provide some stats here)
