from interface import KubernetesClusterPlugin
from pytest_kind import KindCluster


class PluginKind(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """

    def _create_cluster(self):
        # ~ cluster_version = self.cluster_version #TODO:!!! rebase artefact
        # ~ if cluster_version == '1.29': #TODO:!!! rebase artefact
            # ~ cluster_version = 'v1.29.8' #TODO:!!! rebase artefact
        # ~ elif cluster_version == '1.30': #TODO:!!! rebase artefact
            # ~ cluster_version = 'v1.30.4' #TODO:!!! rebase artefact
        # ~ elif cluster_version == '1.31' or cluster_version == 'default': #TODO:!!! rebase artefact
            # ~ cluster_version = 'v1.31.1' #TODO:!!! rebase artefact

        cluster_image = f"kindest/node:{self.cluster_version}"
        self.cluster = KindCluster(self.cluster_name, self.kubeconfig, cluster_image)
        if self.config is None:
            self.cluster.create()
        else:
            self.cluster.create(self.config)
        self.kubeconfig = str(self.cluster.kubeconfig_path.resolve())

    def _delete_cluster(self):
        self.cluster = KindCluster(self.cluster_name)
        self.cluster.delete()
