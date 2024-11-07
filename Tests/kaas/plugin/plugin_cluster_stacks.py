import os
import yaml
import shutil
import subprocess
import base64
import time
import logging
from pytest_kind import KindCluster
from interface import KubernetesClusterPlugin

logger = logging.getLogger("PluginClusterStacks")


# Helper functions
def wait_for_capi_pods_ready(timeout=240, interval=15):
    """
    Waits for all CAPI pods in specific namespaces to reach the 'Running' state with all containers ready.

    :param timeout: Total time to wait in seconds before giving up.
    :param interval: Time to wait between checks in seconds.
    """
    namespaces = [
        "capi-kubeadm-bootstrap-system",
        "capi-kubeadm-control-plane-system",
        "capi-system",
    ]

    start_time = time.time()

    while time.time() - start_time < timeout:
        all_pods_ready = True

        for namespace in namespaces:
            try:
                # Get pod status in the namespace
                result = subprocess.run(
                    f"kubectl get pods -n {namespace} -o=jsonpath='{{range .items[*]}}{{.metadata.name}} {{.status.phase}} {{range .status.containerStatuses[*]}}{{.ready}} {{end}}{{\"\\n\"}}{{end}}'",
                    shell=True, capture_output=True, text=True, check=True
                )

                if result.returncode == 0:
                    pods_status = result.stdout.strip().splitlines()
                    for pod_status in pods_status:
                        pod_info = pod_status.split()
                        pod_name, phase, *readiness_states = pod_info

                        # Check pod phase and all containers readiness
                        if phase != "Running" or "false" in readiness_states:
                            all_pods_ready = False
                            logger.info(f"Pod {pod_name} in {namespace} is not ready. Phase: {phase}, Ready: {readiness_states}")
                else:
                    logger.info(f"Error fetching pods in {namespace}: {result.stderr}")
                    all_pods_ready = False

            except subprocess.CalledProcessError as error:
                logger.error(f"Error checking pods in {namespace}: {error}")
                all_pods_ready = False

        if all_pods_ready:
            logger.info("All CAPI system pods are ready.")
            return True

        logger.info("Waiting for all CAPI pods to become ready...")
        time.sleep(interval)

    raise TimeoutError(f"Timed out after {timeout} seconds waiting for CAPI and CAPO system pods to become ready.")


def wait_for_cso_pods_ready(timeout=240, interval=15):
    """
    Waits for all CSO (Cluster Stack Operator) pods in the 'cso-system' namespace to reach 'Running' with containers ready.

    :param timeout: Total time to wait in seconds before giving up.
    :param interval: Time to wait between checks in seconds.
    """
    cso_namespace = "cso-system"
    start_time = time.time()

    while time.time() - start_time < timeout:
        all_pods_ready = True

        try:
            # Get pod status in the 'cso-system' namespace
            result = subprocess.run(
                f"kubectl get pods -n {cso_namespace} -o=jsonpath='{{range .items[*]}}{{.metadata.name}} {{.status.phase}} {{range .status.containerStatuses[*]}}{{.ready}} {{end}}{{\"\\n\"}}{{end}}'",
                shell=True, capture_output=True, text=True, check=True
            )

            if result.returncode == 0:
                pods_status = result.stdout.strip().splitlines()
                for pod_status in pods_status:
                    pod_info = pod_status.split()
                    pod_name, phase, *readiness_states = pod_info

                    # Check pod phase and all containers readiness
                    if phase != "Running" or "false" in readiness_states:
                        all_pods_ready = False
                        logger.info(f"Pod {pod_name} in {cso_namespace} is not ready. Phase: {phase}, Ready: {readiness_states}")
            else:
                logger.error(f"Error fetching pods in {cso_namespace}: {result.stderr}")
                all_pods_ready = False

        except subprocess.CalledProcessError as error:
            logger.error(f"Error checking pods in {cso_namespace}: {error}")
            all_pods_ready = False

        if all_pods_ready:
            logger.info("All CSO pods in 'cso-system' namespace are ready.")
            return True

        logger.info("Waiting for CSO pods in 'cso-system' namespace to become ready...")
        time.sleep(interval)

    raise TimeoutError(f"Timed out after {timeout} seconds waiting for CSO pods in 'cso-system' namespace to become ready.")


