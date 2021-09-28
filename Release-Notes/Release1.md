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

In a parallel effort to SCS, [StackHPC](https://www.stackhpc.com/) have developed a set of [Helm charts](https://helm.sh) for
deploying Kubernetes clusters on OpenStack using Cluster API. SCS are reviewing the Helm charts as a technical preview with a
view to establishing a closer collaboration with StackHPC going forward.

Helm is a package manager for Kubernetes that is frequently used to share deployment recipes for applications running
on Kubernetes, and these Helm charts apply the same principles to managing infrastructure. The charts define an opinionated
"blueprint" for a Kubernetes cluster and its addons, and a cluster is deployed by specifying one or more YAML files
containing variables for the cluster. Deploying the cluster and all its addons is then a one-line command:

```sh
helm upgrade my-cluster capi/openstack-cluster --install --devel --values clouds.yaml --values cluster.yaml
```

Addons are deployed using [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) executed on the
workload cluster, and use a combination of Helm charts and manifests using [kustomize](https://kubernetes-sigs.github.io/kustomize/).

The Helm charts have the following features:

  * Automatic remediation of unhealthy nodes using `MachineHealthCheck`s
  * Multiple node groups, which can be independently scaled
  * Rolling upgrades by rotating `OpenStackMachineTemplate`s and `KubeadmConfigTemplate`s based on the SHA256 of the `.spec`
  * Ability to customise networking and Kubeadm configuration, including supporting multiple networks
  * Support for several addons
    * Multiple CNIs, defaulting to [Cilium](https://cilium.io/)
    * [OpenStack CCM and Cinder CSI](https://github.com/kubernetes/cloud-provider-openstack)
    * [Metrics server](https://github.com/kubernetes-sigs/metrics-server)
    * [cert-manager](https://cert-manager.io/) with optional [Let's Encrypt](https://letsencrypt.org/) issuer
    * [Nginx ingress controller](https://kubernetes.github.io/ingress-nginx/)
    * Monitoring using the [kube-prometheus stack](https://github.com/prometheus-operator/kube-prometheus)
    * Support for NVIDIA GPUs using the [NVIDIA GPU operator](https://github.com/NVIDIA/gpu-operator)
    * Custom manifests and Helm charts

The charts and documentation are available on GitHub at [stackhpc/capi-helm-charts](https://github.com/stackhpc/capi-helm-charts).

### Beyond CAPI


## Standardization


## SBOM and Links



## Project Updates

### Funding, staffing, tenders

### Community

### Providers

### Gaia-X Hackathons

### IPCEI

