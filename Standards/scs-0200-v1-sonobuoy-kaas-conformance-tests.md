---
title: Sonobuoy - KaaS conformance test framework
type: Decision Record
status: Draft
track: KaaS
---

## Introduction - Motivation

With the [k8s-cluster-api-provider][k8s-api], the SCS provides a tool to generate
and manage k8s clusters on top of its OpenStack IAAS infrastructure. As part of
the application, [Sonobuoy][sonobuoy] is used as a test suite to execute the
official [Kubernetes e2e tests][k8s-e2e-tests]. Future and existing conformance
tests derived from SCS standards are perhaps part of these tests and could therefore
be provided by running the integrated [Sonobuoy e2e test plugin][e2e test plugin].

Apart from running the Kubernetes e2e tests, Sonobuoy also allows users to write
their own tests and apply them as a self-managed [plugin][sonobuoy-plugin-docu].
All tests not provided by the [e2e test plugin][e2e test plugin] could therefore
be written by the respective SCS teams responsible for the standards or tests and
then be made executable with Sonobuoy. Hence, Sonobuoy could provide both a pre-done
test suite and a framework to write additional conformance tests required for SCS.

### Short Sonobuoy Introduction

The main objective of [Sonobuoy plugins][sonobuoy-plugin-docu] is to present test
results in a consolidated way. To do this, Sonobuoy integrates the test into a pod,
which is then applied to the K8s cluster under test. A Sonobuoy worker supervises
this pod and forwards all test results to the aggregator module. It does this by
waiting for a specific "Done" file to be created. Once this file is recognized,
the worker forwards the results to the aggregator, using a predefined location
for the results file within a folder, as seen in following image:
![image search api](https://sonobuoy.io/img/plugin-contract.png)

In order to use the existing conformance tests as a Sonobuoy plugin, a wrapper
around the individual test scripts would be required. This wrapper would need to
have the following effects:

* Gathers all test results and provides them in the results file
* Run tests in sequence and signal the worker when it is finished by generating a "done" file

Apart from providing the test results, a plugin container must also forward the
status of each test by setting a status flag in the results file.
Additionally, the tests would need to be able to run inside a pod in the K8s cluster under test.

## Design Considerations

There are different approaches to create a Sonobuoy plugin, which are discussed
below in order to find a best practice for the SCS project. The documented approaches
show one example each in order to give a better representation to the reader.

Sonobuoy provides plugin examples in the repository <https://github.com/vmware-tanzu/sonobuoy-plugins>, which are referenced throughout this section.

### _Option 1_ Go approach 1: Pick framework from the Sonobuoy plugin examples

The seemingly most interesting plugin is the [e2e-skeleton][e2e-skel], which uses
the [kubernetes-sigs/e2e-framework][e2e-frame]. The [kubernetes-sigs/e2e-framework][e2e-frame]
is a stand-alone project that is separate from the official [Kubernetes e2e tests][k8s-e2e-tests].
The framework provides proper documentation as well as helper functions that abstract
client functionalities, similar to those found in "kubernetes/kubernetes/test/e2e/framework" repository.

As mentioned in the [motivation][e2e-frame-motivation] of the [e2e-framework][e2e-frame],
the project was created to circumvent the disadvantages of [kubernetes' own e2e-tests][k8s-e2e-tests],
which are described in more detail in the [goals][e2e-frame-goals].

PROS:

* arguments in favor of this framework can also be found under the [goals description][e2e-frame-goals] of the documentation
* [e2e-framework][e2e-frame] is a well defined framework, that allows the handling of resource creation and deletion
* official framework provided by "Kubernetes-sigs"

CONS:

* compared to Python, Go is a less common programming language
* arguments not in favor of this framework can also be derived from the [Non-Goals][e2e-frame-nongoals] description of the documentation:
  * "no responsibility for bootstrapping or the execution of the tests themselves" can be ignored, as this is partly taken over by Sonobuoy
  * "no mock or fake cluster components" can be ignored, since the e2e tests of SCS should be used to test real clusters and their functionality
  * for this test procedure, the Sonobuoy e2e plugin should be run in addition to the SCS kaas conformance tests

> proof of concept: `../Tests/kaas/kaas-sonobuoy-go-example-e2e-framework/`

### _Option 2_ Go approach 2: Reuse the kubernetes own e2e test infrastructure and framework

The existing Sonobuoy e2e plugin already provides a vast number of tests that could
be adapted or reused for the SCS project.

If these e2e tests are to be reused in a customized structure, a framework like [ginkgo][ginkgo]
must be used as it is used by the Kubernetes e2e test infrastructure.
This could use the implementation of the build process responsible for the Docker
image containing the e2e tests. The setup could be copied from [kubernetes/test/conformance/image][conformance-image]
and adapted to the projects requirements. The mentioned build process must use the
files of the following directories from the Kubernetes repository:

* [kubernetes/cluster](https://github.com/kubernetes/kubernetes/tree/master/cluster)
* [kubernetes/test/e2e/framework](https://github.com/kubernetes/kubernetes/tree/master/test/e2e)
* [kubernetes/test/conformance/image/go-runner](https://github.com/kubernetes/kubernetes/tree/master/test/conformance/image/go-runner)
* [kubernetes/hack/conformance](https://github.com/kubernetes/kubernetes/tree/master/hack/conformance)
* [kubernetes/hack/make-rules](https://github.com/kubernetes/kubernetes/tree/master/hack/make-rules)

PROS:

* [Kubernetes' own e2e tests][k8s-e2e-tests] already provide a vast amount of examples, which could be reused to develop specific SCS tests
* compared to _option 1_, the [non-goals][e2e-frame-nongoals] of the [e2e-framework][e2e-frame] can be seen as the advantages of using [Kubernetes' own e2e-tests][k8s-e2e-tests].

CONS:

* not easy to implement, as we would have to copy part of the Kubernetes repository and track the changes from the upstream
* according to [README.md](https://github.com/kubernetes/kubernetes/tree/master/cluster#readme), part of it seems to be outdated and might change with a future version
  * compared to _option 1_, the [goals][e2e-frame-goals] of the [e2e-framework][e2e-frame] can be seen as the disadvantages of using [Kubernetes' own e2e-tests][k8s-e2e-tests].

> TODO: provide proof of concept: _kaas-sonobuoy-go-example-k8s-e2e_

#### _Option 3_ Write Python scripts for tests

Sonobuoy makes it possible to write tests in Python and execute them like other
tests in a pod on the K8s cluster. It would therefore be possible to keep on writing
conformance tests in Python.

This option would require a wrapper in order to make the tests scripts executable
as Sonobuoy plugins. This wrapper, as mentioned earlier, would need to capture
the collection of test results as well as the generation of the "Done" file after
the test execution is finished. This could be managed by executing each test script
in a sequential order.

The wrapper as well as the python tests and test framework could then be stored
in a container image and uploaded to a registry in order to be usable by Sonobuoy
within the k8s-cluster-api-provider.

This approach also leaves the decision open as to which test framework should be
used for Python, which should be decided in a secondary Decision Record.

> proof of work: `../Tests/kaas/k8s-default-storage-class`

PROS:

* continue using the already available Python tests
  * only a small number of tests is implemented thus far

CONS:

* no "native" support in Sonobuoy, a wrapper is needed
* decision for a framework is still not done

## Pros and Cons of Different Approaches

### Providing Sonobuoy plug in image

There are two potential approaches for building the Sonobuoy images.
They are completely independent of which of the above-mentioned frameworks is selected.
Here we discuss the pros and cons of these two approaches.

#### _Option 1_ GitHub container registry

Make the image available via the container registry on GitHub.
Hence we would need to apply a CI/CD job to build the images.

PROS

* The tests do not have to be created each time before usage.

CONS

* _?_

#### _Option 2_ local image upload

Create the image locally on the "clusterctl admin control node" and then upload
it manually to the Kubernetes cluster under test.

PROS

* _?_

CONS

* To be able to use the tests, you always have to build them first

## Decision

The KaaS conformance test MUST be provided as a test suite holding the
test cases for the Kubernetes clusters to be checked.
Furthermore, the test cases themselves MUST be wrapped by a test framework to:

* Handle the creation and deletion of resources
* Collect and present results
* Consolidate redundant code across test cases
* Support the creation of test cases through predefined structures

As with the [k8s-cluster-api-provider][k8s-api] the SCS provides a tooling to generate
its KaaS infrastructure. Part of the [k8s-cluster-api-provider][k8s-api] is the usage
of Sonobuoy as a test suite to execute the [Kubernetes own e2e tests][k8s-e2e-tests].
Investigating those e2e test lead to the conclusion that they are not always reusable.
The main purpose of Kubernetes own e2e tests is to test the functionality of
the Kubernetes code itself and not the resources and setup of a specific KaaS infrastrcture
as it is the aim of the SCS KaaS conformance test.

However considering that the SCS has an ongoing process of defining standards and
implementing test cases to check their compliance. In some cases future standards
might already be covored by the e2e test inside the Kubernetes repository.
Hence before writing tests, a developer SHOULD check the kubernetes e2e tests for
existing test cases that might cover conformance of a standard he is currently
working on.

As described above, Sonobuoy offers the possibility to generate custom plugins
that provide self-created test cases. Therefore, future conformance tests MUST
be able to be executed by Sonobuoy by wrapping them in a Sonobuoy plugin.
Moreover, three options for the implementation of the SCS KaaS compliance test
cases are described above so that it can be decided in this decision record which
options should be used.

As a first decision, "_Option 2_ Go Approach 2: Reuse Kubernetes' own e2e test infrastructure and framework"
is the least viable, as it would mean copying almost all of the files used for
the Kubernetes e2e tests. This framework is closely linked to the development of
the Kubernetes code. Therefore, changes to its structure mainly concerns its use
within the Kubernetes repository itself and not its use for other parties.
Changes in the framework cloud have a greater impact on our side as they are
predictable. The development effort gained by reusing the many examples could be
outweighed by the effort that might be invested in the future to adapt our tests
to corresponding framework changes.

This leaves "_Option 1_ Go approach 1: Pick framework from the Sonobuoy plugin examples"
and "_Option 3_ Write Python scripts for tests" as methods for implementing test cases.
Both have their advantages, so it could also be considered to use both and thus
generate two Sonobuoy plugins.

## Documents

[k8s-e2e-tests]: https://github.com/kubernetes/kubernetes/tree/master/test/e2e
[sonobuoy]: https://sonobuoy.io/
[sonobuoy-plugin-docu]: https://sonobuoy.io/docs/v0.57.0/plugins/
[e2e test plugin]: https://sonobuoy.io/docs/main/e2eplugin/
[k8s-api]: https://github.com/SovereignCloudStack/k8s-cluster-api-provider
[e2e-skel]: https://github.com/vmware-tanzu/sonobuoy-plugins/tree/main/examples/e2e-skeleton
[e2e-frame]: https://github.com/kubernetes-sigs/e2e-framework
[e2e-frame-motivation]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#motivations
[e2e-frame-goals]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#goals
[e2e-frame-nongoals]: https://github.com/kubernetes-sigs/e2e-framework/blob/main/docs/design/README.md#non-goals
[ginkgo]: https://onsi.github.io/ginkgo/
[conformance-image]: https://github.com/kubernetes/kubernetes/tree/master/test/conformance/image
