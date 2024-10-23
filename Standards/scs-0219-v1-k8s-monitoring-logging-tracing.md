---
title: Kubernetes Logging/Monitoring/Tracing
type: Decision Record
status: Draft
track: KaaS
---


## Motivation

Either as an operators or as an end users of a Kubernetes cluster, at some point you will need to debug useful information.
In order to obtain this information, mechanisms SHOULD be available to retrieve this information.
These mechanisms consist of:
* Logging
* Monitoring
* Tracing

The aim of this decision record is to examine how Kubernetes handles thoes mechanisms.
Derived from this, this decision record provides a suggestion on how a Kubernetes cluster SHOULD be configured in order to provide meaningful and comprehensible information via logging, monitoring and tracing.


## Decision

A Kubernetes cluster MUST provide both monitoring and logging. 
In addition, a Kubernetes cluster MAY provide traceability mechanisms, as this is important for time-based troubleshooting. 
Therefore, a standardized concept for the setup of the overall mechanisms as well as the resources to be consumed MUST be defined.

This concept SHALL define monitoring and logging in a federated structure.
Therefore, a monitoring and logging stack MUST be deployed on each k8s cluster. 
A central monitoring can then fetch data from the clusters individual monitoring stacks.


### Monitoring

> see: [Metrics For Kubernetes System Components][system-metrics]
> see: [Metrics for Kubernetes Object States][kube-state-metrics]


SCS KaaS infrastructure monitoring SHOULD be used as a diagnostic tool to alert operators and end users to system-related issues by analyzing metrics.
Therefore, it includes the collection and visualization of the corresponding metrics.
Optionally, an alerting mechanism COULD also be standardized.
This SHOULD contain a minimal set of important metrics that signal problematic conditions of a cluster in any case. 

> TODO: Describe one examples here in more detail


#### Kubernetes Metric Server 

Kubernetes provides a source for container resource metrics. 
The main purpose of this source is to be used for Kubernetes' built-in auto-scaling [kubernetes-metrics-server][kubernetes-metrics-server-repo].
However, it could also be used as a source of metrics for monitoring. 
Therefore, this metrics server MUST also be readily accessible for the monitoring setup.

Furthermore, end users rely on certain metrics to debug their applications.
More specifically, an end user wants to have access to all metrics defined by Kubernetes itself.
The content of the metrics to be provided by the [kubernetes-metrics-server][kubernetes-metrics-server-repo] are bound to a Kubernetes version and are organized according to the [kubernetes metrics lifecycle][system-metrics_metric-lifecycle]).

In order for an end user to be sure that these metrics are accessible, a cluster MUST provide the metrics in the respective version.


#### Prometheus Operator

One of the most commonly used monitoring tools in connection with Kubernetes is Prometheus
Therefore, every k8s cluster CLOUD have a [prometheus-operator][prometheus-operator] deployed to all control plane clusters as an optional default.
The operator SHOULD at least be rolled out to all control plane nodes.


#### Security

Communication between the Prometheus services (expoter, database, federation, etc.) SHOULD be accomplished using "[mutual][mutual-auth] TLS" (mTLS).

### Logging

In Kubernetes clusters, log data is not persistent and is discarded after a container is stopped or destroyed.
This makes it difficult to debug crashed pods of a deployment after they have been destroyed.
Therefore, the SCS stack SHOULD also optionally provide a logging stack that solves this problem by storing the log file in a self-managed database beyond the lifetime of a container.

> see: [Logging Architecture][k8s-logging]

### Tracing

> see: [Traces For Kubernetes System Components][system-traces]



[k8s-debug]: https://kubernetes.io/docs/tasks/debug/
[prometheus-operator]: https://github.com/prometheus-operator/prometheus-operator
[k8s-metrics]: https://github.com/kubernetes/metrics
[system-metrics]: https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/
[system-metrics_metric-lifecycle]: https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/#metric-lifecycle
[kube-state-metrics]: https://kubernetes.io/docs/concepts/cluster-administration/kube-state-metrics/
[k8s-deprecating-a-metric]: https://kubernetes.io/docs/reference/using-api/deprecation-policy/#deprecating-a-metric
[k8s-show-hidden-metrics]: https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/#show-hidden-metrics
[system-traces]: https://kubernetes.io/docs/concepts/cluster-administration/system-traces/
[system-logs]: https://kubernetes.io/docs/concepts/cluster-administration/system-logs/
[monitor-node-health]: https://kubernetes.io/docs/tasks/debug/debug-cluster/monitor-node-health/
[k8s-logging]: https://kubernetes.io/docs/concepts/cluster-administration/logging/
[mutual-auth]: https://en.wikipedia.org/wiki/Mutual_authentication
