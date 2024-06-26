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
  * The mere fact that e.g. nginx inc.'s ingress helm chart sets `externalTrafficPolicy: Local` does not mean it is some sort of "industry standard procedure". In fact, while it is not the only helm chart to set it by default, there are a few popular ingress controller charts which apparently do not: [`kubernetes/ingress-nginx` helm chart](https://github.com/kubernetes/ingress-nginx/blob/e7bee5308e84269d13b58352aeae3a6f27ea6e52/charts/ingress-nginx/values.yaml#L475), [traefik helm chart](https://github.com/traefik/traefik-helm-chart/blob/d1a2c281fb12eca2693932acbea6fec7c2212872/traefik/values.yaml), [contour helm chart](https://github.com/bitnami/charts/blob/30300ee924e6e6c55fe9069bf03791d8bcae65b7/bitnami/contour/values.yaml).
  * Furthermore, even when `externalTrafficPolicy: Local` is required to work while not being required to preserve the client IP, this directly contradicts the nginx's helm chart parameter docs, which say that ["Local preserves the client source IP"](https://docs.nginx.com/nginx-ingress-controller/installation/installation-with-helm/#configuration). So, even though the deployment will fundamentally work out of the box, it will work differently than it would be expected by an user who reads the nginx-ingress-controller helm chart documentation.
* [Improve performance](#performance)
  * Significant improvements are possible, but are not validated yet

### Conclusion

Options regarding `externalTrafficPolicy: Local`:

1. <a name="selectedoption"></a>Option "No support"
    - DO NOT require SCS compliant cloud providers to support `externalTrafficPolicy: Local`.
    - In the reference implementation: DO NOT configure health checks in order to not deviate from upstream defaults
    - Leave the option open to standardize e. g. proxy protocol (and/or HTTP `Forwarded` headers) later
1. Option "No support; best effort compatibility in reference implementation"
    - DO NOT require SCS compliant cloud providers to support `externalTrafficPolicy: Local`.
    - In the reference implementation: enabling the health check mechanism to avoid constant connectivity problems if users set it anyway
1. Option "Partial support; No IP preservation"
    - DO require SCS compliant clouds to work with `externalTrafficPolicy: Local`.
    - Do NOT require them to preserve the client IP.
    - In the reference implementation: Enabling the health check mechanism to avoid constant connectivity problems
1. Option "Partial support; Support opt-in IP preservation at a higher level"
    - DO require SCS compliant clouds to work with `externalTrafficPolicy: Local`.
    - DO require them to let the user opt-in to preserve the client IP using the proxy protocol, HTTP `Forwarded` headers or other means
    - Do NOT require them to preserve the client IP at network level.
    - In the reference implementation: Enabling the health check mechanism to avoid constant connectivity problems
1. Option "Full support"
    - DO require SCS compliant clouds to work with `externalTrafficPolicy: Local`.
    - DO require them to preserve the client IP at network level.
    - In the reference implementation: Implement network level load balancing

# Decision

* A Kubernetes `Service` of `type=LoadBalancer` with all non-mandatory fields being unset: Must work as expected, out of the box
* A Kubernetes `Service` of `type=LoadBalancer` with `externalTrafficPolicy: Local` set and all other non-mandatory fields being unset: [Option 1](#selectedoption): "No support" required

# Conformance Tests

TBD, depends on decision
