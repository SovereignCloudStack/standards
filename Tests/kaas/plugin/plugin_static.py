from interface import KubernetesClusterPlugin


class PluginStatic(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes
    using a kubeconfig file
    """

    def create_cluster(self):
        self.kubeconfig = self.kubeconfig

    def delete_cluster(self):
        pass
