import os
import subprocess
import base64
import time

from interface import KubernetesClusterPlugin
from pytest_kind import KindCluster


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
        except subprocess.CalledProcessError as e:
            print(f"Error during clusterctl init: {e}")
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
        time.sleep(90)

        # Step 5: Download and apply the infrastructure components YAML with envsubst and kubectl
        download_and_apply_cmd_cso = (
            "curl -sSL "
            "https://github.com/SovereignCloudStack/cluster-stack-operator/releases/latest/download/cso-infrastructure-components.yaml"
            " | /tmp/envsubst | kubectl apply -f -"
        )

        download_and_apply_cmd_cspo = (
            "curl -sSL "
            "https://github.com/SovereignCloudStack/cluster-stack-provider-openstack/releases/latest/download/cspo-infrastructure-components.yaml"
            " | /tmp/envsubst | kubectl apply -f -"
        )        
        try:
            subprocess.run(download_and_apply_cmd_cso, shell=True, check=True)
            subprocess.run(download_and_apply_cmd_cspo, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during downloading and applying YAML: {e}")
            raise

        # Step 6: Get CS_NAMESPACE and CLOUDS_YAML_PATH from environment variables
        cs_namespace = os.getenv("CS_NAMESPACE")
        clouds_yaml_path = os.getenv("CLOUDS_YAML_PATH")

        if not cs_namespace:
            raise ValueError("CS_NAMESPACE environment variable not set.")
        if not clouds_yaml_path:
            raise ValueError("CLOUDS_YAML_PATH environment variable not set.")

        # Step 7: Run helm upgrade command using CS_NAMESPACE and CLOUDS_YAML_PATH
        helm_command = (
            f"helm upgrade -i csp-helper-{cs_namespace} "
            f"-n {cs_namespace} --create-namespace "
            "https://github.com/SovereignCloudStack/openstack-csp-helper/releases/latest/download/openstack-csp-helper.tgz "
            f"-f {clouds_yaml_path}"
        )

        try:
            subprocess.run(helm_command, shell=True, check=True)
            print(f"Helm upgrade/install for {cs_namespace} completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during Helm upgrade: {e}")
            raise

        # Step 8: Todo: Handle env variables for clusterstack.yaml file
        # Todo: How to handle sleep to wait until all cso components are ready
        time.sleep(120)

        # Step 9: Apply the clusterstack.yaml file
        clusterstack_yaml_path = "clusterstack.yaml"
        try:
            subprocess.run(
                f"envsubst < {clusterstack_yaml_path} | kubectl apply -f -",
                shell=True,
                check=True
            )
            print(f"Successfully applied {clusterstack_yaml_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Error during kubectl apply: {e}")
            raise        

    def _delete_cluster(self):
        self.cluster = KindCluster(self.cluster_name)
        self.cluster.delete()
