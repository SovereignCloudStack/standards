# SCS kaas Sonobuoy testsuite and K8s e2e-test-framework

This directory holds all conformance tests that aim to validate the scs kaas infrastructure

## Sonobuoy plugin description

> NOTE: There is a Sonobuoy blog post walking through this plugin, its benefits, and how to use it. See: <https://sonobuoy.io/plugin-starter/>

### Custom End-to-End (E2E) Tests

This plugin is intended as a skeleton to implement custom tests in Kubernetes.

The benefits of using this plugin instead of starting from scratch are:

* automatically comes with the [e2e-test-framework](https://github.com/kubernetes-sigs/e2e-framework) imported/configured
* includes basic examples, so you don't have to look up boilerplate code
* comes with a Dockerfile and plugin.yaml, meaning there is less overhead to getting started
* long-time support, since the e2e-test-framework and Sonobuoy are still actively maintained

### How to use this plugin

1) Write tests (using the main_test.go as a starting point)
2) Run ./build.sh to build the image and push it to your registry
3) `sonobuoy run -p plugin.yaml` to run your own plugin

## Sonobuoy usage for development of tests

For test development with Sonobuoy, [KinD](https://kind.sigs.k8s.io/) is used as a test cluster.

* (Optional): check if all prerequisites for the development are met and create a `KinD` test cluster

    ```bash
    make dev-prerequests
    make dev-setup
    ```

1. Set environment variables

    ```bash
    export IMAGE_VERSION_TAG="dev"
    export K8S_HOST=<kind-cluster-ip>
    export K8S_PORT=<kind-cluster-port>
    ```

2. Build the image and upload it to the KinD cluster

    ```bash
    make dev-build
    ```

3. Execute the Sonobuoy plugin

    ```bash
    make dev-run
    ```

   This launches the Sonobuoy plugin on the KinD cluster in the background.
   If you want to see the current status of the plugin you can do so by:

    ```bash
    sonobuoy status
    ```

4. Retrieve the Results

   Once Sonobuoy is done running the plugin you can retrieve the results as following:

    ```bash
    make dev-result
    ```

5. Clean the Sonobuoy testcase from the KinD cluster

   Cleaning up all Kubernetes resources which were placed on the KinD cluster by sonobuoy

    ```bash
    make dev-clean
    ```

6. Purge everything

   Deleting the KinD cluster

    ```bash
    make dev-purge
    ```
