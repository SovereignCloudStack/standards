---
title: Robustness features for K8s clusters
type: Standard
status: Draft
track: KaaS
---

## Introduction

Kubernetes clusters in a productive environment are under the assumption to always perform perfectly without any major
interruptions. But due to external or unforeseen influences, clusters can be disrupted in their normal workflow, which
could lead to slow responsiveness or even malfunctions.
In order to possibly mitigate some problems for the Kubernetes clusters, robustness features should be introduced into
the SCS standards. These would harden the cluster infrastructure against several problems, making failures less likely.

### Glossary

The following special terms are used throughout this standard document:

| Term                        | Meaning                                                        |
|-----------------------------|----------------------------------------------------------------|
| Certificate Authority       | Trusted organization that issues digital certificates entities |
| Certificate Signing Request | Request in order to apply for a digital identity certificate   |

## Motivation

A typical productive Kubernetes cluster could be hardened in many different ways, whereas probably many of these actions
would overlap and target similar weaknesses of a cluster.
For this version of the standard, the following points should be addressed:

* Kube-API rate limiting
* etcd compaction/defragmentation
* etcd backup
* Certificate Authority (CA) expiration avoidance

These robustness features should mainly increase the up-time of the Kubernetes cluster by avoiding downtimes either
because of internal problems or external threads like "Denial of Service" attacks.
Additionally, the etcd database should be strengthened with these features in order to provide a secure and robust
backend for the Kubernetes cluster.

## Design Considerations

In order to provide a conclusive standard, some design considerations need to be set beforehand:

### Kube-API rate limiting

Rate limiting is the practice of preventing too many requests to the same server in some time frame. This can help prevent
service interruptions due to congestion and therefore slow responsiveness or even service shutdown.
Kubernetes suggests multiple ways to integrate such a Ratelimit for its API server, a few of which will be mentioned here.
In order to provide a useful Ratelimit for the Kubernetes cluster, combination of these methods should be considered.

#### API server flags

The Kubernetes API server has some flags available to limit the amount of incoming requests that will be accepted by
the server, which should prevent crashing of the API server. This nevertheless shouldn't be the only measure to
introduce a rate limit, since important requests could get blocked during high traffic periods (at least according to
the official documentation).
The following controls are available to tune the server:

* max-requests-inflight
* max-mutating-requests-inflight
* min-request-timeout

More details can be found in the following documents:
[Flow Control](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)

#### Ratelimit Admission Controller

