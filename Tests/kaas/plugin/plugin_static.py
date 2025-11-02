import os.path
import shutil

from interface import KubernetesClusterPlugin


class PluginStatic(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of Kubernetes clusters based on "no-op"
    to be used for conformance testing -- no-op meaning that no cluster is
    provisioned, but a given cluster is used.

    Specifically, use the kubeconfig file given by `config['kubeconfig']`.
    """

    def __init__(self, config, basepath='.', cwd='.'):
        self.config = config
        self.basepath = basepath
        self.cwd = cwd

    def create_cluster(self):
        dst_path = os.path.normpath(os.path.join(self.cwd, 'kubeconfig.yaml'))
        src_path = self.config['kubeconfig']
        if not os.path.isabs(src_path):
            src_path = os.path.normpath(os.path.join(self.basepath, src_path))
        if src_path == dst_path:
            return
        shutil.copyfile(src_path, dst_path)

    def delete_cluster(self):
        pass
