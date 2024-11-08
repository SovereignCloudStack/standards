import yaml
import sys
import logging
from kubernetes import client, config

manual_result_file_template = {
    "name": None,
    "status": None,
    "details": {"messages": None},
}

logger = logging.getLogger("helper")


def initialize_logging():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)


def print_usage(file=sys.stderr):
    """Help output"""
    print(
        """Usage: k8s_storageclass_check.py [options]
This tool checks the requested k8s default storage class according to the SCS Standard 0211 "kaas-default-storage-class".
Options:
 [-k/--kubeconfig PATH_TO_KUBECONFIG] sets kubeconfig file to access kubernetes api
 [-d/--debug] enables DEBUG logging channel
""",
        end="",
        file=file,
    )


class SCSTestException(Exception):
    """Raised when an Specific test did not pass"""

    def __init__(self, *args, return_code: int):
        self.return_code = return_code


def setup_k8s_client(kubeconfigfile=None):

    if kubeconfigfile:
        logger.debug(f"using kubeconfig file '{kubeconfigfile}'")
        config.load_kube_config(kubeconfigfile)
    else:
        logger.debug(" using system kubeconfig")
        config.load_kube_config()

    k8s_api_client = client.CoreV1Api()
    k8s_storage_client = client.StorageV1Api()

    return (
        k8s_api_client,
        k8s_storage_client,
    )


def gen_sonobuoy_result_file(error_n: int, error_msg: str, test_file_name: str):

    test_name = test_file_name.replace(".py", "")

    test_status = "passed"

    if error_n != 0:
        test_status = test_name + "_" + str(error_n)

    result_file = manual_result_file_template

    result_file["name"] = test_name
    result_file["status"] = test_status
    result_file["details"]["messages"] = error_msg

    with open(f"./{test_name}.result.yaml", "w") as file:
        yaml.dump(result_file, file)
