---
title: Sonobuoy kaas conformance tests framework
type: Decision Record
status: Draft
track: KaaS
---

## Introduction - Motivation

With the [k8s-cluster-api-provider][k8s-api] the SCS provides a tooling to generate and manage k8s cluster on top of it's OpenStack IAAS infrastructure.
Part of this tool is the usage of [Sonobuoy][sonobuoy] as a test suit tool to execute the official [kubernetes e2e tests][k8s-e2e-tests].
Future conformance tests derived from standards could already be part of the Kubernetes e2e tests and could be provided by running the integrated Sonobuoy [e2e test plugin][e2e test plugin].

But apart from running the Kubernetes e2e tests Sonobuoy also allows to write your own tests and apply it as a self created [plugin][sonobuoy-plugin-docu].
So for all tests not already provided by the [e2e test plugin][e2e test plugin] we should first write our own tests and second make them executable with Sonobuoy.
Hence it would be useful to also use Sonobuoy as a test suit combined with a framework for writing SCS conformance tests.

### Short Sonobuoy Introduction

The main objective of [Sonobuoy plugins][sonobuoy-plugin-docu] is to present test results and their status in a consolidated way.
This is essentially done by applying the test to a pod that is applied to the k8s cluster under test.
A Sonobuoy worker then supervises this pod and forwards all test results to the aggregator.
It does this by waiting for a "done file" to be created. Once this file is created, it forwards the results to the aggregator, using a predefined location of the results file within the done folder, as seen in following image:
![image search api](https://sonobuoy.io/img/plugin-contract.png)

Therefore, in order to apply the conformance tests as a plugin, we need a tooling/wrapper/framework around the individual test scripts that:

* Gathers all test results and provides them in the results file.
* Run tests in sequence and signal the worker when it is finished by writing the "done file".

Apart from providing the test results, a plugin container must also pass on the status of each test by setting the status flag in the results file.
In addition, to run the tests as a Sonobuoy plugin, we need to create an image that can be run inside the k8s cluster under test.

## Design Considerations

Among the different ways to create a Sonobuoy plugin, there are three potential approaches that might work best for us.
These are described in more detail below, where we discuss the pros and cons of each approach.
One of these three approaches must be chosen for implementation.
For the purposes of the investigation and the preparation of this decision record, there are examples(proof of work) for each different approach.

#### _Option 1_ go approach [1]: Pick framework from the Sonobuoy plugin examples

Sonobuoy provides plugin examples in the following repository: [https://github.com/vmware-tanzu/sonobuoy-plugins][sonobuoy-plugins-repo].
The most suitable plugin for us is the [e2e-skeleton][e2e-skel], which uses the [kubernetes-sigs/e2e-framework][e2e-frame].
The [kubernetes-sigs/e2e-framework][e2e-frame] is a stand-alone project that is separate from the official [kubernetes e2e tests][k8s-e2e-tests].
It is suitable for us to make us of it, as it provides a properly documented framework.
In addition, it contains helper functions that abstract client go functions similar to those in the kubernetes/kubernetes/test/e2e/framework repository
As mentioned in the [motivation][e2e-frame-motivation] of the [e2e-framework][e2e-frame], it was created to circumvent the disadvantages of
[kubernetes' own e2e-tests][k8s-e2e-tests], which are described in more detail in the [goals][e2e-frame-goals].

PROS:
- Arguments in favor of this framework can also be found under the [goals description][e2e-frame-goals] of the documentation
- [e2e-framework][e2e-frame] is a well defined framework who allows the handling of resources creation and deletion
- official framework provided by Kubernetes-sigs

CONS:
- compared to Python, Go is a less common programming language
- arguments not in favor of this framework can also be derived from the [Non-Goals][e2e-frame-nongoals] description of the documentation:
  - However, the point "No responsibility for bootstrapping or the execution of the tests themselves" can be ignored, as this is partly taken over by Sonobuoy.
  - Also the point "no mock or fake cluster components" can be ignored as we want to use the e2e tests to test the Kubernetes cluster environment itself and not the functionality of the Kubernetes source code.
    - For this test procedure we should run the Sonobuoy e2e plugin in addition to the SCS kaas conformance tests.


> proof of work: [kaas-sonobuoy-go-example-e2e-framework](../Tests/kaas/kaas-sonobuoy-go-example-e2e-framework/)


#### _Option 2_ go approach [2]: Reuse the kubernetes own e2e test infrastructure and framework

As mentioned above, Sonobuoy already provides [Kubernetes own e2e tests][k8s-e2e-tests] as a plugin.
These tests contain a vast number of examples that we could reuse and adapt to our needs.
For the implementation, we could reuse the e2e tests and the framework in an adapted structure.
More precisely this would lead us to make use of the test framework [ginkgo][ginkgo].
The entry point for the implementation would be the build process of the Dockerimage which contains
the e2e tests. Therefore we could copy the setup of the build process from
[kubernetes/test/conformance/image][conformance-image] and adapt it to our requirements.
The build process requires some files from the kubernetes repository.
More precisely from:
  - [kubernetes/cluster](https://github.com/kubernetes/kubernetes/tree/master/cluster)
  - [kubernetes/test/e2e/framework](https://github.com/kubernetes/kubernetes/tree/master/test/e2e)
  - [kubernetes/test/conformance/image/go-runner](https://github.com/kubernetes/kubernetes/tree/master/test/conformance/image/go-runner)


PROS:
   - The [Kubernetes' own e2e tests][k8s-e2e-tests] already provide a vast amount of examples from which we can develop our own tests
   - Compared to _option 1_, the [non-goals][e2e-frame-nongoals] of the [e2e-framework][e2e-frame] can be seen as the advantages of using [Kubernetes' own e2e-tests][k8s-e2e-tests].


CONS:
  - not easy to implement, as we would have to copy part of the Kubernetes repository and track the changes there as well.
  - According to [README.md](https://github.com/kubernetes/kubernetes/tree/master/cluster#readme), part of it seems to be outdated and might change in the future.
   - Compared to _option 1_, the [goals][e2e-frame-goals] of the [e2e-framework][e2e-frame] can be seen as the disadvantages of using [Kubernetes' own e2e-tests][k8s-e2e-tests].


> TODO: provide proof of work: _kaas-sonobuoy-go-example-k8s-e2e_


#### _Option 3_ Write Python scripts for tests

Apply the already implemented conformance test python scripts and also continue
writing future tests in python. Therefore, we would need to write a wrapper
around the conformance tests scripts in order to make them executable as a
Sonobuoy plug in. This includes  the collection of the test results and the
Generation of the "done" file at the end. Furthermore, we could do this with a
simple handler that executes each test script in a sequential order. All of
this can then be stored in a container image and uploaded to a container
registry that Sonobuoy can use within the k8s-cluster-api-provider.

This approach also leaves the decision open as to which test framework should be
used for Python. Hence, if we follow this approach, we need to create a
framework of our own.

> proof of work: [k8s-default-storage-class](../Tests/kaas/k8s-default-storage-class)


PROS:
    - We can continue to use the current Python scripts
        - However, only 2 scripts have been implemented so far. Rewriting them in Go should be a feasible task.

CONS:
    - We would need to write our own test framework


## Pros and Cons of Different Approaches


### Provide Sonobuoy plug in image

There are two potential approaches for building the Sonobuoy images.
They are completely independent of which of the above-mentioned frameworks is selected.
Here we discuss the pros and cons of these two approaches.

#### _Option 1_ GitHub container registry

Make the image available via the container registry on GitHub.
Hence we would need to apply a CI/CD job to build the images.


PROS
  - The tests do not have to be created each time before usage.

CONS
  - _None_

#### _Option 2_ local image upload

Create the image locally on the "clusterctl admin control node" and then upload it manually to the Kubernetes cluster under test.

PROS
  - _None_

CONS
  - To be able to use the tests, you always have to build them first


[k8s-e2e-tests]: https://github.com/kubernetes/kubernetes/tree/master/test/e2e
[sonobuoy]: https://sonobuoy.io/
[sonobuoy-plugins-repo]: https://github.com/vmware-tanzu/sonobuoy-plugins
[sonobuoy-plugin-docu]: https://sonobuoy.io/docs/v0.57.0/plugins/)
[e2e test plugin]: https://sonobuoy.io/docs/main/e2eplugin/
[k8s-api]: https://github.com/SovereignCloudStack/k8s-cluster-api-provider
[e2e-skel]: https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/examples/e2e-skeleton
[e2e-frame]: https://github.com/kubernetes-sigs/e2e-framework
[e2e-frame-motivation]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#motivations
[e2e-frame-goals]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#goals
[e2e-frame-nongoals]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#non-goals
[ginkgo]:https://onsi.github.io/ginkgo/
[conformance-image]:https://github.com/kubernetes/kubernetes/tree/master/test/conformance/image

