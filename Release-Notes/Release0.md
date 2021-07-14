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
Patchman, phpMyAdmin, Elasticsearch (b/f license change), Kibana

Validation: Rally, Refstack

Infrastructure: Linux, KVM, ceph, OVN, MariaDB, RabbitMQ, Redis

IAM: LDAP, Keycloak

IaaS (OpenStack): keystone, nova, glance, cinder, neutron, octavia, horizon

Optional OpenStack services: designate, heat, gnocchi, ceilometer, aodh, panko,
barbican, magnum

TODO: Add link to full SBOM here.

## Known Bugs

## Technical Previews

While already in productive use (on bare metal) by two providers, the bare metal
setup currently has a few more manual steps than we would like. This will improve
with the next releases.

We have worked hard on supporting identity federation (OIDC and SAML) during the last
few months. We have also spent significant effort on getting the k8s stack with
k8s cluster API into a good shape. However, we have determined that we do not
yet consider those two key pieces as production-ready. The goal is to change that
for R1 (see below).

Containers: K8s aaS with k8s cluster API: https://github.com/SovereignCloudStack/k8s-cluster-api-provider

For now, you can use the software to see where SCS is going and test our technical
preview code. We really appreciate feedback we get on these pieces as well.
However keep in mind that we do not guarantee to ship technical previews from
Release n as production ready software in one of the next releases. We certainly
hope to do so.

## Updates

TODO: make patch

## Bug reporting

See [main README](../README.md) file.
