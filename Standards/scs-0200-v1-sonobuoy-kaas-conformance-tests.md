---
title: Sonobuoy kaas conformance tests framework
type: Decision Record
status: Draft
track: KaaS
---


## Introduction - Motivation

With the **k8s-cluster-api-provider**[K8S_CLUSTER_API_PROVIDER/LINK] the SCS provides a tooling to generate and manage k8s cluster ontop of it's openstack IAAS infrastructure.
Part of this tool is the usage of [sonobuoy](https://sonobuoy.io/) as a **"test suit tool"** to execute the official [kubernetes e2e tests](https://github.com/kubernetes/kubernetes/tree/master/test/e2e).
Future conformance tests derived from standards could already be part of the kubernetes e2e tests and could be provided by running the integrated sonobuoy [e2e test plugin](https://sonobuoy.io/docs/main/e2eplugin/).

But appart from running the kubernetes e2e tests sonobuoy also allows to write your own tests and apply it as a self created [plugin](https://sonobuoy.io/docs/v0.57.0/plugins/).
So for all tests not already provided by the [e2e test plugin](https://sonobuoy.io/docs/main/e2eplugin/) we shuold first write our own tests and second make them executable with sonobuoy.
Hence it would be useful to also use Sonobuoy as a test suit combined with a framework for writing SCS conformance tests.

### Short Sonobuoy Intruduction

The main objective of a [sonobuoy plugins](https://sonobuoy.io/docs/v0.56.17/plugins/) is to present test results and their status in a consolidated way.
This is essentially done by applying the test to a pod that is applied to the k8s cluster under test.
A sonobuoy worker then supervises this pod and forwards all test results to the aggregator.
It does this by waiting for a "done file" to be created. Once this file is created, it forwards the results to the aggregator, using a predefined location of the results file within the done folder, as seen in following image:
![image search api](https://sonobuoy.io/img/plugin-contract.png)

Therefore, in order to apply the conformance tests as a plugin, we need a tooling/ wrapper to implement the individual test scripts that:

* Gathers all test results and provides them in the results file.
* Run tests in sequence and signal the worker when it is finished by writing the "done file".

Apart from providing the test results, a plugin container must also pass on the status of each test by setting the status flag in the results file.
In addition, to run the tests as a sonobuoy plugin, we need to create an image that can be run inside the k8s cluster under test.



## Design Considerations

#### Which plugin sceleton to use for implementation

Sonobuoy provides plugin examples in the following repository: [https://github.com/vmware-tanzu/sonobuoy-plugins](https://github.com/vmware-tanzu/sonobuoy-plugins)



- [e2e-skeleton](https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/examples/e2e-skeleton)
- https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/plugin-helper
- https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/requirements-check
- https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/cluster-inventory
- https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/cis-benchmarks
- https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/sonolark
- [sonoshell](https://github.com/vmware-tanzu/sonobuoy-plugins/blob/main/sonoshell)

The most suitable plugin for us would be the[e2e-skeleton](https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/examples/e2e-skeleton).
This plugin makes use of the [e2e-framework](https://github.com/kubernetes-sigs/e2e-framework)




#### Recommended File Structure DRAFT

- Sonobuoy is only a framework for all Kubernetes associated conformance tests.
- Therefore the kaas file structure should be implemented around it
- Therfore following file structure SHOULD be provided by the kaas directory:


NOTE: this structure takes into account that the implementation is based on writing all tests in Go


```tree

├── kaas
│   ├── Makefile
│   ├── Dockerfile
│   ├── plugin.yaml
│   ├── go.mod
│   ├── go.sum
│   ├── main_test.go
│   ├── README.md
│   ├── k8s-test-1.go
│   ├── k8s-test-2.go
│   └── k8s-test-<n>.go

```


## Pros and Cons of Different Approaches

There are two potential approaches for writing Kubernetes conformance tests executable by Sonobuoy.
Here we discuss the pros and cons of these two approaches.
Using Sonobuoy would not only relaie on writing tests in go.
There is more than one option to implement tests as Sonobuoy plugin.
Two of them might be of most interst to us:


#### _Option 1_ Write Python scripts for tests

Apply the already implemented confomrance test python scripts and also continue
writing future tests in python. Therefore, we would need to write a wrapper
around the conformance tests scripts in order to make them executable as a
sonobuoy plug in. This includes  the collection of the test results and the
Generateion of the "done" file at the end. Furthermore, we could do this with a
simple handler that executes each test script in a sequential order. All of
this can then be stored in a container image and uploaded to a container
registry that Sonobuoy can use within the k8s-cluster-api-provider.

This approach also leaves it free to decide on which testframework to use for with python.


#### _Option 2_ Write go.scripts for the tests

Writing our tests in go using the [plugin-helper](https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/plugin-helper)
as skeleton for developing tests.
More percilcy we could make use of the [e2e-skeleton example](https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/examples/e2e-skeleton)
provided by Sonobuoy.
This example is based on the ussage of the [Kubernetes e2e-framework](https://github.com/kubernetes-sigs/e2e-framework).


PROS:
- [Kubernetes e2e-framework](https://github.com/kubernetes-sigs/e2e-framework) well definde framework who handels Resource creation and deletion
- official framework provided by Kubernetes-sigs


CONS

- compared to Python, Go is a less common programming language
- slightly more effort for development (the example runs only in sonobuoy and not standalone)


### Provide Sonobuoy plug in image

#### _Option 1_ github container registry

Make the image available via the container registry on github.

#### _Option 2_ local image upload

Build the image locally on the "clusterctl admin control node" and then manually upload it to the Kubernetes cluster under test.

## Open questions:

* set up CI/CD using k8s-clustster-api-provider to back tests conformance tests aggainst it?






