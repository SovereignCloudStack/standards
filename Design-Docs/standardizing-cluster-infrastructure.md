---
title: Digital Sovereignty through standardized cluster stacks, provider-independent infrastructure, and clearly separated layers 
version: 2022-04-29-001
authors: Sven Batista Steinbach, Janis Kemper
state: Draft
---

# Digital Sovereignty through standardized cluster stacks, provider-independent infrastructure, and clearly separated layers

<!-- toc -->
- [Summary](#summary)
- [Motivation](#motivation)
  - [Goals](#goals)
  - [Non-goals](#non-goals)
- [Proposal](#proposal)
  - [Proposal 1: Pre-defined cluster stacks are necessary to ensure that clusters and applications work - a free configuration of cluster components is not possible](#proposal-1-pre-defined-cluster-stacks-are-necessary-to-ensure-that-clusters-and-applications-work---a-free-configuration-of-cluster-components-is-not-possible)
  - [Proposal 2: Cluster operators should be able to define clusters independently of the provider](#proposal-2-cluster-operators-should-be-able-to-define-clusters-independently-of-the-provider)
  - [Proposal 3: Users should be able to define applications independently of the cluster infrastructure](#proposal-3-users-should-be-able-to-define-applications-independently-of-the-cluster-infrastructure)
- [User stories](#user-stories)
  - [User story 1: DevOps expert configuring applications on SCS infrastructure](#user-story-1-devops-expert-configuring-applications-on-scs-infrastructure)
  - [User story 2: Cloud provider implementing SCS stack](#user-story-2-cloud-provider-implementing-scs-stack)
  - [User story 3: User wanting to implement a multi-cloud](#user-story-3-user-wanting-to-implement-a-multi-cloud)
  - [User story 4: SCS operator wanting to have maintainable SCS infrastructure](#user-story-4-scs-operator-wanting-to-have-maintainable-scs-infrastructure)
- [Risks and Mitigations](#risks-and-mitigations)
- [Design details](#design-details)
  - [Proposal 1: Using cluster stacks](#proposal-1-using-cluster-stacks)
    - [What exactly is a cluster stack?](#what-exactly-is-a-cluster-stack)
    - [What components does a cluster stack have? What has to be considered when defining a stack?](#what-components-does-a-cluster-stack-have-what-has-to-be-considered-when-defining-a-stack)
      - [Layer 1: Pre-cluster state](#layer-1-pre-cluster-state)
      - [Layer 2: Cluster state](#layer-2-cluster-state)
      - [Layer 3: Kubernetes core](#layer-3-kubernetes-core)
    - [Example of a cluster stack](#example-of-a-cluster-stack)
  - [Proposal 2: Cluster definition is independent of the provider](#proposal-2-cluster-definition-is-independent-of-the-provider)
  - [Proposal 3: Applications are configured independently of the cluster infrastructure](#proposal-3-applications-are-configured-independently-of-the-cluster-infrastructure)
  - [Drawbacks](#drawbacks)
  - [Alternatives](#alternatives)
<!-- /toc -->

## Summary

We want to define cluster infrastructure, which works on different cloud providers. The cluster infrastructure should have as much flexibility as possible but has to be well-defined and tested to ensure a good user experience while defining and creating clusters as well as launching applications.

Infrastructure should be portable from one provider to the other and providers should be easily certifiable. The provider infrastructure should be transparent for everybody.

Every cloud provider has to have a Cluster API provider integration and a cloud controller manager (CCM). It can be both an “actual” cloud provider with API and a bare-metal system (based on OpenStack).

To facilitate the configuration of applications in these clusters, we propose to standardize CCM (load balancer) and naming of storage classes, so that applications can be configured independently of the cluster infrastructure.  

## Motivation

The main goal of SCS is to ensure the users’ and cluster operators’ sovereignty while using European cloud infrastructure. With this proposal, we want to ensure that the infrastructure, from the node image to core Kubernetes components, is transparent in all SCS providers. We want to have a concise structure and good documentation on what providers have to do to get certified by SCS and aim to keep the certification process itself lean.

Furthermore, we consider the freedom of choosing a provider a key to the sovereignty of cluster operators. They should operate their clusters fully independently of the provider infrastructure.

For users who launch and run applications on SCS-certified infrastructure, we want to ensure that they do not have to worry about security issues. SCS infrastructure should only get certified when all aspects of security are taken care of. The users should be able to configure their applications independently of the cluster infrastructure. Only this will lead to actual sovereignty, as they would otherwise have to worry about certain security issues, e.g. related to metrics-server with self-signed certificates.

### Goals

- Standardize infrastructure (e.g. definition of load balancers) of European cloud providers
- Easy certification process for cloud providers
- Concise documentation on how to fulfill SCS certification
- Applications are configured independently of the cloud provider
- Automated e2e tests for cluster and application configuration
- Secure cluster infrastructure for users and cluster operators
- Auditability & automated testing (unit and e2e tests) of SCS code

### Non-goals

- This proposal does not intend to define specifically all inputs, e.g. to define load balancers in SCS infrastructure. This is left for an open discussion in the SCS team and with cloud providers.
- We don’t want to say that any specific components are must-haves for cluster infrastructure, but we will give suggestions.

## Proposal

This proposal does not specify any details about load balancer definitions, node images, or server types. It rather aims to define a way to handle standardization and certification in general.

It consists of three parts:

### Proposal 1: Pre-defined cluster stacks are necessary to ensure that clusters and applications work - a free configuration of cluster components is not possible

A cluster stack consists of “big components”, e.g. node image and Cluster API provider; down to “small” ones, such as private/public network, IPv4/IPv6, container runtime (interface), and firewall. All of these components related to the image, networking, or cluster resources interact and there is no way of freely configuring such a cluster without heavy constraints.

Why do we think that such cluster stacks are necessary?  

- Some configurations are incompatible (e.g. choosing eBPF without a node image that supports it)
- Some configurations might work but require further knowledge and additional work (Ubuntu and Cilium work together in general, but not with Cilium’s latest version because of a bug in older kernels)
- Some configurations depend on the cloud providers. A user has to know these details to get a working system (MTU size, e.g. with Cilium).

Assuming that a cluster consists of n components, then we would say that decisions need to be taken for all of these n components (i.e. Kubeadm as bootstrap controller or Ubuntu as OS for node image). The collection of these decisions defines a cluster stack.

There can be multiple cluster stacks to satisfy different needs, but there should not be too many cluster stacks. This is necessary to keep the cluster stacks maintainable (defining, testing, updating) and to not overwhelm and confuse users with a large number of stacks that cannot be clearly differentiated.

### Proposal 2: Cluster operators should be able to define clusters independently of the provider

The cluster infrastructure should be independent of the providers because of a few reasons. It ensures true freedom of choice (a big aspect of digital sovereignty), allows easy migrations of infrastructure from one provider to another, and keeps the configuration of clusters easy for cluster operators.

To achieve this, the Cluster API provider integrations have to be standardized in some way. Cluster operators should only configure objects that are independent of the provider. For example, instead of having to configure the `ProviderMachine` object of two different providers, the cluster operator should only configure an SCS machine object, which is then translated into the object of the relevant provider. This is not meant to change the provider integrations themselves, but rather to have an additional translation layer.

### Proposal 3: Users should be able to define applications independently of the cluster infrastructure

SCS should have a repository with application configurations. The configurations in this repository should not depend on the provider, as this would create a lot of additional maintenance work. Additionally, it would not be possible to migrate applications easily from one provider to another.

To achieve independence of application configurations from the cluster infrastructure, there are mainly two tasks that have to be done: standardizing the CCM, which currently requires provider-specific configurations of service objects, and standardizing the naming of storage classes.  

## User stories

The persona we call “user” (using SCS clusters) is only supposed to work with applications and should not worry at all about the cluster infrastructure below. Cluster operators define and manage clusters based on pre-defined cluster stacks that are implemented by infrastructure providers.

### User story 1: DevOps expert configuring applications on SCS infrastructure

A DevOps expert wants to add a Traefik ingress to the SCS application stack. As the ingress needs a load balancer, he defines a service of type load balancer. In the SCS documentation, there is a section describing how to implement a load balancer and what kind of parameters can be set, such that the DevOps expert does not need a long time to finish the configuration. This configuration is now valid for all cloud providers and can be used for every cluster on different European cloud providers. The maintainability of SCS applications is ensured by this independence of the application and cluster layer.

### User story 2: Cloud provider implementing SCS stack

After the cloud provider implemented the SCS cluster stack, all applications are ready to be installed and work perfectly. Therefore, the cloud provider does not have to invest time in configuring applications but can rely on the pre-defined and well-maintained SCS stack. Its users can profit from the additional value generated by this feature of ready-to-install applications. E2E tests ensure that everything has been implemented correctly.

### User story 3: User wanting to implement a multi-cloud

As the applications can be used on every SCS-certified cloud, a true multi-cloud is possible.

### User story 4: SCS operator wanting to have maintainable SCS infrastructure

Through few but well-defined cluster stacks, most use-cases of cloud providers and users are covered. These few stacks can be easily maintained by the SCS operator. Automated E2E tests reduce the manual work.

## Risks and Mitigations

The risks are the same as every standardization has. Cloud providers might not be satisfied by the selection of cluster stacks that SCS chose. As soon as one wish is granted, others come and want to have their ideas implemented in SCS as well. In the end, there is no standardization and a useless certification of SCS infrastructure.

## Design details

As described above, we want to achieve two things: standardizing clusters and making applications independent of the cluster infrastructure itself. By separating these two layers, we achieve a clear definition of responsibilities and compatibility of different cloud providers.

In this way, standardized but also configurable Kubernetes clusters can be created in self-service - also via GitOps.

### Proposal 1: Using cluster stacks

There are various components playing a role in defining cluster infrastructure. We consider the following three technical layers:

1. Pre-cluster state - node image
2. Cluster state - Cluster API and provider implementation
3. Kubernetes core applications

All of these layers depend on each other, such that it is not possible to freely select and exchange components. This is why we introduce the cluster stack which consists of a selection of sub-systems and configurations that follow a certain goal.

For example, there can be a stack for Kubernetes version 1.22 and one for 1.23. There can also be stacks that use a node image based on Ubuntu and others with Fedora. These cluster stacks have to be implemented by the providers, as there are certain details, e.g. related to the node image, that have to be adapted to the respective provider.

The process of building and implementing these cluster stacks has to be well designed, as there are new patch versions every couple of weeks. Providers should be able to implement cluster stacks within a few days. E2E tests play a big role in automating work and ensuring that everything works.

#### What exactly is a cluster stack?

First, SCS defines a stack and decides that it should use a certain Kubernetes version, that it has a certain node image, etc. Based on these decisions, the stack is defined in yaml files using some templating language (e.g. Helm/Helmfile or Jsonnet). These yaml files can be seen as a framework that is implemented by the providers. Some parts of the cluster stack configuration have to be adapted by the cloud providers. Good documentation from SCS ensures that implementing a cluster stack is straightforward. A templating language is used, so that cluster operators can specify certain configurations of the cluster stacks that have not been fixed. For example, the configuration of OpenID Connect.

#### What components does a cluster stack have? What has to be considered when defining a stack?

Based on the aforementioned layers, we want to make a list of all technical details, cluster components, and things to consider.

##### Layer 1: Pre-cluster state

The pre-cluster state consists of the node image that has to be compatible with the provider and impacts both the second and third layers. This is why it has to be created for each stack and infrastructure provider. The SCS project can build frameworks that allow providers to efficiently create and publish the node images.

It is important to consider that providers use different ways of providing these images. For example, Hetzner Cloud provides them indirectly by using snapshots in the creation process of a server. OpenStack, on the other hand, uses qcow2 images that are provided in a direct way. Note that in both cases images can be created with certain tools (e.g. Packer).

The node images can be tested with SCS E2E tests and a test framework that can be implemented by every provider.

There are various components, tools, and possible configurations that play a role in the pre-cluster state. This is a list that should serve as a reference:

- Node problem detector (https://github.com/kubernetes/node-problem-detector): It depends on the OS because node errors do.
- konnectivity-server ([https://kubernetes.io/docs/tasks/extend-kubernetes/setup-konnectivity](https://kubernetes.io/docs/tasks/extend-kubernetes/setup-konnectivity/)): kube-api-server proxy for traffic from control planes to cluster
- Production-readiness: log-collector, log-rotator, pinning versions, DNS, NTP, ssh-hardening
- Container Runtime (CRI-conform): cri-o, containerd
- Low-Level Container Runtime (OCI-conform): crun, runc, runsc (gvisor), kata containers. With the help of runtime objects, this could be chosen directly in Kubernetes. Kata containers, for example, don’t work with virtualized systems without nested KVM support.
- cgroups V2 vs V1, croupfs vs systemd
- eBPF support: requires kernel >5.10
- iptables requirements: depends on whether kube-proxy is used, which is not the case in some modern systems
- SSH hardening
- Firewall: local software firewall, externally or via cilium eBPF firewall

##### Layer 2: Cluster state

Cluster state consists of standardized Cluster API objects, such as `ClusterClass`, and other life cycle objects, e.g. `MachineDeployment` and `MachineHealthCheck`. Additionally, there are provider-specific objects that exist in every provider integration, like `ProviderCluster` and `ProviderMachineTemplate`, as well as other objects.

SCS has to define the inputs for those objects in each Cluster Stack in such a way, that each provider can implement it.

The most important standardization, but also the one that restricts the options to define clusters the most, is related to how the Kubernetes system is supposed to look like. Note that the Kubernetes system is heavily influenced by the components chosen for the pre-cluster state.

The first decision that has to be taken is to select a bootstrap provider: Kubeadm or Talos. Talos would require a node image with Talos OS.

A note here on the choice of bootstrap provider: the CAPI control-plane-provider and bootstrap-provider depend on this and have to be either from Kubeadm or Talos. This has to be supported by the infrastructure provider as well.

A specific Kubernetes version has to be chosen as well, as other components depend on it.

**What do we consider part of every cluster stack?**

We recommend choosing these components for every stack to make sure that the cluster works well, is secure and that the maintainability of the cluster stacks is better. As all of the settings that we propose differ a lot between Talos and Kubeadm, we choose the latter one, as it is more common.

In Kubeadm there are some settings that we would consider must-haves:

- cloud-init
- audit-logs
- Signed certificates - CSR controller (e.g. integrated into CAPI (provider integration)), which validates and approves certificate signing requests and is, for example, the base for running metrics-server securely
- aggregation-layer
- security settings, to fulfill at least CIS benchmark

Furthermore, there are some settings and configurations that SHOULD be part of every cluster stack. Cluster operators should be able to change the defaults set in the cluster stacks, e.g. to switch OpenID Connect on or off.

- etcd encryption
- HPA config
- OIDC config
- admission-control

##### Layer 3: Kubernetes core

There are a few components that have to be considered in this layer. First of all, the provider-specific cloud controller manager (CCM). The container network interface (CNI) is another component, which depends heavily on other selected components (Cilium, eBPF, node image, MTU size, configuration of Cluster API objects like `ProviderCluster`).

There is also an interesting component, which is used for Kubernetes clusters that follow the zero-trust principle: the konnectivity-agent. It depends on the node image, as a konnectivity-server is needed, on the Kubeadm configuration of the Cluster API objects (egress config), and can depend on the CNI, as environments without kube-proxy are currently not supported.

#### Example of a cluster stack

This example is very high-level and cannot go in-depth. It is an example of a selection of components, which could serve as a base for a working cluster stack.

**Pre-cluster state**: Node image with Ubuntu, cgroups V2, containerd, crun, eBPF support, node-problem-detector, and konnectivity-server.

**Cluster state**: Kubeadm and cloud-init, private networks, etcd encryption, audit-logs, admission-control, HPA config, signed certificates and CSR controller, Kubernetes 1.23.6

**Kubernetes core**: Cillium with kube-proxy, CCM, CSI, konnectivity-agent

### Proposal 2: Cluster definition is independent of the provider

We propose a templating logic for clusters, which aims for having only two parameters defining the cluster infrastructure: the names of the provider and of the cluster stack. Both parameters can be exchanged freely, as long as the provider implements a certain cluster stack. All the rest of the cluster definition remains unaffected.

To achieve this, apart from defining cluster stacks as described in Proposal 1, the provider integrations of Cluster API have to be aligned. SCS should define certain parameters, e.g. `ProviderMachineTemplate`, and all provider integrations of SCS providers should have some kind of translation matrix so that this input can be converted into the relevant provider object, e.g. `HCloudMachineTemplate`.

We want to leave out the details of how this translation from SCS-defined properties into the respective provider integrations works. It can be discussed in future meetings.

### Proposal 3: Applications are configured independently of the cluster infrastructure

The first step of achieving independence of the layers, the cluster stacks have to be aligned in a certain way, e.g. that a CSR controller is a must-have for running metrics-server securely. This has been described in Proposal 1.

The second step consists of two tasks:

- Defining an adapted SCS cloud provider interface that unifies the inputs for creating load balancers
- Standardizing the naming of storage classes

A normal CCM has one object that it creates: the load balancer. Based on a service object that is defined by the user and that contains certain annotations, the CCM creates a load balancer. Service objects are written by users and play a big role in a lot of applications. Right now, if a user wants to switch from one cloud provider to another, he needs to adapt the annotations he sets in the service objects of his application configurations.

Example:

- OpenStack load balancer: [https://github.com/kubernetes/cloud-provider-openstack/blob/master/pkg/openstack/loadbalancer.go#L67](https://github.com/kubernetes/cloud-provider-openstack/blob/master/pkg/openstack/loadbalancer.go#L67)
- Hetzner load balancer: [https://github.com/syself/hetzner-cloud-controller-manager/blob/master/internal/annotation/load_balancer.go](https://github.com/syself/hetzner-cloud-controller-manager/blob/master/internal/annotation/load_balancer.go)

This can be avoided rather easily. We have to implement a new interface for load balancers, as a counterpart to the current one ([https://pkg.go.dev/k8s.io/cloud-provider#LoadBalancer](https://pkg.go.dev/k8s.io/cloud-provider#LoadBalancer)), which is a part of the cloud provider interface ([https://pkg.go.dev/k8s.io/cloud-provider#Interface](https://pkg.go.dev/k8s.io/cloud-provider#Interface)). SCS implements the current cloud provider interface and defines a new one, which SCS cloud providers have to implement. In there, we unify the naming of the annotations and give a pre-defined set of inputs to the function that, for example, creates a load balancer.

To be more precise: Instead of `"load-balancer.hetzner.cloud/id"` and `"[loadbalancer.openstack.org/load-balancer-id](http://loadbalancer.openstack.org/load-balancer-id)"` we would establish a standard that could be named `"load-balancer.scs.cloud/id"`. The SCS load balancer controller interface knows these annotations and converts them into a function like the following:
 `func CreateLoadbalancer(id string, otherInputs object) error`

Note that the ID here comes from the aforementioned annotation. Of course, this function will have more parameters after the standardizing process is completed. `otherInputs` serves as a placeholder for all those still missing inputs. To define precisely the annotations and parameters of the functions that cloud providers need to implement, further discussion is required in the SCS team.

Note that standardizing the inputs has the effect that cloud providers cannot have certain individual features, which require some unique inputs.

The second task is to standardize the naming of storage classes.

Different cloud providers have different storage classes and name them differently. As these names of the storage classes are used in persistent volume claims (i.e. parts of the configuration of our applications) ([https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reserving-a-persistentvolume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reserving-a-persistentvolume)), we would need a separate configuration for each application and cloud provider. Therefore, there wouldn’t be any standardization. Instead, we propose to standardize the naming of storage classes, so that the PVCs in the configuration of applications can be defined independently of the provider.

### Drawbacks

Standardizing something always leads to less freedom of choice. Cloud providers would not be able to have individual inputs for creating load balancers, so some of their features might be obsolete.

There will be always cluster operators, which are not satisfied by the selection of cluster stacks and want to see their desires to be reflected in SCS infrastructure. A notable point of discussion in the future will be Talos vs Kubeadm. Choosing the “modern version” Talos changes a lot of other components of a cluster stack. While it is not used in production in many companies, there are a lot of users that want to work with it. They will insist on cluster stacks with Talos.  

### Alternatives

**No standardization of annotations for service objects in CCM**:

This allows cloud providers to be more flexible about their feature set, as they don’t have to align it with others. Applications would depend on cloud providers, so that there are up to n different configurations of one application for n cloud providers. Users have to deal with these different configurations and have a much higher workload. [Here]([https://github.com/dysnix/helmfiles/tree/master/releases/ingress-nginx](https://github.com/dysnix/helmfiles/tree/master/releases/ingress-nginx)) is an example of an application, which contains provider-specific configurations. There is no standardization of cloud providers, which makes SCS certifications weak and migrations from one provider to the next hard.

**No definition of cluster stacks, but rather a definition of relationships of components (”component A is independent of component B, no matter how the individual choice looks like”, or “if A1 is chosen, then you cannot choose B1”)**:

These rules would be extremely difficult to set up and maintain. As no proper testing is feasible for so many combinations, the results for the users and cluster operators would be worse. Errors might happen. The positive side would be that there is more choice in the definition of a cluster. It is questionable, however, if more choices give so much additional value, that it is acceptable to have a system that is not tested well. Furthermore, it would be very difficult to manage certifications. While a cloud provider can get certified easily for implementing cluster stacks, it is less clear how this would work without having pre-defined cluster stacks.
