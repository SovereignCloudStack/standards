import os
import subprocess
import base64
import time

from pytest_kind import KindCluster
from interface import KubernetesClusterPlugin


class PluginClusterStacks(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of cluster-stacks
    """
        
    def _create_cluster(self):
        # Step 1: Create the Kind cluster
        self.cluster = KindCluster(
            self.cluster_name
        )
        self.cluster.create()
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())

        # Step 2: Set environment variables
        os.environ['CLUSTER_TOPOLOGY'] = 'true'
        os.environ['EXP_CLUSTER_RESOURCE_SET'] = 'true'
        os.environ['EXP_RUNTIME_SDK'] = 'true'
        os.environ['KUBECONFIG'] = self.kubeconfig

       # Step 3: Initialize clusterctl with OpenStack as the infrastructure provider
        try:
            subprocess.run(
                ["clusterctl", "init", "--infrastructure", "openstack"],
                check=True
            )
            print("clusterctl init completed successfully with OpenStack provider.")
        except subprocess.CalledProcessError as error:
            print(f"Error during clusterctl init: {error}")
            raise

        # Step 4: Set Git-related environment variables
        os.environ['GIT_PROVIDER_B64'] = base64.b64encode(b'github').decode('utf-8')
        os.environ['GIT_ORG_NAME_B64'] = base64.b64encode(b'SovereignCloudStack').decode('utf-8')
        os.environ['GIT_REPOSITORY_NAME_B64'] = base64.b64encode(b'cluster-stacks').decode('utf-8')

        # Retrieve the Git token from environment variables
        git_access_token = os.getenv('GIT_ACCESS_TOKEN')
        if git_access_token:
            # Encode the Git access token and set it as an environment variable
            encoded_token = base64.b64encode(git_access_token.encode('utf-8')).decode('utf-8')
            os.environ['GIT_ACCESS_TOKEN_B64'] = encoded_token
        else:
            print("Error: GIT_ACCESS_TOKEN environment variable not set.")

        print("Waiting for webhook services to become ready...")
        time.sleep(60)

        # Step 5: Download and apply the infrastructure components YAML with envsubst and kubectl
        download_and_apply_cmd_cso = (
            "curl -sSL "
            "https://github.com/SovereignCloudStack/cluster-stack-operator/releases/latest/download/cso-infrastructure-components.yaml"
            " | /tmp/envsubst | kubectl apply -f -"
        )
        # Todo: USE something else like envsubst in python?
        download_and_apply_cmd_cspo = (
            "curl -sSL "
            "https://github.com/SovereignCloudStack/cluster-stack-provider-openstack/releases/latest/download/cspo-infrastructure-components.yaml"
            " | /tmp/envsubst | kubectl apply -f -"
        )
        try:
            subprocess.run(download_and_apply_cmd_cso, shell=True, check=True)
            subprocess.run(download_and_apply_cmd_cspo, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            print(f"Error during downloading and applying YAML: {error}")
            raise

        # Step 6: Define a namespace for a tenant (CSP/per tenant) and get pat to clouds.yaml file from env variable
        cs_namespace = os.getenv("CS_NAMESPACE", "default")
        clouds_yaml_path = os.getenv("CLOUDS_YAML_PATH")

        if not clouds_yaml_path:
            raise ValueError("CLOUDS_YAML_PATH environment variable not set.")

        # Step 7: Deploy CSP-helper chart
        helm_command = (
            f"helm upgrade -i csp-helper-{cs_namespace} "
            f"-n {cs_namespace} --create-namespace "
            "https://github.com/SovereignCloudStack/openstack-csp-helper/releases/latest/download/openstack-csp-helper.tgz "
            f"-f {clouds_yaml_path}"
        )

        try:
            subprocess.run(helm_command, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            print(f"Error during Helm upgrade: {error}")
            raise

        # Step 8: Handle env variables for clusterstack.yaml file
        os.environ['CS_NAME'] = os.getenv('CS_NAME', 'scs')
        os.environ['CS_K8S_VERSION'] = os.getenv('CS_K8S_VERSION', '1.29')
        os.environ['CS_VERSION'] = os.getenv('CS_VERSION', 'v1')
        os.environ['CS_CHANNEL'] = os.getenv('CS_CHANNEL', 'stable')
        os.environ['CS_CLOUDNAME'] = os.getenv('CS_CLOUDNAME', 'openstack')
        os.environ['CS_SECRETNAME'] = os.getenv('CS_SECRETNAME', os.environ['CS_CLOUDNAME'])

        # Todo: How to handle sleep to wait until all cso components are ready
        time.sleep(30)

        # Step 9: Create Cluster Stack definition (CSP/per tenant)
        clusterstack_yaml_path = "clusterstack.yaml"
        try:
            subprocess.run(
                f"envsubst < {clusterstack_yaml_path} | kubectl apply -f -",
                shell=True,
                check=True
            )
            print(f"Successfully applied {clusterstack_yaml_path}.")
        except subprocess.CalledProcessError as error:
            print(f"Error during kubectl apply: {error}")
            raise

        # Step 10: Handle env variables for cluster.yaml file
        os.environ['CS_CLUSTER_NAME'] = os.getenv('CS_CLUSTER_NAME', 'cs-cluster')
        os.environ['CS_POD_CIDR'] = os.getenv('CS_POD_CIDR', '192.168.0.0/16')
        os.environ['CS_SERVICE_CIDR'] = os.getenv('CS_SERVICE_CIDR', '10.96.0.0/12')
        os.environ['CS_EXTERNAL_ID'] = os.getenv('CS_EXTERNAL_ID', 'ebfe5546-f09f-4f42-ab54-094e457d42ec') # gx-scs
        os.environ['CS_K8S_PATCH_VERSION'] = os.getenv('CS_K8S_PATCH_VERSION', '6')

        # Construct CS_CLASS_NAME
        cs_name = os.getenv('CS_NAME')
        cs_k8s_version = os.getenv('CS_K8S_VERSION').replace('.', '-')  # Replace dots with dashes
        cs_version = os.getenv('CS_VERSION')
        os.environ['CS_CLASS_NAME'] = f"openstack-{cs_name}-{cs_k8s_version}-{cs_version}"

        # Step 11: Create the workload cluster resource (SCS-User/customer)
        cluster_yaml_path = "cluster.yaml"
        try:
            subprocess.run(
                f"envsubst < {cluster_yaml_path} | kubectl apply -f -",
                shell=True,
                check=True
            )
            print(f"Successfully applied {cluster_yaml_path}.")
        except subprocess.CalledProcessError as error:
            print(f"Error during kubectl apply: {error}")
            raise

        # Step 12: Get kubeadmcontrolplane name
        max_retries = 6
        delay_between_retries = 10  # seconds        
        for attempt in range(max_retries):
            try:
                kcp_command = "kubectl get kubeadmcontrolplane -o=jsonpath='{.items[0].metadata.name}'"
                kcp_name = subprocess.run(kcp_command, shell=True, check=True, capture_output=True, text=True)
                kcp_name_stdout = kcp_name.stdout.strip()  # Remove any leading/trailing whitespace
                if kcp_name_stdout:
                    print(f"KubeadmControlPlane name: {kcp_name_stdout}")
                    break
            except subprocess.CalledProcessError as error:
                print(f"Error getting kubeadmcontrolplane name: {error}")
            # Wait before retrying
            time.sleep(delay_between_retries)
        else:
            raise RuntimeError("Failed to get kubeadmcontrolplane name")

        # Step 13: Wait for kubeadmcontrolplane to be available
        try:
            wait_command = f"kubectl wait kubeadmcontrolplane/{kcp_name.stdout.strip()} --for=condition=Available --timeout=300s"
            subprocess.run(wait_command, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for kubeadmcontrolplane to be available: {error}")

        # Step 14: Get kubeconfig of the workload k8s cluster
        try:
            cs_cluster_name = os.environ['CS_CLUSTER_NAME']
            kubeconfig_filename = f"kubeconfig-{cs_cluster_name}"
            kubeconfig_command = f"clusterctl get kubeconfig {cs_cluster_name} > ./{kubeconfig_filename}"
            subprocess.run(kubeconfig_command, shell=True, check=True)
            print(f"Kubeconfig of the workload k8s cluster has been saved to {kubeconfig_filename}.")
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error getting kubeconfig of the workload k8s cluster: {error}")

        # Step 15: Wait for clusteraddons resource to become ready
        try:
            kubeconfig_command = f"kubectl wait clusteraddons/cluster-addon-{cs_cluster_name} --for=condition=Ready --timeout=300s"
            subprocess.run(kubeconfig_command, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for clusteraddons to be ready: {error}")

        # Step 16: Wait for all system pods in the workload k8s cluster to become ready
        try:
            wait_pods_command = (
                f"kubectl wait -n kube-system --for=condition=Ready --timeout=300s pod --all --kubeconfig {kubeconfig_filename}"
            )
            subprocess.run(wait_pods_command, shell=True, check=True)
            print("All system pods in the workload Kubernetes cluster are ready.")
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for system pods to become ready: {error}")

    def _delete_cluster(self):
        # Todo: Delete cluster created by cluster-stacks on top of OpenStack with some timeout
        self.cluster = KindCluster(self.cluster_name)
        self.cluster.delete()
