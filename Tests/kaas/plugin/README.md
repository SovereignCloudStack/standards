# Plugin for provisioning k8s clusters and performing conformance tests on these clusters

## Development environment

### Requirements

* [docker](https://docs.docker.com/engine/install/)
* [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

### Setup for Development

1. **Generate python 3.10 env**

   ```bash
   sudo apt-get install python3.10-dev
   virtualenv -p /usr/bin/python3.10 venv
   echo "*" >> venv/.gitignore
   source venv/bin/activate
   (venv) curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
   (venv) python3.10 -m pip install --upgrade pip
   (venv) python3.10 -m pip --version

   ```

2. **Install dependencies:**

   ```bash
   (venv) pip install pip-tools
   (venv) pip-compile requirements.in
   (venv) pip-sync requirements.txt
   ```

3. **Create a Cluster**

   To create a cluster, run:

   ```bash
   (venv) python run_plugin.py create <plugin-name> ../clusterspec.yaml
   ```

## Setting up and running the cluster-stacks plugin

This section covers how to configure and run the `cluster-stacks` plugin to provision Kubernetes clusters and perform conformance tests.

### Requirements for cluster-stacks plugin

In addition to the core requirements, ensure the following are set up:

* An **OpenStack** environment configured and accessible.
* A `clouds.yaml` file defining OpenStack credentials and endpoints.
* An installing the envsubst via this command:
  ```bash
  GOBIN=/tmp go install github.com/drone/envsubst/v2/cmd/envsubst@latest
  ```

### Environment Variables

Before running the `cluster-stacks` plugin, you need to set up the following environment variable:

- **GIT_ACCESS_TOKEN**: This token is required for Git operations, especially if your repository is private.

To set the `GIT_ACCESS_TOKEN`, run the following command in your terminal:

```bash
export GIT_ACCESS_TOKEN=<your-github-token>
```

### Configuring clusterspec.yaml file

The `clusterspec.yaml` file is used to set parameters for creating a Kubernetes cluster with the `cluster-stacks` plugin. This file allows you to specify details related to the cluster-stack, Git integration, and cluster configurations.

### Mandatory Parameter

The only mandatory parameter in `clusterspec.yaml` is `clouds_yaml_path` field, which points to the `clouds.yaml` file for OpenStack. If other parameters are omitted, the default values will be used.

### Optional Parameters

You can include additional parameters in `clusterspec.yaml` to customize the cluster setup. These optional parameters are grouped below by their category.

#### Cluster-Stack Related Parameters

These parameters configure specific settings for the cluster-stack:

```yaml
cs_name: <cs_name>                  # Default: "scs"
cs_k8s_version: <cs_k8s_version>    # Default: "1.29"
cs_version: <cs_version>            # Default: "v1"
cs_channel: <cs_channel>            # Default: "stable"
cs_cloudname: <cs_cloudname>        # Default: "openstack"
```

#### Git-Related Parameters

The [Cluster Stack Operator](https://github.com/sovereignCloudStack/cluster-stack-operator/) (CSO) utilizing the [Cluster Stack Provider OpenStack](https://github.com/SovereignCloudStack/cluster-stacks/tree/main/providers/openstack) (CSPO) must be directed to the Cluster Stacks repository housing releases for the OpenStack provider. Modify the following parameters if you wish to redirect CSO and CSPO to an alternative Git repository

```yaml
git_provider: <git_provider>      # Default: "github"
git_org_name: <git_org_name>      # Default: "SovereignCloudStack"
git_repo_name: <git_repo_name>    # Default: "cluster-stacks"
```

#### Cluster Parameters

Set these parameters to customize the configuration for your cluster.

```yaml
cs_cluster_name: <cs_cluster_name>              # Default: "cs-cluster"
cs_pod_cidr: <cs_pod_cidr>                      # Default: "192.168.0.0/16"
cs_service_cidr: <cs_service_cidr>              # Default: "10.96.0.0/12"
cs_external_id: <cs_external_id>                # Default: A generated UUID
cs_k8s_patch_version: <cs_k8s_patch_version>    # Default: "6"
```