From version 1.13 onwards, Kubernetes includes a EventRateLimit Admission Controller, which aims to mitigate Ratelimit
problems associated with the API server by providing limits for requests every second either to specific resources or
even the whole API server. If requests are denied due to this Admission Controller, they're either cached or denied
completely and need to be retried; this also depends on the EventRateLimit configuration.
More details can be found in the following documents:
[Rancher rate limiting](https://rke.docs.rancher.com/config-options/rate-limiting)
[EventRateLimit](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#eventratelimit)
It is important to note, that this only helps the API server against event overloads and not necessarily the network
in front of it, which could still be overwhelmed.

#### Flow control

Flow control for the Kubernetes API server can be provided by the API priority and fairness feature, which classifies
and isolates requests in a fine-grained way in order to prevent an overload of the API server.
The package introduces queues in order to not deny requests and dequeue them through Fair Queueing techniques.
Overall, the Flow control package introduces many different features like request queues, rule-based flow control,
different priority levels and rate limit maximums.
The concept documentation offers a more in-depth explanation of the feature:
[Flow Control](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)

### etcd maintenance

etcd is a strongly consistent, distributed key-value store that provides a reliable way to store data that needs to be
accessed by a distributed system or cluster of machines. For these reasons, etcd was chosen as the default database
for Kubernetes.
In order to remain reliable, an etcd cluster needs periodic maintenance. This is necessary to maintain the etcd keyspace;
failure to do so could lead to a cluster-wide alarm, which would put the cluster into a limited-operation mode.
To mitigate this scenario, the etcd keyspace can be compacted. Additionally, an etcd cluster can be defragmented, which
gives back disk space to the underlying file system and can help bring the cluster back into an operable state, if it
ran out of space earlier.

etcd keyspace maintenance can be achieved by providing the necessary flags/parameters to etcd, either via the KubeadmControlPlane or in the
configuration file of the etcd cluster, if it is managed independent of the Kubernetes cluster.
Possible flags, that can be set for this feature, are:

* auto-compaction-mode
* auto-compaction-retention

More information about compaction can be found in the respective etcd documentation
[etcd maintenance](https://etcd.io/docs/v3.3/op-guide/maintenance/)

### etcd backup

An etcd cluster should be regularly backed up in order to be able to restore the cluster to a known good state at an
earlier space in time if a failure or incorrect state happens.
The cluster should be backed up multiple times in order to have different possible states to go back to. This is especially
useful, if data in the newer backups was already corrupted in some way or important data was deleted in them.
For this reason, a backup strategy needs to be developed with a decreasing number of backups in an increasing period of time,
meaning that the previous year should only have 1 backup, but the current week should have multiple.
Information about the backup process can be found in the etcd documentation:
[Upgrade etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)

### Certificate rotation

In order to secure the communication of a Kubernetes cluster, (TLS) certificates signed by a controlled
Certificate Authority (CA) can be used.
Normally, these certificates expire after a set period of time. In order to avoid expiration and failure of a cluster,
these certificates need to be rotated regularly and at best automatically.
It is important to either set `--rotate-server-certificates` as a command line parameter or set `rotateCertificates: true`
in the kubelet config or the `kubeletExtraArgs` of the cluster-template.yaml file. This activates the rotation of the
kubelet server certificate. Another recommendation is to set `serverTLSBootstrap: true`, which also enables the request
and rotation of the certificate for the kubelet by requesting them from `certificates.k8s.io`
according to the documentation under [Kubeadm certs].

A clusters certificates can be rotated by updating the cluster, which according to the Kubernetes documentation
automatically renews the certificates.
Another method would be the manual renewal, which can be done through multiple methods, depending on the K8s cluster
used. An example for a K8s cluster set up with `kubeadm` would be to execute the command

```bash
kubeadm certs renew all
```

Since clusters conformant with the SCS standards would probably be updated within the time period described in the
standard [SCS-0210-v2](https://github.com/SovereignCloudStack/standards/tree/main/Standards/scs-0210-v2-k8s-version-policy.md),
this rotation can probably be assumed to happen, because of the cluster update functionality.

It is also important to mention, that CSRs may need to be approved manually with the commands

```bash
kubectl get csr
kubectl certificate approve <CSR>
```

in order to complete a certificate rotation. This is most likely dependent on the K8s cluster solution in use.
`kubectl get csr` allows to check, if this is the case; a `Pending` CSR would need to be approved.

```bash
NAME        AGE     SIGNERNAME                        REQUESTOR                      CONDITION
csr-9wvgt   112s    kubernetes.io/kubelet-serving     system:node:worker-1           Pending
```

Another option to approve the CSRs would be to use a third-party controller that automates the process. One example for
this would be the [kubelet csr approver](https://github.com/postfinance/kubelet-csr-approver), which can be deployed on
a K8s cluster and requires `serverTLSBootstrap` to be set to true. Other controllers with a similar functionality might
have other specific requirements, which won't be explored in this document.

Another problem is that the CA might expire. Unfortunately, not all K8s tools have functionality to renew these
certificates with the help of commands. Instead, there is documentation for manually rotating the CA, which can be found
under [Manual rotation of ca certificate](https://kubernetes.io/docs/tasks/tls/manual-rotation-of-ca-certificates/).

Further information and examples can be found in the Kubernetes documentation:
[Kubeadm certs](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
[Kubelete TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)

## Decision

Robustness features combine multiple aspects of increasing the security, hardness and
longevity of a Kubernetes cluster. The decisions will be separated into their respective
areas.

### Kube-API rate limiting

The number of requests send to the kube-api or Kubernetes API server MUST be limited
in order to protect the server against outages, deceleration or malfunctions due to an
overload of requests.
In order to do so, at least the following parameters MUST be set on a Kubernetes cluster:

* max-requests-inflight
* max-mutating-requests-inflight
* min-request-timeout

Values for these flags/parameters SHOULD be adapted to the needs of the environment and
the expected load.

A cluster MUST also activate and configure a Ratelimit admission controller.
This requires an `EventRateLimit` resource to be deployed on the Kubernetes cluster.
The following settings are RECOMMENDED for a cluster-wide deployment, but more
fine-grained rate limiting can also be applied, if this is necessary.

```yaml
kind: Configuration
apiVersion: eventratelimit.admission.k8s.io/v1alpha1
limits:
- burst: 20000
  qps: 5000
  type: Server
```

It is also RECOMMENDED to activate the Kubernetes API priority and fairness feature,
which also uses the aforementioned cluster parameters to better queue, schedule and
prioritize incoming requests.

### etcd compaction

etcd MUST be cleaned up regularly, so that it functions correctly and doesn't take
up too much space, which happens because of its increase of the keyspace.

To compact the etcd keyspace, the following flags/parameters MUST be set for etcd:

* auto-compaction-mode = periodic
* auto-compaction-retention = 8h

### etcd backup

An etcd cluster MUST be backed up regularly. It is RECOMMENDED to adapt
a strategy of decreasing backups over longer time periods, e.g. keeping snapshots every
10 minutes for the last 120 minutes, then one hourly for 1 day, then one daily for 2 weeks,
then one weekly for 3 months, then one monthly for 2 years, and after that a yearly backup.
At the very least, a backup MUST be done once a week.
These numbers can be adapted to the security setup and concerns like storage or network
usage. It is also RECOMMENDED to encrypt the backups in order to secure them further.
How this is done is up to the operator.

### Certificate rotation

It should be avoided, that certificates expire either on the whole cluster or for single components.
To avoid this scenario, certificates MUST be rotated regularly; in the
case of SCS, we REQUIRE at least a yearly certificate rotation.
To achieve a complete certificate rotation, the parameters `serverTLSBootstrap` and `rotateCertificates`
MUST be set in the kubelet configuration.

The certificates can be rotated by either updating the Kubernetes cluster, which automatically
renews certificates, or by manually renewing them. How this is done is dependent on the used K8s cluster.

It is also RECOMMENDED to renew the CA regularly to avoid an expiration of the CA.
This standard doesn't set an exact timeline for a renewal, since it is dependent on lifetime and
therefore expiration date of the CA in question.

## Related Documents

[Flow Control](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)
[Rate limiting](https://rke.docs.rancher.com/config-options/rate-limiting)
[EventRateLimit](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#eventratelimit)
[etcd maintenance](https://etcd.io/docs/v3.3/op-guide/maintenance/)
[Upgrade etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
[Kubeadm certs](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
[Kubelet TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)

## Conformance Tests

Conformance Tests, OPTIONAL
