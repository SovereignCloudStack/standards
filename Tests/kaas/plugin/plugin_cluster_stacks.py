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

    def __init__(self, config):
        self.config = config
        self.cs_cluster_name = os.getenv('CS_CLUSTER_NAME', 'cs-cluster')
        self.kubeconfig_cs_cluster_filename = f"kubeconfig-{self.cs_cluster_name}"

        # Git-related variables
        self.git_provider_b64 = base64.b64encode(b'github').decode('utf-8')
        self.git_org_name_b64 = base64.b64encode(b'SovereignCloudStack').decode('utf-8')
        self.git_repo_name_b64 = base64.b64encode(b'cluster-stacks').decode('utf-8')

        os.environ['GIT_PROVIDER_B64'] = self.git_provider_b64
        os.environ['GIT_ORG_NAME_B64'] = self.git_org_name_b64
        os.environ['GIT_REPOSITORY_NAME_B64'] = self.git_repo_name_b64

        # Retrieve the Git token from environment variables
        git_access_token = os.getenv('GIT_ACCESS_TOKEN')
        if git_access_token:
            # Encode the Git access token and set it as an environment variable
            encoded_token = base64.b64encode(git_access_token.encode('utf-8')).decode('utf-8')
            os.environ['GIT_ACCESS_TOKEN_B64'] = encoded_token
        else:
            raise ValueError("Error: GIT_ACCESS_TOKEN environment variable not set.")

        # Cluster Stack Parameters
        self.cs_name = os.getenv('CS_NAME', 'scs')
        self.cs_k8s_version = os.getenv('CS_K8S_VERSION', '1.29')
        self.cs_version = os.getenv('CS_VERSION', 'v1')
        self.cs_channel = os.getenv('CS_CHANNEL', 'stable')
        self.cs_cloudname = os.getenv('CS_CLOUDNAME', 'openstack')
        self.cs_secretname = os.getenv('CS_SECRETNAME', self.cs_cloudname)
        self.cs_class_name = f"openstack-{self.cs_name}-{self.cs_k8s_version.replace('.', '-')}-{self.cs_version}"
        os.environ['CLUSTER_TOPOLOGY'] = 'true'
        os.environ['EXP_CLUSTER_RESOURCE_SET'] = 'true'
        os.environ['EXP_RUNTIME_SDK'] = 'true'
        os.environ['CS_NAME'] = self.cs_name
        os.environ['CS_K8S_VERSION'] = self.cs_k8s_version
        os.environ['CS_VERSION'] = self.cs_version
        os.environ['CS_CHANNEL'] = self.cs_channel
        os.environ['CS_CLOUDNAME'] = self.cs_cloudname
        os.environ['CS_SECRETNAME'] = self.cs_secretname
        os.environ['CS_CLASS_NAME'] = self.cs_class_name

        # CSP-related variables
        self.cs_namespace = os.getenv("CS_NAMESPACE", "default")
        self.clouds_yaml_path = os.getenv("CLOUDS_YAML_PATH")

        if not self.clouds_yaml_path:
            raise ValueError("CLOUDS_YAML_PATH environment variable not set.")

        # Cluster env variables
        self.cs_pod_cidr = os.getenv('CS_POD_CIDR', '192.168.0.0/16')
        self.cs_service_cidr = os.getenv('CS_SERVICE_CIDR', '10.96.0.0/12')
        self.cs_external_id = os.getenv('CS_EXTERNAL_ID', 'ebfe5546-f09f-4f42-ab54-094e457d42ec')
        self.cs_k8s_patch_version = os.getenv('CS_K8S_PATCH_VERSION', '6')

        os.environ['CS_POD_CIDR'] = self.cs_pod_cidr
        os.environ['CS_SERVICE_CIDR'] = self.cs_service_cidr
        os.environ['CS_EXTERNAL_ID'] = self.cs_external_id
        os.environ['CS_K8S_PATCH_VERSION'] = self.cs_k8s_patch_version
        os.environ['CS_CLUSTER_NAME'] = self.cs_cluster_name

    def _create_cluster(self):
        # Step 1: Create the Kind cluster
        self.cluster = KindCluster(
            self.cluster_name
        )
        self.cluster.create()
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())

        # Step 2: Export Kubeconfig
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

        # print("Waiting for webhook services to become ready...")
        time.sleep(60)

        # Step 4: Download and apply the infrastructure components YAML with envsubst and kubectl
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

        # Step 5: Define a namespace for a tenant (CSP/per tenant) and get pat to clouds.yaml file from env variable
        cs_namespace = os.getenv("CS_NAMESPACE", "default")
        clouds_yaml_path = os.getenv("CLOUDS_YAML_PATH")

        if not clouds_yaml_path:
            raise ValueError("CLOUDS_YAML_PATH environment variable not set.")

        # Step 6: Deploy CSP-helper chart
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

        # Todo: How to handle sleep to wait until all cso components are ready
        time.sleep(30)

        # Step 7: Create Cluster Stack definition (CSP/per tenant)
        clusterstack_yaml_path = "clusterstack.yaml"
        try:
            subprocess.run(
                f"/tmp/envsubst < {clusterstack_yaml_path} | kubectl apply -f -",
                shell=True,
                check=True
            )
            print(f"Successfully applied {clusterstack_yaml_path}.")
        except subprocess.CalledProcessError as error:
            print(f"Error during kubectl apply: {error}")
            raise

        # Step 8: Create the workload cluster resource (SCS-User/customer)
        cluster_yaml_path = "cluster.yaml"
        try:
            subprocess.run(
                f"/tmp/envsubst < {cluster_yaml_path} | kubectl apply -f -",
                shell=True,
                check=True
            )
            print(f"Successfully applied {cluster_yaml_path}.")
        except subprocess.CalledProcessError as error:
            print(f"Error during kubectl apply: {error}")
            raise

        # Step 9: Get kubeadmcontrolplane name
        max_retries = 6
        delay_between_retries = 10  # seconds
        for _ in range(max_retries):
            try:
                kcp_command = "kubectl get kubeadmcontrolplane -o=jsonpath='{.items[0].metadata.name}'"
                kcp_name = subprocess.run(kcp_command, shell=True, check=True, capture_output=True, text=True)
                kcp_name_stdout = kcp_name.stdout.strip()
                if kcp_name_stdout:
                    print(f"KubeadmControlPlane name: {kcp_name_stdout}")
                    break
            except subprocess.CalledProcessError as error:
                print(f"Error getting kubeadmcontrolplane name: {error}")
            # Wait before retrying
            time.sleep(delay_between_retries)
        else:
            raise RuntimeError("Failed to get kubeadmcontrolplane name")

        # Step 10: Wait for kubeadmcontrolplane to be available
        try:
            wait_command = f"kubectl wait kubeadmcontrolplane/{kcp_name.stdout.strip()} --for=condition=Available --timeout=300s"
            subprocess.run(wait_command, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for kubeadmcontrolplane to be available: {error}")

        # Step 11: Get kubeconfig of the workload k8s cluster
        try:
            kubeconfig_command = f"clusterctl get kubeconfig {self.cs_cluster_name} > ./{self.kubeconfig_cs_cluster_filename}"
            subprocess.run(kubeconfig_command, shell=True, check=True)
            print(f"Kubeconfig of the workload k8s cluster has been saved to {self.kubeconfig_cs_cluster_filename}.")
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error getting kubeconfig of the workload k8s cluster: {error}")

        # Step 12: Wait for clusteraddons resource to become ready
        try:
            kubeconfig_command = f"kubectl wait clusteraddons/cluster-addon-{self.cs_cluster_name} --for=condition=Ready --timeout=300s"
            subprocess.run(kubeconfig_command, shell=True, check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for clusteraddons to be ready: {error}")

        # Step 13: Wait for all system pods in the workload k8s cluster to become ready
        try:
            wait_pods_command = (
                f"kubectl wait -n kube-system --for=condition=Ready --timeout=300s pod --all --kubeconfig {self.kubeconfig_cs_cluster_filename}"
            )
            subprocess.run(wait_pods_command, shell=True, check=True)
            print("All system pods in the workload Kubernetes cluster are ready.")
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for system pods to become ready: {error}")

    def _delete_cluster(self):
        # Step 1: Check if the cluster exists and if so delete it
        try:
            check_cluster_command = f"kubectl get cluster {self.cs_cluster_name} --kubeconfig {self.kubeconfig}"
            result = subprocess.run(check_cluster_command, shell=True, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"Cluster {self.cs_cluster_name} exists. Proceeding with deletion.")
                # Step 2: Delete the cluster with a timeout
                delete_cluster_command = (
                    f"kubectl delete cluster {self.cs_cluster_name} --kubeconfig {self.kubeconfig} "
                    f"--timeout=300s"
                )
                subprocess.run(delete_cluster_command, shell=True, check=True)
                print(f"Cluster {self.cs_cluster_name} deleted successfully.")
            else:
                print(f"No cluster named {self.cs_cluster_name} found. Nothing to delete.")

        except subprocess.CalledProcessError as error:
            if "NotFound" in error.stderr:
                print(f"Cluster {self.cs_cluster_name} not found. Skipping deletion.")
            else:
                print(f"Error checking for cluster existence: {error}")
                raise
        # Todo: Maybe it is worth to remove the kubeconfig file
        # Step 2: Delete the Kind cluster
        try:
            self.cluster = KindCluster(self.cluster_name)
            self.cluster.delete()
            print(f"Kind cluster {self.cluster_name} deleted successfully.")
        except Exception as error:
            print(f"Error during Kind cluster deletion: {error}")
            raise
