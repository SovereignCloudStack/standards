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


## Metrics collection and dashboards

### Prometheus exporters and Grafana dashboards

We provide generic configuration examples and blueprints for prometheus rules and grafana dashboards. The examples need to be understood and adapted to the particular needs of your environment. You can find the examples at <https://github.com/osism/kolla-operations>. 

With R2 we plan to implement a basic set of these alerts and dashboards in the testbed deployment in order to make them even easier consumable for new users. Feel free to give feedback on the examples and contribute your own generic examples. 

We're working on bringing a basic set of prometheus exporters to the OpenStack-kolla upstream community. 

As part of our effort to add further monitoring tooling, we're integrating further prometheus exporters such as libvirt ([https://review.opendev.org/c/openstack/kolla-ansible/i+/643568](https://review.opendev.org/c/openstack/kolla-ansible/+/643568)) and ovn (<https://review.opendev.org/c/openstack/kolla/+/762986>). Integration is targeted for R2.

### openstack-health-monitor

### ...

## Logging

### Central logging

OSISM now enables kolla-ansible centralized logging by default. The default rules need to be further refined to suit your needs. We plan to implement a more generic set of rules for R2.

## Federation

### OIDC support via keycloak

### non-TLS restrictions (testbed)

### Logout


## Bare Metal Service


## Container Layer 

### Overview and Goals for R1

### k8s capi update

### Application Credential

### Management scripts

### Features

### Helm templates (technical preview)

### Beyond CAPI


## Standardization


## SBOM and Links



## Project Updates

### Funding, staffing, tenders

### Community

### Providers

### Gaia-X Hackathons

### IPCEI

