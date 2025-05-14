

class KubernetesClusterPlugin():
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes

    To implement fill the methods `create_cluster` and `delete_cluster` with
    api provider-specific functionalities for creating and deleting clusters.
    The `create_cluster` method must ensure that the kubeconfigfile is provided
    at the position in the file system defined by the parameter
    `kubeconfig_filepath`

    - Implement `create_cluster` and `delete_cluster` methods
    - Create `__init__(self, config, basepath)` method to handle api specific
      configurations.

    Example:
        .. code:: python

          from interface import KubernetesClusterPlugin
          from apiX_library import cluster_api_class as ClusterAPI

          class PluginX(KubernetesClusterPlugin):

              def __init__(self, config, basepath):
                  self.config = config
                  self.basepath = basepath  # find other config files here

              def create_cluster(self, kubeconfig_path):
                  self.cluster = ClusterAPI(name=self.config['name'], kubeconfig_filepath)
                  self.cluster.create()

              def delete_cluster(self, cluster_name):
                  self.cluster = ClusterAPI(name=self.config['name'])
                  self.cluster.delete()
        ..
    """

    def create_cluster(self, kubeconfig_path: str):
        """
        This method is to be called to create a k8s cluster
        """
        raise NotImplementedError

    def delete_cluster(self):
        """
        This method is to be called in order to unprovision a cluster
        """
        raise NotImplementedError
