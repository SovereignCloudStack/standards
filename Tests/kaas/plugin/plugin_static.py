from interface import KubernetesClusterPlugin
import os


class PluginStatic(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes
    using a kubeconfig file
    """
    def _create_cluster(self):
        self.kubeconfig_path = os.environ["KUBECONFIG"]

    def _delete_cluster(self):
        pass
