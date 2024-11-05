from abc import abstractmethod
from typing import final
import os
import os.path
import shutil
import logging

logger = logging.getLogger("interface")


class KubernetesClusterPlugin():
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes
    """

    kubeconfig = None
    cluster_name = None
    k8s_api_client = None
    working_directory = None

    @final
    def __init__(self, config_file=None):
        logger.info(f"Init provider plug-in of type {self.__class__.__name__}")
        self.config = config_file
        logger.debug(self.config)
        self.working_directory = os.getcwd()
        logger.debug(f"Working from {self.working_directory}")

    @abstractmethod
    def _create_cluster(self, cluster_name) -> (str, int):
        """
        Create a Kubernetes cluster to test aggainst.
        :param: cluster_name:
        :return: kubeconfig: kubeconfig of the cluster used for testing
        """
        pass

    @abstractmethod
    def _delete_cluster(self, cluster_name) -> (str, int):
        """
        Delete the Kubernetes cluster.
        :param: cluster_name:
        :return: None
        """
        pass

    @final
    def create(self, name="scs-cluster", version=None, kubeconfig_filepath=None):
        """
        This method is to be called to create a k8s cluster
        :param: kubernetes_version:
        :return: uuid
        """
        self.cluster_name = name
        self.cluster_version = version

        self._create_cluster()

        if kubeconfig_filepath:
            shutil.move(self.kubeconfig, kubeconfig_filepath)
        else:
            kubeconfig_filepath = str(self.kubeconfig)

        return kubeconfig_filepath

    @final
    def delete(self, cluster_name=None):
        """
        This method is to be called in order to unprovision a cluster
        :param: cluster_uuid:
        """
        self.cluster_name = cluster_name
        try:
            self._delete_cluster()
        except Exception as e:
            logging.exception(e)
