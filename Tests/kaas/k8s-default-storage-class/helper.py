import yaml
import sys
import logging
from kubernetes import client, config
import os

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
