# Release Notes for SCS Release 3
(Release Date: 2022-09-21)

## Scope

Main goals for Release 3 (R3) were user federation, increase in deployment and upgrade
velocity by improving automated test coverage as well as bringing disk encryption based on
tang from the state of a technical preview to be fully supported.

## Component Versions and User-visible improvements (highlights)

* We support the latest [Kubernetes 1.25](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.25.md)
  releases.
* The Kubernetes Cluster API is now available in a stable v1beta1
  [release 1.2.x](https://github.com/kubernetes-sigs/cluster-api/releases)
  with the corresponding [cluster-api-provider-openstack 0.6.x](https://github.com/kubernetes-sigs/cluster-api/releases).
* The [Kubernetes Cluster API cluster management service](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/)
  has seen major managability improvements.
  Please consult the
  [k8s cluster api provider release notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/Release-Notes-R3.md)
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

* We have used our keystone to keycloak federation to use keycloak as identity
  broker to federate identities from other (SCS) clouds' keycloaks.
  This works well for the Web-Interface; we have still some work to do to also make it smooth
  also for API/CLI usage. We have [documented the current status](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/IAM-federation/keystone-keycloak-federation.md)

* We believe that Gaia-X self-descriptions should also contain a description of
  technical properties of services; higher-level services and workloads can than
  declare their requirements and be matched against lower level services / platforms.
  In good platforms, most (or all) technical properties are discoverable. In the
  Gaia-X Hackathon #4, we have worked on a demonstrator that characterizes some
  aspects of an OpenStack-based IaaS platform and which produces self-descriptions
  that can be submitted to the Gaia-X trust service, pass the tests and you can
  be awared a verifiable credential. Code is available in the
  [gx-self-description-generator repo](https://github.com/SovereignCloudStack/gx-self-description-generator)

### SCS Developer focused improvements (testbed and k8s cluster management)

* Following significant discussions on how to standardize our cluster management solution,
  there is a draft concept as part of R3 now, which will be further worked on during
  the R4 cycle. See [Cluster standardization](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/Release-Notes-R3.md#cluster-standardization)
  section of the release notes from k8s-cluster-api-provider.
  While our reference implementation uses the concepts and code from k8s cluster API on
  top of our SCS reference implementation (OpenStack automated by OSISM), we want to
  assure that non-OpenStack IaaS and solutions that diverge from cluster-API have the possibility
  to be SCS compliant.

* Workload clusters managed by our SCS cluster management solutions can now much
  more easily receive k8s version upgrades, [as the cluster-template no longer needs
  to be touched for this](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/Release-Notes-R3.md#simplified-rolling-node-upgrades-223). There is an [Upgrade Guide](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/doc/Upgrade-Guide.md) available now.

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

Upgrade from R2 to R3 for cluster management and clusters:
See [k8s-cluster-api-provider Release Notes](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/Release-Notes-R3.md#incompatible-changes)
for more details. There is an Upgrade Guide written specifically to address the steps needed for upgrading
your cluster management and the workload clusters.

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

* Certificates in k8s clusters are subject to expiration - typically after one year.
  We ensure these are renewed on control-plane upgrades, but operators may need manual attention
  in case upgrades are not performed for extended periods of time. This is documented in
  the k8s-cluster-api-provider's
  [Maintenance and Troubleshooting Guide](certificate rotation in k8s cluster://github.com/SovereignCloudStack/k8s-cluster-api-provider/blob/main/doc/Maintenance_and_Troubleshooting.md).

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
them without any further tweaks. The
[conformance test for the flavor naming](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/tools/flavor-name-check.py)
has seen minor improvements; a
[conformance test for the image metadata](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/tools/image-md-check.py)
has been added.

## Release Tagging

See [Release Numbering scheme](../Design-Docs/Release-Numbering-Scheme.md) -- unchanged from R0.
We have added the tag `v4.0.0` to the relevant repositories to designate the `SCS_RELEASE_R3`.

Note that we will release R4 (v5.0.0) in March 2023 and stop providing maintenance
updates for R3 at the end of April 2023.

## List of known issues & restrictions in R3

* Distributed Virtual Routing (DVR) is not officially supported by OSISM, not tested and not recommended.

## Contributing

We appreciate contribution to strategy and implementation, please join
our community -- or just leave input on the github issues and PRs.
Have a look at our [How to contribute page](https://scs.community/contribute/).

## Thanks

The work for R3 has been done by many contributors from our community.
We have not collected detailed stats that would split out the individual contributor's
and companies shares ... we may do so in the future. We are grateful to have such an
active and engaged community that has done so much work! Thanks to our contributors!

Of course we are leveraging a huge amount of open source technology that has been
created by our friends in other communities, many of which are part of the
CNCF, Linux Foudation, OIF, and others. We participate and contribute where
we can and definitely want to acknowledge the great work that we build upon.

