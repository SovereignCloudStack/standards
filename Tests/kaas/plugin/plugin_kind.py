import logging
import os
import os.path
from pathlib import Path

from interface import KubernetesClusterPlugin
from pytest_kind import KindCluster

logger = logging.getLogger("plugin_kind")


class PluginKind(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """
    def __init__(self, config_file=None):
        logger.info(f"Init provider plug-in of type {self.__class__.__name__}")
        self.config = config_file
        logger.debug(self.config)
        self.working_directory = os.getcwd()
        logger.debug(f"Working from {self.working_directory}")

    def create_cluster(self, cluster_name="scs-cluster", version=None, kubeconfig=None):
        """
        This method is to be called to create a k8s cluster
        :param: kubernetes_version:
        :return: kubeconfig_filepath
        """
        cluster_version = version
        if cluster_version == '1.29':
            cluster_version = 'v1.29.8'
        elif cluster_version == '1.30':
            cluster_version = 'v1.30.4'
        elif cluster_version == '1.31' or cluster_version == 'default':
            cluster_version = 'v1.31.1'
        cluster_image = f"kindest/node:{cluster_version}"
        kubeconfig_filepath = Path(kubeconfig)
        if kubeconfig_filepath is None:
            raise ValueError("kubeconfig_filepath is missing")
        else:
            self.cluster = KindCluster(name=cluster_name, image=cluster_image, kubeconfig=kubeconfig_filepath)
        if self.config is None:
            self.cluster.create()
        else:
            self.cluster.create(self.config)
        return str(self.cluster.kubeconfig_path.resolve())

    def delete_cluster(self, cluster_name=None):
        self.cluster = KindCluster(cluster_name)
        self.cluster.delete()
