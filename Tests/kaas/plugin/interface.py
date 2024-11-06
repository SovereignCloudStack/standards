from abc import abstractmethod


class KubernetesClusterPlugin():
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes

    To implement fill the methods `create_cluster` and `delete_cluster` with
    api provider-specific functionalities for creating and deleting clusters.

    - Implement `create_cluster` and `delete_cluster` methods
    - Create `__init__(self, config_file=None)` method to handle api specific
      configurations.

    Example:
        .. code:: python

          from interface import KubernetesClusterPlugin
          from apiX_library import cluster_api_class as ClusterAPI

          class PluginX(KubernetesClusterPlugin):

              def __init__(self, config_file=None):
                  self.config = config_file

              def create_cluster(self):
                  self.cluster = ClusterAPI(name=cluster_name, image=cluster_image)
                  self.cluster.create(self.config)
                  kubeconfig_filepath = str(self.cluster.kubeconfig_path.resolve())
                  return self.kubeconfig_filepath

              def delete_cluster(self):
                  self.cluster = ClusterAPI(cluster_name)
                  self.cluster.delete()
        ..
    """

    @abstractmethod
    def create_cluster(self, cluster_name="scs-cluster", version=None, kubeconfig_filepath=None) -> (str):
        """
        This method is to be called to create a k8s cluster
        :param: cluster_name:
        :param: version:
        :param: kubeconfig_filepath:
        :return: kubeconfig_filepath
        """

    @abstractmethod
    def delete_cluster(self, cluster_name=None):
        """
        This method is to be called in order to unprovision a cluster
        :param: cluster_name:
        """
