---
title: Architecture for the Cloud Service provider Observability System for the KaaS Layer
type: Decision Record
status: Draft
track: Ops
---

## Introduction

Cloud Service Providers offer a variety of products to a customer. Those can include compute resources like virtual machines, networking, and identity and access management. As customers of those services build their applications upon those offered services the service provider needs to ensure a certain quality level of their offerings. This is done by observing the infrastructure. Observability systems leverage different types of telemetry data which include:

1. Metrics: Usually time series data about different parameters of a system which can include e.g. CPU usage, number of active requests, health status, etc.
2. Logs: Messages of software events during runtime
3. Traces: A more developer-oriented form of logging to provide insights into an application or to analyze request flows in distributed systems.

Based on those data, an alerting system can be used to send out notifications to an Operations Team if a system behaves abnormally. Based on the telemetry data the Operations Team can find the issue, work on it, and mitigate future incidents.

## Motivation

Currently, only the IaaS Layer of the SCS Reference Implementation has an Observability Stack consisting of tools like Prometheus, Grafana, and Alertmanager as well as several Exporters to extract monitoring data from the several OpenStack components and additional software that is involved in the Reference Implementation. As the Kubernetes as a Service Layer becomes more and more important and the work on the Cluster API approach to create customer clusters progresses further, an observability solution for this layer is also needed. CSP should be able to watch over customer clusters and intervene if a cluster gets in a malfunctioning state. For this, a toolset and architecture are needed which is proposed in this ADR.

## Requirements

A survey was conducted to gather the needs and requirements of a CSP when providing Kubernetes as a Service. The feedback of the survey led to the following requirement on a Kubernetes as a Service Observability System:

- Telemetry Data that MUST be fetched:
    - CPU, RAM, Disk, Network
    - HTTP Connectivity Metrics
    - Control Plane and Pod metrics (States, Ready, etc.)
    - K8s certs metrics
    - Metrics of underlying node
    - Logs of control plane, kubelet and containerd
- Telemetry Data that MAY be fetched:
    - K8s resources (exporters, kubestate metrics, cadvisor, parts of the kubelet)
    - Ingress controller exporter (http error rate, cert metrics like expiration date)
- Telemetry Data that SHOULD NOT BE fetched:
    - Any metrics or logs a CSP does not need to provide support with respect to their SLA with a Customer.
- Telemetry Data that MUST NOT be fetched:
    - Secrets
    - Customer Specific Workload Metrics
- The Alerting Mechanism MUST include a default ruleset 
- The Observability Stack MUST run on the CSP Infrastructure
- The Observability Stack MUST be High Available
- The Observability Stack MUST be able to observe itself
- Observed Clusters SHOULD have a low resource impact on the used software to provide telemetry data for the Observability Stack

### Options considered

#### Use of the dNation Observability Stack as a base

