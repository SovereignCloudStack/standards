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

# Default configuration values
DEFAULTS = {
    'cs_name': 'scs',
    'clouds_yaml_path': '~/.config/openstack/clouds.yaml',
    'git_provider': 'github',
    'git_org_name': 'SovereignCloudStack',
    'git_repo_name': 'cluster-stacks',
    'cluster_topology': 'true',
    'exp_cluster_resource_set': 'true',
    'exp_runtime_sdk': 'true'
}

# Keys needed for environment variables
ENV_KEYS = {'cs_name', 'cs_version', 'cs_channel', 'cs_cloudname', 'cs_secretname', 'cs_class_name',
            'cs_namespace', 'cs_pod_cidr', 'cs_service_cidr', 'cs_external_id', 'cs_k8s_patch_version',
            'cs_cluster_name', 'cs_k8s_version', 'git_provider', 'git_org_name', 'git_repo_name',
            'cluster_topology', 'exp_cluster_resource_set', 'exp_runtime_sdk'}


# Helper functions
def wait_for_pods(self, namespaces, timeout=240, interval=15, kubeconfig=None):
    """
    Waits for all pods in specified namespaces to reach the 'Running' state with all containers ready.

    :param namespaces: List of namespaces to check for pod readiness.
    :param timeout: Total time to wait in seconds before giving up.
    :param interval: Time to wait between checks in seconds.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        all_pods_ready = True

        for namespace in namespaces:
            try:
                # Get pod status in the namespace
                command = (
                    f"kubectl get pods -n {namespace} --kubeconfig {kubeconfig} "
                    f"-o=jsonpath='{{range .items[*]}}{{.metadata.name}} {{.status.phase}} {{range .status.containerStatuses[*]}}{{.ready}} {{end}}{{\"\\n\"}}{{end}}'"
                )
                result = self._run_subprocess(command, f"Error fetching pods in {namespace}", shell=True, capture_output=True, text=True)

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
                    logger.error(f"Error fetching pods in {namespace}: {result.stderr}")
                    all_pods_ready = False

            except subprocess.CalledProcessError as error:
                logger.error(f"Error checking pods in {namespace}: {error}")
                all_pods_ready = False

        if all_pods_ready:
            logger.info("All specified pods are ready in all namespaces.")
            return True

        logger.info("Waiting for all pods in specified namespaces to become ready...")
        time.sleep(interval)

    raise TimeoutError(f"Timed out after {timeout} seconds waiting for pods in namespaces {namespaces} to become ready.")


def wait_for_workload_pods_ready(namespace="kube-system", timeout=600, kubeconfig_path=None, max_retries=3, delay=30):
    """
    Waits for all pods in a specific namespace on a workload Kubernetes cluster to become ready.

    :param namespace: The Kubernetes namespace where pods are located (default is "kube-system").
    :param timeout: The timeout in seconds to wait for pods to become ready (default is 600).
    :param kubeconfig_path: Path to the kubeconfig file for the target Kubernetes cluster.
    :raises RuntimeError: If pods are not ready within the specified timeout.
    """
    for attempt in range(max_retries):
        try:
            kubeconfig_option = f"--kubeconfig {kubeconfig_path}" if kubeconfig_path else ""
            wait_pods_command = (
                f"kubectl wait -n {namespace} --for=condition=Ready --timeout={timeout}s pod --all {kubeconfig_option}"
            )

            # Run the command
            subprocess.run(wait_pods_command, shell=True, check=True)
            logger.info(f"All pods in namespace {namespace} in the workload Kubernetes cluster are ready.")
            return True

        except subprocess.CalledProcessError as error:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed with error: {error}. Retrying in {delay} seconds...")
            time.sleep(delay)

    raise RuntimeError(f"Error waiting for pods in namespace '{namespace}' to become ready.")


def load_config(config_path):
    """
    Loads the configuration from a YAML file.
    """

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file) or {}
        return config


def setup_environment_variables(self):
    """
    Constructs and returns a dictionary of required environment variables
    based on the configuration.
    """
    # Calculate values that need to be set dynamically
    if hasattr(self, 'cluster_version'):
        self.config['cs_k8s_version'] = self.cluster_version
        self.config['cs_class_name'] = (
            f"openstack-{self.config['cs_name']}-{str(self.config['cs_k8s_version']).replace('.', '-')}-"
            f"{self.config['cs_version']}"
        )
    self.config['cs_secretname'] = self.config['cs_cloudname']
    if hasattr(self, 'cluster_name'):
        self.config['cs_cluster_name'] = self.cluster_name

    # Construct general environment variables
    required_env = {key.upper(): value for key, value in self.config.items() if key in ENV_KEYS}

    # Encode Git-related environment variables
    required_env.update({
        'GIT_PROVIDER_B64': base64.b64encode(self.config['git_provider'].encode()).decode('utf-8'),
        'GIT_ORG_NAME_B64': base64.b64encode(self.config['git_org_name'].encode()).decode('utf-8'),
        'GIT_REPOSITORY_NAME_B64': base64.b64encode(self.config['git_repo_name'].encode()).decode('utf-8')
    })

    git_access_token = os.getenv('GIT_ACCESS_TOKEN')
    if not git_access_token:
        raise ValueError("GIT_ACCESS_TOKEN environment variable not set.")
    os.environ['GIT_ACCESS_TOKEN_B64'] = base64.b64encode(git_access_token.encode()).decode('utf-8')

    return required_env


class PluginClusterStacks(KubernetesClusterPlugin):
    def __init__(self, config_file=None):
        self.config = load_config(config_file) if config_file else {}
        logger.debug(self.config)
        self.working_directory = os.getcwd()
        for key, value in DEFAULTS.items():
            self.config.setdefault(key, value)
        self.clouds_yaml_path = os.path.expanduser(self.config.get('clouds_yaml_path'))
        self.cs_namespace = self.config.get('cs_namespace')
        logger.debug(f"Working from {self.working_directory}")

    def create_cluster(self, cluster_name="scs-cluster", version=None, kubeconfig_filepath=None):
        self.cluster_name = cluster_name
        self.cluster_version = version
        self.kubeconfig_cs_cluster_filename = f"kubeconfig-{cluster_name}.yaml"

        # Create the Kind cluster
        self.cluster = KindCluster(name=cluster_name)
        self.cluster.create()
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())
        if kubeconfig_filepath:
            shutil.move(self.kubeconfig, kubeconfig_filepath)
        else:
            kubeconfig_filepath = str(self.kubeconfig)

        # Initialize clusterctl with OpenStack as the infrastructure provider
        self._run_subprocess(
            ["sudo", "-E", "clusterctl", "init", "--infrastructure", "openstack"],
            "Error during clusterctl init",
            kubeconfig=kubeconfig_filepath
        )

        # Wait for all CAPI pods to be ready
        wait_for_pods(self, ["capi-kubeadm-bootstrap-system", "capi-kubeadm-control-plane-system", "capi-system"], kubeconfig=kubeconfig_filepath)

        # Apply infrastructure components
        self._apply_yaml_with_envsubst("cso-infrastructure-components.yaml", "Error applying CSO infrastructure components", kubeconfig=kubeconfig_filepath)
        self._apply_yaml_with_envsubst("cspo-infrastructure-components.yaml", "Error applying CSPO infrastructure components", kubeconfig=kubeconfig_filepath)

        # Deploy CSP-helper chart
        helm_command = (
            f"helm upgrade -i csp-helper-{self.cs_namespace} -n {self.cs_namespace} "
            f"--create-namespace https://github.com/SovereignCloudStack/openstack-csp-helper/releases/latest/download/openstack-csp-helper.tgz "
            f"-f {self.clouds_yaml_path}"
        )
        self._run_subprocess(helm_command, "Error deploying CSP-helper chart", shell=True, kubeconfig=kubeconfig_filepath)

        wait_for_pods(self, ["cso-system"], kubeconfig=kubeconfig_filepath)

        # Create Cluster Stack definition and workload cluster
        self._apply_yaml_with_envsubst("clusterstack.yaml", "Error applying clusterstack.yaml", kubeconfig=kubeconfig_filepath)
        self._apply_yaml_with_envsubst("cluster.yaml", "Error applying cluster.yaml", kubeconfig=kubeconfig_filepath)

        # Get and wait on kubeadmcontrolplane and retrieve workload cluster kubeconfig
        kcp_name = self._get_kubeadm_control_plane_name(kubeconfig=kubeconfig_filepath)
        self._wait_kcp_ready(kcp_name, kubeconfig=kubeconfig_filepath)
        self._retrieve_kubeconfig(kubeconfig=kubeconfig_filepath)

        # Wait for workload system pods to be ready
        wait_for_workload_pods_ready(kubeconfig_path=self.kubeconfig_cs_cluster_filename)

    def delete_cluster(self, cluster_name=None, kubeconfig_filepath=None):
        self.cluster_name = cluster_name
        kubeconfig_cs_cluster_filename = f"kubeconfig-{cluster_name}.yaml"
        try:
            # Check if the cluster exists
            check_cluster_command = f"kubectl get cluster {cluster_name}"
            result = self._run_subprocess(check_cluster_command, "Failed to get cluster resource", shell=True, capture_output=True, text=True, kubeconfig={kubeconfig_filepath})

            # Proceed with deletion only if the cluster exists
            if result.returncode == 0:
                delete_command = f"kubectl delete cluster {cluster_name} --timeout=600s"
                self._run_subprocess(delete_command, "Timeout while deleting the cluster", shell=True, kubeconfig=kubeconfig_filepath)

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

    def _apply_yaml_with_envsubst(self, yaml_file, error_msg, kubeconfig=None):
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

            self._run_subprocess(command, error_msg, shell=True, kubeconfig=kubeconfig)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"{error_msg}: {error}")

    def _get_kubeadm_control_plane_name(self, kubeconfig=None):
        max_retries = 6
        delay_between_retries = 10
        for _ in range(max_retries):
            try:
                kcp_command = (
                    "kubectl get kubeadmcontrolplane -o=jsonpath='{.items[0].metadata.name}'"
                )
                kcp_name = self._run_subprocess(kcp_command, "Error retrieving kcp_name", shell=True, capture_output=True, text=True, kubeconfig=kubeconfig)
                logger.info(kcp_name)
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

    def _wait_kcp_ready(self, kcp_name, kubeconfig=None):
        try:
            self._run_subprocess(
                f"kubectl wait kubeadmcontrolplane/{kcp_name} --for=condition=Available --timeout=600s",
                "Error waiting for kubeadmcontrolplane availability",
                shell=True,
                kubeconfig=kubeconfig
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Error waiting for kubeadmcontrolplane to be ready: {error}")

    def _retrieve_kubeconfig(self, kubeconfig=None):
        kubeconfig_command = (
            f"clusterctl get kubeconfig {self.cluster_name} > {self.kubeconfig_cs_cluster_filename}"
        )
        self._run_subprocess(kubeconfig_command, "Error retrieving kubeconfig", shell=True, kubeconfig=kubeconfig)

    def _run_subprocess(self, command, error_msg, shell=False, capture_output=False, text=False, kubeconfig=None):
        try:
            env = setup_environment_variables(self)
            env['PATH'] = f'/usr/local/bin:/usr/bin:{self.working_directory}'
            if kubeconfig:
                env['KUBECONFIG'] = kubeconfig

            # Run the subprocess with the custom environment
            result = subprocess.run(command, shell=shell, capture_output=capture_output, text=text, check=True, env=env)

            return result

        except subprocess.CalledProcessError as error:
            logger.error(f"{error_msg}: {error}")
            raise