def wait_for_workload_pods_ready(namespace="kube-system", timeout=600, kubeconfig_path=None):
    """
    Waits for all pods in a specific namespace on a workload Kubernetes cluster to become ready.

    :param namespace: The Kubernetes namespace where pods are located (default is "kube-system").
    :param timeout: The timeout in seconds to wait for pods to become ready (default is 600).
    :param kubeconfig_path: Path to the kubeconfig file for the target Kubernetes cluster.
    :raises RuntimeError: If pods are not ready within the specified timeout.
    """
    try:
        kubeconfig_option = f"--kubeconfig {kubeconfig_path}" if kubeconfig_path else ""
        wait_pods_command = (
            f"kubectl wait -n {namespace} --for=condition=Ready --timeout={timeout}s pod --all {kubeconfig_option}"
        )

        # Run the command
        subprocess.run(wait_pods_command, shell=True, check=True)
        logger.info("All pods in namespace '{namespace}' in the workload Kubernetes cluster are ready.")

    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Error waiting for pods in namespace '{namespace}' to become ready: {error}")


def load_config(config_path):
    """
    Loads the configuration from a YAML file.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file) or {}
        return config


def setup_environment_variables(self):
    # Cluster Stack Parameters
    self.clouds_yaml_path = self.config.get('clouds_yaml_path', '~/.config/openstack/clouds.yaml')
    self.cs_k8s_version = self.cluster_version
    self.cs_name = self.config.get('cs_name', 'scs')
    self.cs_version = self.config.get('cs_version', 'v1')
    self.cs_channel = self.config.get('cs_channel', 'stable')
    self.cs_cloudname = self.config.get('cs_cloudname', 'openstack')
    self.cs_secretname = self.cs_cloudname

    # CSP-related variables and additional cluster configuration
    self.kubeconfig_cs_cluster_filename = f"kubeconfig-{self.cluster_name}.yaml"
    self.cs_class_name = f"openstack-{self.cs_name}-{str(self.cs_k8s_version).replace('.', '-')}-{self.cs_version}"
    self.cs_namespace = self.config.get("cs_namespace", "default")
    self.cs_pod_cidr = self.config.get('cs_pod_cidr', '192.168.0.0/16')
    self.cs_service_cidr = self.config.get('cs_service_cidr', '10.96.0.0/12')
    self.cs_external_id = self.config.get('cs_external_id', 'ebfe5546-f09f-4f42-ab54-094e457d42ec')
    self.cs_k8s_patch_version = self.config.get('cs_k8s_patch_version', '6')

    if not self.clouds_yaml_path:
        raise ValueError("CLOUDS_YAML_PATH environment variable not set.")

    required_env = {
        'CLUSTER_TOPOLOGY': 'true',
        'EXP_CLUSTER_RESOURCE_SET': 'true',
        'EXP_RUNTIME_SDK': 'true',
        'CS_NAME': self.cs_name,
        'CS_K8S_VERSION': self.cs_k8s_version,
        'CS_VERSION': self.cs_version,
        'CS_CHANNEL': self.cs_channel,
        'CS_CLOUDNAME': self.cs_cloudname,
        'CS_SECRETNAME': self.cs_secretname,
        'CS_CLASS_NAME': self.cs_class_name,
        'CS_NAMESPACE': self.cs_namespace,
        'CS_POD_CIDR': self.cs_pod_cidr,
        'CS_SERVICE_CIDR': self.cs_service_cidr,
        'CS_EXTERNAL_ID': self.cs_external_id,
        'CS_K8S_PATCH_VERSION': self.cs_k8s_patch_version,
        'CS_CLUSTER_NAME': self.cluster_name,
    }
    # Update the environment variables
    os.environ.update({key: str(value) for key, value in required_env.items()})


def setup_git_env(self):
    # Setup Git environment variables
    git_provider = self.config.get('git_provider', 'github')
    git_org_name = self.config.get('git_org_name', 'SovereignCloudStack')
    git_repo_name = self.config.get('git_repo_name', 'cluster-stacks')

    os.environ.update({
        'GIT_PROVIDER_B64': base64.b64encode(git_provider.encode()).decode('utf-8'),
        'GIT_ORG_NAME_B64': base64.b64encode(git_org_name.encode()).decode('utf-8'),
        'GIT_REPOSITORY_NAME_B64': base64.b64encode(git_repo_name.encode()).decode('utf-8')
    })

    git_access_token = os.getenv('GIT_ACCESS_TOKEN')
    if git_access_token:
        os.environ['GIT_ACCESS_TOKEN_B64'] = base64.b64encode(git_access_token.encode()).decode('utf-8')
    else:
        raise ValueError("GIT_ACCESS_TOKEN environment variable not set.")


class PluginClusterStacks(KubernetesClusterPlugin):
    def __init__(self, config_file=None):
        self.config = load_config(config_file) if config_file else {}
        logger.debug(self.config)
        self.working_directory = os.getcwd()
        logger.debug(f"Working from {self.working_directory}")

    def create_cluster(self, cluster_name="scs-cluster", version=None, kubeconfig_filepath=None):
        self.cluster_name = cluster_name
        self.cluster_version = version

        # Setup variables
        setup_environment_variables(self)
        setup_git_env(self)

        # Create the Kind cluster
        self.cluster = KindCluster(name=cluster_name)
        self.cluster.create()
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())
        if kubeconfig_filepath:
            shutil.move(self.kubeconfig, kubeconfig_filepath)
        else:
            kubeconfig_filepath = str(self.kubeconfig)
        os.environ['KUBECONFIG'] = kubeconfig_filepath

        # Initialize clusterctl with OpenStack as the infrastructure provider
        self._run_subprocess(["clusterctl", "init", "--infrastructure", "openstack"], "Error during clusterctl init")

        # Wait for all CAPI pods to be ready
        wait_for_capi_pods_ready()

        # Apply infrastructure components
        self._apply_yaml_with_envsubst("cso-infrastructure-components.yaml", "Error applying CSO infrastructure components")
        self._apply_yaml_with_envsubst("cspo-infrastructure-components.yaml", "Error applying CSPO infrastructure components")

        # Deploy CSP-helper chart
        helm_command = (
            f"helm upgrade -i csp-helper-{self.cs_namespace} -n {self.cs_namespace} "
            f"--create-namespace https://github.com/SovereignCloudStack/openstack-csp-helper/releases/latest/download/openstack-csp-helper.tgz "
            f"-f {self.clouds_yaml_path}"
        )
        self._run_subprocess(helm_command, "Error deploying CSP-helper chart", shell=True)

        wait_for_cso_pods_ready()

        # Create Cluster Stack definition and workload cluster
        self._apply_yaml_with_envsubst("clusterstack.yaml", "Error applying clusterstack.yaml")
        self._apply_yaml_with_envsubst("cluster.yaml", "Error applying cluster.yaml")

        # Get and wait on kubeadmcontrolplane and retrieve workload cluster kubeconfig
        kcp_name = self._get_kubeadm_control_plane_name()
        self._wait_kcp_ready(kcp_name)
        self._retrieve_kubeconfig()

        # Wait for workload system pods to be ready
        print(self.kubeconfig_cs_cluster_filename)
        wait_for_workload_pods_ready(kubeconfig_path=self.kubeconfig_cs_cluster_filename)

    def delete_cluster(self, cluster_name=None, kubeconfig_filepath=None):
        kubeconfig_cs_cluster_filename = f"kubeconfig-{cluster_name}.yaml"
        try:
            # Check if the cluster exists
            check_cluster_command = f"kubectl get cluster {cluster_name} --kubeconfig {kubeconfig_filepath}"
            result = subprocess.run(check_cluster_command, shell=True, check=True, capture_output=True, text=True)

            # Proceed with deletion only if the cluster exists
            if result.returncode == 0:
                delete_command = f"kubectl delete cluster {cluster_name} --timeout=600s --kubeconfig {kubeconfig_filepath}"
                self._run_subprocess(delete_command, "Timeout while deleting the cluster", shell=True)

        except subprocess.CalledProcessError as error:
            if "NotFound" in error.stderr:
                logger.info(f"Cluster {cluster_name} not found. Skipping deletion.")
            else:
                raise RuntimeError(f"Error checking for cluster existence: {error}")

        # Delete kind cluster
        self.cluster = KindCluster(cluster_name)
        self.cluster.delete()

        # Remove kubeconfigs
        if os.path.exists(kubeconfig_cs_cluster_filename):
            os.remove(kubeconfig_cs_cluster_filename)
        if os.path.exists(kubeconfig_filepath):
            os.remove(kubeconfig_filepath)

    def _apply_yaml_with_envsubst(self, yaml_file, error_msg):
        try:
            # Determine if the file is a local path or a URL
            if os.path.isfile(yaml_file):
                command = f"/tmp/envsubst < {yaml_file} | kubectl apply -f -"
            elif yaml_file == "cso-infrastructure-components.yaml":
                url = "https://github.com/SovereignCloudStack/cluster-stack-operator/releases/latest/download/cso-infrastructure-components.yaml"
                command = f"curl -sSL {url} | /tmp/envsubst | kubectl apply -f -"
            elif yaml_file == "cspo-infrastructure-components.yaml":
                url = "https://github.com/SovereignCloudStack/cluster-stack-provider-openstack/releases/latest/download/cspo-infrastructure-components.yaml"
                command = f"curl -sSL {url} | /tmp/envsubst | kubectl apply -f -"
            else:
                raise ValueError(f"Unknown file or URL: {yaml_file}")

            self._run_subprocess(command, error_msg, shell=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"{error_msg}: {error}")

    def _get_kubeadm_control_plane_name(self):
        max_retries = 6
        delay_between_retries = 10
        for _ in range(max_retries):
            try:
                kcp_name = subprocess.run(
                    "kubectl get kubeadmcontrolplane -o=jsonpath='{.items[0].metadata.name}'",
                    shell=True, check=True, capture_output=True, text=True
                )
                kcp_name_stdout = kcp_name.stdout.strip()
                if kcp_name_stdout:
                    print(f"KubeadmControlPlane name: {kcp_name_stdout}")
                    return kcp_name_stdout
            except subprocess.CalledProcessError as error:
                print(f"Error getting kubeadmcontrolplane name: {error}")
            # Wait before retrying
            time.sleep(delay_between_retries)
        else:
            raise RuntimeError("Failed to get kubeadmcontrolplane name")

    def _wait_kcp_ready(self, kcp_name):
        try:
            self._run_subprocess(
                f"kubectl wait kubeadmcontrolplane/{kcp_name} --for=condition=Available --timeout=600s",
                "Error waiting for kubeadmcontrolplane availability",
                shell=True
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for kubeadmcontrolplane to be ready: {error}")

    def _retrieve_kubeconfig(self):
        kubeconfig_command = (
            f"clusterctl get kubeconfig {self.cluster_name} > {self.kubeconfig_cs_cluster_filename}"
        )
        self._run_subprocess(kubeconfig_command, "Error retrieving kubeconfig", shell=True)

    def _run_subprocess(self, command, error_msg, shell=False):
        try:
            subprocess.run(command, shell=shell, check=True)
            logger.info(f"{command} executed successfully")
        except subprocess.CalledProcessError as error:
            logger.error(f"{error_msg}: {error}")
            raise
