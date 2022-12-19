---
title: Behavior of KaaS load balancers
type: Standard
status: Draft
track: KaaS
---

# Introduction

Kubernetes `Services` with [`type: LoadBalancer`](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer) provide an abstraction to configure load balancers which are usually provided by the cloud.

The "cloud" (respectively the cloud controller manager) is responsible to implement this.

In effect, when a user creates such `Service` on any cloud provider, there are generally no provider specific operations required for basic use cases.

# Motivation

While the user-facing API of `type=LoadBalancer` `Services` is actually quite small, there are a few caveats when setting [`externalTrafficPolicy: Local`](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip) using the default OpenStack configuration.

An user may opt to set it to `Local` in order to e.g. preserve client IP addresses or because of performance concerns. In the following, this use case is referred to as "The Special Use Case".

# Design Considerations

## Options considered

### **Do not require** that "The Special Use Case" works out of the box

By default, `create-monitor` is not enabled in the OpenStack controller manager. While [changing this](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/commit/002cecdc3680be3dc64b0dd71a84a6696b62c908) seems to make it work, there may be good reasons for keeping this opt-in.

Because of these reasons (which are yet to be researched), it might be best to keep things as-is and do not require SCS KaaS clusters to work out of the box in this configuration.

### **Do require** that "The Special Use Case" works out of the box

The reasons which are mentioned in the previous section may also not lead to the decision that keeping `create-monitor` opt-in is the best way to go. In this case, set `create-monitor` by default.

# Open questions

- What are the reasons for setting `create-monitor` being opt-in?

# Decision

The default use case of using a `Service` with `type: LoadBalancer` and `externalTrafficPolicy: Cluster` is required to work.

"The Special Use Case" of using a `Service` with `type: LoadBalancer` and `externalTrafficPolicy: Local` is TBD.

# Conformance Tests

For default use case:

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

For "The Special Use Case":

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

