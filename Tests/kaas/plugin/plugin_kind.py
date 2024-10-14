from .interface import KubernetesClusterPlugin
from pytest_kind import KindCluster


class PluginKind(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """

    def _create_cluster(self):
        config_file = None
        cluster_image = f"kindest/node:{self.cluster_version}"
        self.cluster = KindCluster(self.cluster_name, self.kubeconfig, cluster_image)
        self.cluster.create(config_file)
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())

    def _delete_cluster(self):
        self.cluster = KindCluster(self.cluster_name)
        self.cluster.delete()
