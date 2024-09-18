from interface import KubernetesClusterPlugin
from pytest_kind import KindCluster


class PluginKind(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """

    def _create_cluster(self):
        self.cluster_name = "scs-cluster"
        self.cluster = KindCluster(self.cluster_name)
        self.cluster.create()
        self.kubeconfig_path = str(self.cluster.kubeconfig_path.resolve())

    def _delete_cluster(self):
        self.cluster.delete()