The [dNation monitoring stack](https://github.com/dNationCloud/kubernetes-monitoring) offers a lot of basic capabilities needed on an observability stack for Kubernetes like Prometheus Operator, Grafana, Alertmanager, Loki, Promtail and Thanos.

#### Pull-based Architecture

Each customer cluster has Thanos and Prometheus installed in addition to Thanos and Prometheus on the Observer Cluster. Metrics of a customer cluster are pulled from Thanos (Customer Cluster) for short term queries, as for long term queries the data of all Thanos instances is stored in an external Object Store of the CSP.

#### Push-based Archtitecture

Here, Thanos and Prometheus are only used on the CSP side to store and manage all observability data. For the customer clusters only the Prometheus Agent will be used. Prometheus Agent will push all metrics of a Customer Cluster to the central Thanos instance and is preserved in an external Object Store. This introduces less complexity and resource consumption on the customer workload clusters.

#### Scope of the Observability Architecture

The Observability Cluster and Architecture SHOULD be defined in a modular way so that it can be used to not only observe the Kubernetes Layer of an SCS Stack, but every aspect of an SCS Stack.

#### Observing the Observability Infrastructure

For usage in production, it needs to be possible to observe the Observability Cluster itself.

#### Alerting Rulesets

Use a mix of [kubernetes-mixin alerts](https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/alerts) and [dNation Alerts Ruleset](https://github.com/dNationCloud/kubernetes-monitoring/tree/main/jsonnet/rules), as they offer an extensive and well reviewed set of default Alerts covering the important Parts of a Kubernetes Deployment (Nodes, Controlplane, K8s Resources, etc.)

## Decisions

1. Base the MVP-0 Implementation on the dNation Kubernetes Monitoring Stack.
2. The **Push-based** Architecture was chosen over the Pull-based Approach.
3. The Observability Stack will be created based on the dNation observability stack
4. The Observability Stack can be used as a standalone component to use with the Kubernetes Layer. It should be possible to observe other parts of an SCS Stack like the status of the OpenStack components, but this will not be mandatory.
5. The Observability Stack should be designed that it is possible to provision two observer clusters side by side, observing each other. To do this is only a recommendation for production usage.
6. The MVP-0 will consist of the following features:
    - Observability data from KaaS Clusters is scraped
        - K8s cluster that hosts observer deployment is deployed
        - S3 compatible bucket as a storage for long term metrics is configured
        - thanos query-frontend is deployed and configured
        - thanos query is deployed and configured
        - thanos reciever is deployed and configured (simple deployment, non HA, without router)
        - thanos ruler is deployed and configured
        - thanos compactor is deployed and configured
        - thanos bucket-web is deployed and configured
        - thanos storegateway is deployed and configured
        - prometheus server is deployed and configured
        - prometheus alertmanager is deployed and configured
        - prometheus black-box exporter is deployed and configured
        - kaas-metric-importer is deployed and configured (service aims to differentiate between intentional deletion of KaaS instances and failures in the KaaS monitoring agent)
    - Alerts are defined on the KaaS Clusters metrics
        - all prometheus alerts are working as expected
    - There exist Dashboards for KaaS Cluster Health
        - KaaS L0 dashboard counters are working correctly
        - Dedicated L0 dashboards are deployed for KaaS and for IaaS monitoring layers
    - There exist Dashboards for SCS services endpoinds health (BlackBox exporter)
    - There exist Dashboards for IaaS layer health
    - Automatic Setup of Exporters for Observability of managed K8s clusters
        - KaaS service is mocked
        - VM that will host a mock of KaaS service is deployed
        - a script that deploys a multiple KinD clusters and register them in observer is created
    - Automatic Setup of Thanos sidecar for Observability of IaaS layer (testbed)
        - IaaS service is mocked
        - OSISM testbed is deployed
        - implement an option to deploy thanos sidecar with some simple config in OSISM testbed
    - There exist Dashboards for Harbor Registry Health
    - Alerts are defined on the Harbor Registry metrics

## Reference

### Outcome of the CSP Survey about Requirements for KaaS Observability

A survey was conducted to gather the needs and requirements of a CSP when providing Kubernetes as a Service. The results of the Survey (Questions with answers) were the following:

1. What is your understanding of a managed Kubernetes Offering:
    - Hassle-Free Installation and Maintainance (customer viewpoint); Providing Controlplane and worker nodes and responsibility for correct function but agnostic to workload
    - Day0, 1 and 2 (~planning, provisioning, operations) full lifecyle management or let customer manages some parts of that, depending on customer contract

2. What Type and Depth of observability is needed
    - CPU, RAM, HDD and Network usage, Health and Function of Cluster Nodes, Controlplane and if desired Customer Workload

3. Do you have an observabiltiy infrastructure, if yes, how it is built
    - Grafana/Thanos/Prometheus/Loki/Promtail/Alertmanger Stack, i.e. [Example Infrastructure](https://raw.githubusercontent.com/dNationCloud/kubernetes-monitoring-stack/main/thanos-deployment-architecture.svg)

4. Data Must haves
    - CPU, RAM, Disk, Network
    - HTTP Connectivity Metrics
    - Control Plane and Pod metrics (States, Ready, etc.)
    - Workload specific metrics
    - Node Stats
    - K8s resources (exporters, kubestate metrics, cadvisor, parts of the kubelet)
    - Ingress controller exporter (http error rate, cert metrics like expiration date)
    - K8s certs metrics
    - Metrics of underlying node
    - Logs of control plane, kubelet and containerd

5. Must Not haves
    - Secrets, otherwise as much as possible for anomaly detection over long time data

6. Must have Alerts
    - Dependent on SLAs and SLA Types, highly individual
    - Use of [kubernetes-mixin alerts](https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/alerts) and [dNation Alerts Ruleset](https://github.com/dNationCloud/kubernetes-monitoring/tree/main/jsonnet/rules)

7. Must NOT Alert on
    - Should not wake people, nothing that does not lead to Action items

8. Observability from Within Or Outside KaaS. How does the architecture look like?
    - Monitoring Infra on CSP Side
    - Data from Customer Clusters and Mon Infra on CSP and KaaS, get both data. KaaS Monitoring can also be used by customer

9. Special Constraints
    - HA Setup in different Clusters on Different Sites
