# Release Notes for SCS Release 2
(Release Date: 2022-03-XX)

## Scope

Main goals for Release 2 (R2) was ...

## Component Versions and User-visible improvements (highlights)

* Kubernetes 1.22.7/1.23.4
* Kubernetes Cluster API 1.0.5
* OpenStack Xena
  - SPICE support in addition to noVNC

* ...


* [OSISM 3.0.0](https://github.com/osism/release/blob/main/notes/3.0.0/NOTES.md)

## New Features (Highlights)

### Operator focused improvments

* Added dashboards for the operators:
  - Homer
  - Flower
  - Grafana dashboards

  - 
* User federation has been prepared to be ready for Gaia-X federation integration
  - Keystone can consume users from Keycloak via OpenID-Connect
  - Keycloak uses the highly-available Galera database cluster now
  - mod_oauth2 support for Keystone

* Vast improvements in the SCS Deployment automation 
  - Full automation of bare metal deployment with Bifrost and Ironic
  - Using Netbox as central source of truth for the complete setup

* New services available (opt-in)
  - ClamAV, DnsDist, Cgit, FRRouting, Nexus, Tang

* Traefik centrally routes the connections to Nexus, Netbox, Phpmyadmin, Homer, Flower, ARA, Cgit

### SCS Developer focused improvements (testbed)

The configuration of the testbed was minimized and the deployment was made more production-oriented.

Further wnoteworthy improvements to testbed:
* TLS in testbed
* Virtual BMC in testbed
* Public DNS for testbed (`testbed.osism.xyz`)

We have a Zuul CI framework running and started migrating CI testing from github actions to
using our zuul infrastructure.

Renovate is being used to keep the pinned versions up-to-date and consistent across the
many repositories.

An overview over the used software versions is available from the
[OSISM release](https://github.com/osism/release) repository as input
for a complete SBOM. This allows to e.g. investigate the contents of the
used (v3.0.0) images.


## Upgrade/Migration notes

## Removals

* OpenStack Victoria images are no longer built and thus no longer kept updated
* Support for Zabbix has been removed, Prometheus will be used as the only monitoring stack in the future
* Heimdall as a service was removed, as an alternative Homer is now available

## Deprecations

* Cockpit is deprecated in favor of Boundary by HashiCorp or Teleport
* ceph-ansible is deprecated in preparation for cephadm
* All osism- scripts on the manager are deprecated and will be replaced by the new OSISM CLI. The scripts will be removed in the next release
* The following services are currently not used and are deprecated and scheduled for removal as of now: Falco, Jenkins, Rundeck, Lynis, Trivy
* Heat will no longer be offered by default in the testbed in the future
* The docker-compose CLI will be removed and replaced by the new compose plugin for Docker.
docker-compose is then no longer available and docker compose must be used instead

## Security Fixes

## Resolved Issues

* cAdvisor has now reduced number of Prometheus metrics and labels exported by 
default - this will ease the load on the system.
This implies that corresponding timeseries data will no longer be created.

## Conformance

## Release Tagging

See [Release Numbering scheme](../Design-Docs/Release-Numbering-Scheme.md) -- unchanged from R0.
We have added the tag `v3.0.0` to the relevant repositories to designate the `SCS_RELEASE_R2`.

## List of known issues & restrictions in R2
