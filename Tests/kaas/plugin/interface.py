

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
    - Create `__init__(self, config_file=None)` method to handle api specific
      configurations.

    Example:
        .. code:: python

          from interface import KubernetesClusterPlugin
          from apiX_library import cluster_api_class as ClusterAPI

          class PluginX(KubernetesClusterPlugin):

              def __init__(self, config_file):
                  self.config = config_file

              def create_cluster(self, cluster_name, version, kubeconfig_filepath):
                  self.cluster = ClusterAPI(name=cluster_name, image=cluster_image, kubeconfig_filepath)
                  self.cluster.create(self.config)

              def delete_cluster(self, cluster_name, version):
                  self.cluster = ClusterAPI(cluster_name)
                  self.cluster.delete()
        ..
    """

    def create_cluster(self, cluster_name, version, kubeconfig_filepath):
        """
        This method is to be called to create a k8s cluster
        :param: cluster_name:
        :param: version:
        :param: kubeconfig_filepath:
        """
        raise NotImplementedError

    def delete_cluster(self, cluster_name, version):
        """
        This method is to be called in order to unprovision a cluster
        :param: cluster_name:
        :param: version:
        """
        raise NotImplementedError
