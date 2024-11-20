import shutil

from interface import KubernetesClusterPlugin


class PluginStatic(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes
    using a kubeconfig file
    """

    def __init__(self, config_path):
        self.kubeconfig_path = config_path

    def create_cluster(self, cluster_name, version, kubeconfig):
        shutil.copyfile(self.kubeconfig_path, kubeconfig)

    def delete_cluster(self, cluster_name, version):
        pass
