import logging
import os
import os.path
from pathlib import Path

from interface import KubernetesClusterPlugin
from pytest_kind import KindCluster

logger = logging.getLogger(__name__)


class PluginKind(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """
    def __init__(self, config, basepath='.'):
        self.basepath = basepath
        self.config = config
        logger.debug(self.config)

    def create_cluster(self, kubeconfig_path):
        cluster_name = self.config['name']
        cluster_image = self.config['image']
        cluster_yaml = self.config.get('cluster')
        if cluster_yaml and not os.path.isabs(cluster_yaml):
            cluster_yaml = os.path.normpath(os.path.join(self.basepath, cluster_yaml))
        cluster = KindCluster(name=cluster_name, image=cluster_image, kubeconfig=Path(kubeconfig_path))
        cluster.create(cluster_yaml)

    def delete_cluster(self):
        cluster_name = self.config['name']
        KindCluster(cluster_name).delete()
