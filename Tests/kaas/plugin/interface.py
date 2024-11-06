from abc import abstractmethod


class KubernetesClusterPlugin():
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes
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
        :param: cluster_uuid:
        """
