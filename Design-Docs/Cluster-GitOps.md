# Proposal for GitOps Style IaC for Cluster Management

Kurt Garloff, v0.1, 2022-02-18

## Motivation and Goals

Using the Kubernetes Cluster-API (capi), we can use a k8s style declarative
way to describe the workload clusters that should be running and can manage
their lifecycle: creation, changes, rolling upgrades amd clean up can all be
performed with it. The OpenStack provider (capo) has the basic integration
to manage the networks, virtual machines, load-balancers. For full automation,
a few more pieces have been developed in the SCS
[k8s-cluster-api-provider](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/)
repository: Registering the images, setting up extra security groups for
non-Calico CNI, creating anti-affinity server groups, deploying the OCCM
and cinder CSI integration and optionally some more services (such as Flux,
cert-manager, nginx ingress, ...)

This follows similar ideas as described on
<https://www.weave.works/blog/gitops-and-cluster-api-master-of-masters>.

Most of the simpler cluster setups can be done without ever touching the cluster-template.yaml
file -- just doing a dozen adjustments in clusterctl.yaml provides a reasonable amount
of flexibility. In SCS' k8s-cluster-api-provider setup, the standards settings from
the capo templates have been extended by the settings that let you chose cilium
as alternative CNI provider, the OCCM and CSI deployment and the extra services.

To implement a simple gitops style management for a set of clusters, we would
basically create a reconciliation loop on the capi management node, which
gets the enhanced configuration files from git and creates, changes and
destroys clusters according to the settings there. The mechanism should
distinguish between base settings and overlays (kustomization style) to
modify and extend the settings and should allow an opt-in mechanism to
do more detailed adjustments via overriding also the cluster-templates
(kustomization style again).

Cluster-admin credentials need to be provided to the owners of the cluster.
The current thinking is to have a public key included in the git repo;
the cluster-admin credentials for the created cluster would be encrypted
with this public key and can then be published. (Would still use https
to ensure that these are the true credentials.) Only the owner(s) of
the private key can decrypt the credentials.

## Implementation thoughts

The loop would roughly look like this:
1. Get the latest clusters from git (via a regular check or an event)
1. Per cluster
1.1. Ensure we have the image available, register if needed
1.1. For a new cluster
1.1.1. Optionally create a new project (for a new cluster), if so share the image to it
1.1.1. Create two application credentials (one for capo, one for OCCM/CSI)
1.1.1. Create cilium security group
1.1. Create anti-affinity
1.1. Adjust settings in the cluster-template (cluster-name, sec groups, affinity, ...)
1.1. Process with clusterctl
1.1. Submit to capo
1.1. Wait for control plane readiness
1.1. For new cluster: Extract cluster-admin creds and encrypt with pubkey
1.1. Deploy CNI (calico or cilium) -- avoid switching unless forced
1.1. Deploy OCCM
1.1. Deploy cinder
1.1. Deploy metrics service (if not disabled), otherwise remove
1.1. Sanity checks
1.1. For all other optional services (nginx, flux, cert-manager, harbor, ...):
1.1.1. Deploy service if enabled, otherwise remove (if deployed before)
1.1. Sanity checks
1.1. optional CI tests

## Open questions

* Can this be integrated into capo or do we really need to create a loop around it?

* Can we integrate this with the helm charts work?

* Can we implement this using flux?

* How does this relate exactly to <https://github.com/weaveworks/weave-gitops>?
