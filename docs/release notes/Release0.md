# Release Notes for SCS Release 0

(Release Date: 2021-07-15)

## Scope

The main focus of R0 is to demonstrate the viability of our approach to a much broader
audience by providing a well-documented testbed. This will allow anyone interested
to study the system in real-life, test, contribute, compare, ... it.

Also we learn performing the release process.

## Features

Fully automated virtual (testbed setup) with ansible (terraform bootstrap to create
storage, networking and VM resources for bootstrapping via cloud-init injected
scripts that call ansible).)

The infrastructure, management and openstack services are all deployed in containers.

Included tools for Operations: ARA, Netbox, Cockpit, Netdata, Skydive (opt-in),
Patchman, phpMyAdmin, Elasticsearch (b/f license change), Kibana, Grafana, influxdb

Validation: Rally, Refstack

Infrastructure: Linux, KVM, ceph (pacific), OpenVSwitch, OVN, MariaDB, RabbitMQ, Redis,
Etcd, HAproxy, Keepalived, Memcached, Keycloak

IaaS (OpenStack - Wallaby): keystone, nova, glance, cinder, neutron, octavia, horizon

Optional OpenStack services: designate, heat, gnocchi, ceilometer, aodh, panko, senlin,
barbican, manila, magnum

See [testbed SBOM](https://docs.osism.de/testbed/overview.html#software-bill-of-materials-sbom) for
a complete list. The exact versions of the contained components can be retrieved from the
[release repo](https://github.com/osism/release/tree/master/1.0.0) of OSISM.

## Get SCS

See [main README](/docs/intro.md).

## Known Bugs

Nothing major known yet.

## Technical Previews

While already in productive use (on bare metal) by two providers, the bare metal
setup currently has a few more manual steps than we would like. This will improve
with the next releases.

We have worked hard on supporting identity federation (OIDC and SAML) during the last
few months. We have also spent significant effort on getting the k8s stack with
k8s cluster API into a good shape. However, we have determined that we do not
yet consider those two key pieces as production-ready. The goal is to change that
for R1 (see below).

For now, you can use the software to see where SCS is going and test our technical
preview code. We really appreciate feedback we get on these pieces as well.
However keep in mind that we do not guarantee to ship technical previews from
a Release as production-ready software in one of the next releases. We certainly
hope to do so.

To test how our k8s aaS platform will look like, have a look at
<https://github.com/SovereignCloudStack/k8s-cluster-api-provider>
You can follow the documentation to set up the k8s cluster API on an SCS
cloud (or other well configured OpenStack clouds that support octavia).

The [openstack-health-monitor](https://github.com/SovereignCloudStack/openstack-health-monitor)
is used by us to monitor that the API works and successfully creates working resources
in finite time. We plan to integrate it with a dashboard and an alarming mechanism in
the next releases.

## Release tagging

See [Release Numbering scheme](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Release-Numbering-Scheme.md).
The containers have version number v1.0.0 for R0.

## Updates

Updating the software can conveniently be done from the manager node by running the
ansible playbooks again. Details are in the
[OSISM testbed documentation](https://docs.osism.tech/testbed/usage.html#update-services).

## Bug reporting

See [main README](/docs/intro.md) file.
