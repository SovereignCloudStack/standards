---
title: Kubernetes Logging/Monitoring/Tracing
type: Decision Record
status: Draft
track: KaaS
---

## Motivation

Either as an administrator or as a customer of a Kubernetes cluster, at some point you will need to debug useful information.
In order to obtain this information, mechanisms SHOULD be available to retrieve this information.
These mechanisms consist of:
* Logging
* Monitoring
* Tracing

The aim of this decision record  is to examine how Kubernetes handles thoes mechanisms.
Derived from this, this decision record provides a suggestion on how a Kubernetes cluster SHOULD be configured in order to provide meaningful and comprehensible information via logging, monitoring and tracing.



## Decision




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
