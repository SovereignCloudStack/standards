class KubernetesClusterPlugin():
    """
    An abstract base class for writing Kubernetes cluster provider plugins.

    - Implement the methods `create_cluster` and `delete_cluster`.
    - Create the method `__init__(self, config, basepath, cwd)` to
      handle API-specific configuration.

    Example:
        .. code:: python
          import os.path

          from interface import KubernetesClusterPlugin
          from apiX_library import cluster_api_class as ClusterAPI

          class PluginX(KubernetesClusterPlugin):

              def __init__(self, config, basepath, cwd):
                  self.config = config
                  self.basepath = basepath  # find other config files here
                  self.cwd = cwd  # create new files here

              def create_cluster(self):
                  kubeconfig_path = os.path.join(self.cwd, 'kubeconfig.yaml')
                  ClusterAPI(name=self.config['name']).create(kubeconfig_path)

              def delete_cluster(self, cluster_name):
                  ClusterAPI(name=self.config['name']).delete()
        ..
    """

    def create_cluster(self):
        raise NotImplementedError

    def delete_cluster(self):
        raise NotImplementedError
