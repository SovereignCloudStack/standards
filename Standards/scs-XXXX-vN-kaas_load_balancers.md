---
title: Behavior of KaaS load balancers
type: Standard
status: Draft
track: KaaS
---

# Introduction

Kubernetes `Services` with [`type: LoadBalancer`](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer) provide an abstraction to configure load balancers which are usually provided by the cloud.

The "cloud" (respectively the cloud controller manager) is responsible to implement this.

In effect, when a user creates such `Service` on any cloud provider, there are generally no provider specific parameters required, even though implementation might vary significantly from one provider to another.

That being said, there are some parameters with default values which may be overridden, introducing some sort of implementation details which affect cross-provider-support.

This standard record is intended to clarify: What exact configurations and use cases can be expected to work out of the box on a SCS compliant cloud?

# Motivation / desirable features

## `externalTrafficPolicy: Local`

By default `externalTrafficPolicy` is set to `Cluster`. Changing it to `Local` does address some problems of the default `Cluster` setting, but to have its full effect, it also requires the underlaying load balancers and cluster setups to work a bit more opinionated.

### Benefits

* <a name="keepip"></a>Preserving the actual client/source IP for backing Pods. [K8s Docs](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip).
  * Kubernetes nodes stop doing SNAT, so they do not obfuscate the IP anymore
* <a name="ootb"></a>Being the default setting for e.g. [nginx's nginx-ingress-controller helm chart](https://docs.nginx.com/nginx-ingress-controller/installation/installation-with-helm/#configuration), supporting this will make such helm charts work out of the box
* <a name="performance"></a> Improve performance
  * Connections will not hop across nodes, so performance should be improved

### Drawbacks / Neutralized benefits / Countering arguments

* In the SCS reference implementation, some default setting of the OpenStack cloud controller needs to be changed in order to prevent constant connectivity issues.
  * Regards load balancer health checks
  * Reasoning behind default setting is still unknown, so there may be some unconsidered edge cases
* [Preserving the actual client/source IP for backing Pods](#keepip)
  * This only really is a benefit if the nodes see the actual client/source IP themselves - for example when the load balancer is implemented as a low level packet forwarder ([K8s docs](https://kubernetes.io/docs/tutorials/services/source-ip/#cross-platform-support)). In the OpenStack Octavia case, which seems to include an HAProxy (terminating TCP) operating on a higher level, setting `externalTrafficPolicy: Local` would only make the HAProxy IP visible. In effect, setting it in this case would not really help preserving client IPs.
  * So, handling `externalTrafficPolicy: Local` as "supported" may cause confusion, as client IP preservation is its most prominent feature - most likely also more prominent than the reduced number of hops
* [Being the default setting for e.g. nginx's nginx-ingress-controller helm chart](#ootb)
  * Ultimately, there will be always opt-in/opt-out fields in Kubernetes resources which impact cross-provider-support.
  * The fact that e.g. nginx inc.'s ingress helm chart expects `externalTrafficPolicy: Local` to work without problems does not mandate that SCS must share this view. In fact, while it is not the only helm chart to set it by default, there are a few popular ingress controller charts which apparently do not: [`kubernetes/ingress-nginx` helm chart](https://github.com/kubernetes/ingress-nginx/blob/e7bee5308e84269d13b58352aeae3a6f27ea6e52/charts/ingress-nginx/values.yaml#L475), [traefik helm chart](https://github.com/traefik/traefik-helm-chart/blob/d1a2c281fb12eca2693932acbea6fec7c2212872/traefik/values.yaml), [contour helm chart](https://github.com/bitnami/charts/blob/30300ee924e6e6c55fe9069bf03791d8bcae65b7/bitnami/contour/values.yaml).
  * Furthermore, even when `externalTrafficPolicy: Local` is required to work while not being required to preserve the client IP, this directly contradicts the nginx's helm chart parameter docs, which say that ["Local preserves the client source IP"](https://docs.nginx.com/nginx-ingress-controller/installation/installation-with-helm/#configuration).
* [Improve performance](#performance)
  * Significant improvements are possible, but are not validated yet

### Conclusion (**TBD**)

| Option 1 | Option 2 |
|----|----|
| Require SCS compliant clouds to work with `externalTrafficPolicy: Local` (enabling the health check mechanism to avoid constant connectivity problems) | Do not require SCS compliant cloud providers to support `externalTrafficPolicy: Local` |

# Decision

* A "vanilla" Kubernetes `Service` with `type=LoadBalancer` without any special fields set: Must work as expected, out of the box
* An otherwise "vanilla" `Service` with `externalTrafficPolicy: Local` set: **TBD**

# Conformance Tests

With default `externalTrafficPolicy: Cluster`:

```bash
#!/bin/bash

set -e

suffix=$(openssl rand -hex 3)

kubectl get pods nginx-$suffix > /dev/null || kubectl run nginx-$suffix --restart=Never --image=nginx --port 80
kubectl get svc nginx-$suffix-svc > /dev/null || kubectl expose pod nginx-$suffix --port 80 --name nginx-$suffix-svc --type=LoadBalancer

while [[ -z "$IP" ]]; do
  IP=$(kubectl get svc nginx-$suffix-svc '--output=go-template={{range .status.loadBalancer.ingress}}{{.ip}}{{end}}')
done

echo "Testing access to $IP.
externalTrafficPolicy: Cluster
"
set -x
for i in {1..30};do
  curl --max-time 5 -sS $IP > /dev/null && break || echo "pretest $i: curl failed, but wait until one call succeeded or enough tests failed to stop waiting"
done
echo "Do actual testing, now"
for i in {1..50};do
  curl --max-time 2 -sS $IP > /dev/null
  echo "test $i: succeeded"
done

kubectl delete pod nginx-$suffix
kubectl delete svc nginx-$suffix-svc
```

With `externalTrafficPolicy: Local` being set:

```bash
#!/bin/bash

set -e

suffix=$(openssl rand -hex 3)

kubectl get pods nginx-$suffix > /dev/null || kubectl run nginx-$suffix --restart=Never --image=nginx --port 80
kubectl get svc nginx-$suffix-svc > /dev/null || kubectl expose pod nginx-$suffix --port 80 --name nginx-$suffix-svc --type=LoadBalancer --overrides='{"metadata": {"apiVersion": "v1"}, "spec": {"externalTrafficPolicy": "Local"}}'
while [[ -z "$IP" ]]; do
  IP=$(kubectl get svc nginx-$suffix-svc '--output=go-template={{range .status.loadBalancer.ingress}}{{.ip}}{{end}}')
done

echo "Testing access to $IP.
externalTrafficPolicy: Local
"
set -x
for i in {1..30};do
  curl --max-time 5 -sS $IP > /dev/null && break || echo "pretest $i: curl failed, but wait until one call succeeded or enough tests failed to stop waiting"
done
echo "Do actual testing, now"
for i in {1..50};do
  curl --max-time 2 -sS $IP > /dev/null
  echo "test $i: succeeded"
done

kubectl delete pod nginx-$suffix
kubectl delete svc nginx-$suffix-svc
```

