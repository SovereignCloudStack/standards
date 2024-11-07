import shutil

from interface import KubernetesClusterPlugin


class PluginStatic(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes
    using a kubeconfig file
    """

    def __init__(self, config_file=None):
        self.kubeconfig_path = config_file

    def create_cluster(self, cluster_name="scs-cluster", version=None, kubeconfig=None):
        shutil.copyfile(self.kubeconfig_path, kubeconfig)

    def delete_cluster(self, cluster_name=None, version=None):
        pass
