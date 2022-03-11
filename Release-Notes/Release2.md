# Release Notes for SCS Release 2
(Release Date: 2022-03-XX)

## Scope

Main goals for Release 2 (R2) was ...

## Component Versions

* Kubernetes 1.22.2
* Kubernetes Cluster API 1.0.0
* ...

## New Features (highlights)

* The monitoring stack as been extended to include a set of default dashboards for grafana.

## Upgrade/Migration notes

## Removals

## Deprecations

## Security Fixes

## Resolved Issues

* cAdvisor has now reduced number of Prometheus metrics and labels exported by 
default - this will ease the load on the system.
This implies that corresponding timeseries data will no longer be created.

## Release Tagging

See [Release Numbering scheme](../Design-Docs/Release-Numbering-Scheme.md) -- unchanged from R0.
We have added the tag `v3.0.0` to the relevant repositories to designate the `SCS_RELEASE_R2`.

## List of known issues & restrictions in R2
