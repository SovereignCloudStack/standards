# SCS kaas sonobuoy testsuie and k8s e2e-test-framework framework

This directory holds all conformance tests that aim to validate the scs kaas infrastructure


## From Sonobuoy: Plug description

> NOTE: There was a Sonobuoy blog post walking through this plugin, its benefits, and how to use it. See: https://sonobuoy.io/plugin-starter/

### Custom End-To-End (E2E) Tests

This plugin is meant as a skeleton for you to grab and run with to implement your
own custom tests in Kubernetes.

The benefits of using this plugin instead of starting from scratch:
 - Automatically comes with the [e2e-test-framework](https://github.com/kubernetes-sigs/e2e-framework) imported/configured
 - Includes basic examples so you don't have to look up basic boilerplate
 - Automatically comes with a Dockerfile and plugin.yaml so there is less overhead to getting started
 - Will get support as the e2e-test-framework and Sonobuoy evolve to get the best features supported by default

### How to use this plugin

- Write tests (using main_test.go as a jumping off point)
- Run ./build.sh to build the image and push it to your registry
- `sonobuoy run -p plugin.yaml` to run your own plugin


## sonobuoy usage for development of tests

The development is based on the useage of [kind](https://kind.sigs.k8s.io/) as a test cluster.


* (Optional): check if all pre requests for development are met and create a kind test cluster

    ```
    make dev-prerequests
    make dev-setup
    ```

1. Set enviornment variables

    ```
    export IMAGE_VERSION_TAG="dev"
    export K8S_HOST=<kind-cluster-ip>
    export K8S_PORT=<kind-cluster-port>
    ```


2. Build the image and upload it to the kind cluster

    This rule

    ```
    make dev-build
    ```

3. Execute the sonobuoy plugin

    ```
    make dev-run
    ```
    This lunches the sonobuoy plugin on the kind cluster in the background
    If you want to see the current status of the plugin you can do so by:
    ```
    sonobuoy status
    ```

4. Retrieve the Results

    Once sonobuoy is done running the plug in you can retrieve the results as following:

    ```
    make dev-result
    ```

5. Clean the Sonobuoy testcase form the kind cluster

    Cleaning up all Kubernetes resources which were placed on the kind cluster by sonobuoy

    ```
    make dev-clean
    ```

6. Purge everything

    Deleting the kind cluster

    ```
    make dev-purge
    ```


