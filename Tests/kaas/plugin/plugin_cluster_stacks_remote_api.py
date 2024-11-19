import os
import yaml
import subprocess
import base64
import time
import logging
from interface import KubernetesClusterPlugin

logger = logging.getLogger("PluginClusterStacks")

# Helper functions
def wait_for_pods(self, namespaces, timeout=240, interval=15, kubeconfig=None):
    """
    Waits for all pods in specified namespaces to reach the condition 'Ready'.

    :param namespaces: List of namespaces to check for pod readiness.
    :param timeout: Total time to wait in seconds before giving up.
    :param interval: Time to wait between checks in seconds.
    :param kubeconfig: Optional path to the kubeconfig file for the target Kubernetes cluster.
    :return: True if all pods are ready within the given timeout, raises TimeoutError otherwise.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        all_pods_ready = True

        for namespace in namespaces:
            try:
                # Get pod status in the namespace
                wait_pods_command = (
                    f"kubectl wait -n {namespace} --for=condition=Ready --timeout={timeout}s pod --all"
                )
                result = self._run_subprocess(wait_pods_command, f"Error fetching pods in {namespace}", shell=True, capture_output=True, text=True, kubeconfig=kubeconfig)

                if result.returncode != 0:
                    logger.warning(f"Not all pods in namespace {namespace} are ready. Details: {result.stderr}")
                    all_pods_ready = False
                else:
                    logger.info(f"All pods in namespace {namespace} are ready.")

            except subprocess.CalledProcessError as error:
                logger.error(f"Error checking pods in {namespace}: {error}")
                all_pods_ready = False

        if all_pods_ready:
            logger.info("All specified pods are ready in all namespaces.")
            return True

        logger.info("Waiting for all pods in specified namespaces to become ready...")
        time.sleep(interval)

    raise TimeoutError(f"Timed out after {timeout} seconds waiting for pods in namespaces {namespaces} to become ready.")


def load_config(config_path):
    """
    Loads the configuration from a YAML file.
    """

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file) or {}
        return config

class PluginClusterStacksRemoteAPI(KubernetesClusterPlugin):
    def __init__(self, config_file=None):
        self.config = load_config(config_file) if config_file else {}
        logger.debug(self.config)
        self.working_directory = os.getcwd()
        logger.debug(f"Working from {self.working_directory}")
        self.kubeconfig_mgmnt = self.config['kubeconfig']
        self.workloadclusters  = self.config['workloadcluster']
        self.cs_namespace = self.config['namespace']


    def create_cluster(self, cluster_name=None, version=None, kubeconfig_filepath=None):
        self.cluster_name = cluster_name
        self.cluster_version = version
        self.kubeconfig_cs_cluster = kubeconfig_filepath

        # Create workload cluster
        self._apply_yaml(self.workloadclusters, "Error applying cluster.yaml", kubeconfig=self.kubeconfig_mgmnt)

        #TODO:!!! We also need to introduce a waiting function here

        print("retrieve kubeconfig to path")
        self._retrieve_kubeconfig(namespace=self.cs_namespace, kubeconfig=self.kubeconfig_mgmnt)

        # Wait for workload system pods to be ready
        # wait_for_workload_pods_ready(kubeconfig_path=self.kubeconfig_cs_cluster)
        # ~ wait_for_pods(self, ["kube-system"], timeout=600, interval=15, kubeconfig=self.kubeconfig_cs_cluster)


    def delete_cluster(self, cluster_name=None): #TODO:!!! need to adjust delete method
        self.cluster_name = cluster_name
        #Get the name of the workloadcluster from the config file
        workload_cluster_config = load_config(self.workloadclusters)
        workload_cluster_name = workload_cluster_config['metadata']['name']
        try:
            # Check if the cluster exists
            check_cluster_command = f"kubectl --kubeconfig={self.kubeconfig_mgmnt} get cluster {workload_cluster_name} -n {self.cs_namespace}"
            result = self._run_subprocess(check_cluster_command, "Failed to get cluster resource", shell=True, capture_output=True, text=True)

            # Proceed with deletion only if the cluster exists
            if result.returncode == 0:
                delete_command = f"kubectl --kubeconfig={self.kubeconfig_mgmnt} delete cluster {workload_cluster_name} --timeout=600s -n {self.cs_namespace}"
                self._run_subprocess(delete_command, "Timeout while deleting the cluster", shell=True)

        except subprocess.CalledProcessError as error:
            if "NotFound" in error.stderr:
                logger.info(f"Cluster {workload_cluster_name} not found. Skipping deletion.")
            else:
                raise RuntimeError(f"Error checking for cluster existence: {error}")


    def _apply_yaml(self, yaml_file, error_msg, kubeconfig=None):
        """
        Applies a Kubernetes YAML configuration file to the cluster, substituting environment variables as needed.

        :param yaml_file: The name of the YAML file to apply.
        :param kubeconfig: Optional path to a kubeconfig file, which specifies which Kubernetes cluster
                        to apply the YAML configuration to.
        """
        try:
            # Determine if the file is a local path or a URL
            if os.path.isfile(yaml_file):
                command = f"kubectl --kubeconfig={self.kubeconfig_mgmnt} apply -f {yaml_file} -n {self.cs_namespace}"
            else:
                raise ValueError(f"Unknown file: {yaml_file}")

            self._run_subprocess(command, error_msg, shell=True)

        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"{error_msg}: {error}")


    def _retrieve_kubeconfig(self, namespace="default", kubeconfig=None):
        """
        Retrieves the kubeconfig for the specified cluster and saves it to a local file.

        :param namespace: The namespace of the cluster to retrieve the kubeconfig for.
        :param kubeconfig: Optional path to the kubeconfig file for the target Kubernetes cluster.
        """

        #Get the name of the workloadcluster from the config file
        workload_cluster_config = load_config(self.workloadclusters)
        workload_cluster_name = workload_cluster_config['metadata']['name']

        command_args = [
            "kubectl ",
            f"--kubeconfig={self.kubeconfig_mgmnt}",
            f"-n {self.cs_namespace}",
            f"get secret {workload_cluster_name}-kubeconfig", 
            "-o go-template='{{.data.value|base64decode}}'",
            f"> {self.kubeconfig_cs_cluster}",
        ]
        kubeconfig_command = ""
        for entry in command_args:
            kubeconfig_command += entry + " "
        self._run_subprocess(kubeconfig_command, "Error retrieving kubeconfig", shell=True)


    def _run_subprocess(self, command, error_msg, shell=False, capture_output=False, text=False):
        """
        Executes a subprocess command with the specified environment variables and parameters.

        :param command: The shell command to be executed. This can be a string or a list of arguments to pass to the subprocess.
        :param error_msg: A custom error message to be logged and raised if the subprocess fails.
        :param shell: Whether to execute the command through the shell (default: `False`).
        :param capture_output: Whether to capture the command's standard output and standard error (default: `False`).
        :param text: Whether to treat the command's output and error as text (default: `False`).
        :return: The result of the `subprocess.run` command
        """
        try:
            # Run the subprocess
            result = subprocess.run(command, shell=shell, capture_output=capture_output, text=text, check=True)
            return result
        except subprocess.CalledProcessError as error:
            logger.error(f"{error_msg}: {error}")
            raise
