# Adoption costs for SCS standards

This document outlines the adoption costs for the KaaS/Kubernetes standards of the SCS project. Tests and estimates were
done using Yaook especially `yaook/k8s`, which provides a functioning Kubernetes cluster on top of an Openstack instance.
Nonetheless, other Kubernetes cluster variants should have similar costs for adopting standards, since in the end,
the frontend is a Kubernetes cluster.

## Standards

### SCS K8s Version Policy Standard (scs-v0210-v2-k8s-version-policy)

The test for the [K8s Version Policy Standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0210-v2-k8s-version-policy.md) can't be used like
most other tests provided in the SCS standards repository.
It aims on testing a KaaS offering of a CSP with the creation of the most recent Kubernetes
version provided by the CSP. Since only this part is tested, the test doesn't have any validity for a single
cluster, since the updating and versioning should be decided by the user, which could want to leave a server
on a version just for stability reasons.

In general, updating a single cluster isn't that time intensive, but providing a complete update for a Kaas
offering, especially with the requested testing could take some more time. 
In this instance, we will only look at updating a single cluster, which should be done in an hour (depending on the running applications and the size of the cluster).

Estimated cost: 60 man-minutes for a single cluster

### SCS KaaS Default storage class Standard (scs-0211-v1-kaas-default-storage-class)

HINT: This standard isn't yet required by any "SCS KaaS Compatible" version.

Most of the standard isn't hard to adopt for a cluster, since it only involves simple modification of `StorageClass` objects.
The cost-intensive part would be the hardware failure protection by binding the `StorageClass` to redundant,
non-lifecycle bound storage, since this would mean that storage needs to be provided in a higher capacity to
achieve the same usable capacity. This possibly incurs extra cost for hardware, which is around 130€ for a terabyte of datacenter SSD. 
Due to the scale of variation for possible installations, no man-hour estimation will be done here for the hardware part.

Estimated cost: 10 man-minutes just for the `StorageClass` settings

### SCS K8s Node Distribution and Availability (scs-0214-v1-k8s-node-distribution)

Node distribution can be a challenging topic to tackle, especially for CSPs with small infrastructures
or shared control-plane clusters. How these special setups are handled still needs to be discussed further
in future standard versions.

If we take a default Kubernetes cluster for a CSP, it is fairly easy to distribute a cluster with multiple
nodes over different machines, zones and regions (concepts which are provided by the IaaS layer).
Nodes must be distributed over multiple failure zones, which also needs to be shown through a set of labels.
These labels need to be applied to a cluster; this should be done automatically or via a utility application, but
it can also be done manually. This (obviously) incurs higher costs the more clusters need to be labelled.

Estimated cost: 10 man-minutes per cluster, if done manually