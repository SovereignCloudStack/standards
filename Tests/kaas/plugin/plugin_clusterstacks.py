import base64
import logging
import os
import os.path
from pathlib import Path

from interface import KubernetesClusterPlugin
from jinja2 import Environment
import kubernetes
import yaml

logger = logging.getLogger(__name__)


TEMPLATE_KEYS = ('cluster', 'clusterstack', 'kubeconfig')


def load_templates(env, basepath, fn_map, keys=TEMPLATE_KEYS):
    new_map = {}
    for key in keys:
        fn = fn_map.get(key)
        if fn is None:
            new_map[key] = None
            continue
        with open(os.path.join(basepath, fn), "r") as fileobj:
            new_map[key] = env.from_string(fileobj.read())
    missing = [key for k, v in new_map.items() if v is None]
    if missing:
        raise RuntimeError(f'missing templates: {", ".join(missing)}')
    return new_map


class PluginClusterStacks(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of kubernetes cluster for
    conformance testing purpose with the use of Kind
    """
    def __init__(self, config, basepath='.', cwd='.'):
        self.basepath = basepath
        self.cwd = cwd
        self.config = config
        logger.debug(self.config)
        self.env = Environment()
        self.template_map = load_templates(self.env, self.basepath, self.config['templates'])
        self.vars = self.config['vars']
        self.vars['name'] = self.config['name']
        self.secrets = self.config['secrets']
        self.kubeconfig = yaml.load(
            self.template_map['kubeconfig'].render(**self.vars, **self.secrets),
            Loader=yaml.SafeLoader,
        )
        self.client_config = kubernetes.client.Configuration()
        token = self.kubeconfig['users'][0]['user']['token']
        self.client_config.api_key['authorization'] = 'Bearer {}'.format(token)
        self.client_config.host = self.kubeconfig['clusters'][0]['cluster']['server']
        self.client_config.ssl_ca_cert = os.path.abspath(os.path.join(self.cwd, 'ca.crt'))
        with open(self.client_config.ssl_ca_cert, "wb") as fileobj:
            fileobj.write(base64.standard_b64decode(self.kubeconfig['clusters'][0]['cluster']['certificate-authority-data'].encode()))
        self.namespace = self.kubeconfig['contexts'][0]['context']['namespace']

    def auto_vars_syself(self, api_client):
        # beware: the following is quite the incantation
        prefix = f"v{self.config['kubernetesVersion']}"
        api_instance = kubernetes.client.CustomObjectsApi(api_client)
        # mimic `kubectl get clusterstackrelease` (it's a bit more involved with the API)
        res = api_instance.list_namespaced_custom_object('clusterstack.x-k8s.io', 'v1alpha1', self.namespace, 'clusterstackreleases')
        # filter items by readiness and kubernetesVersion, select fields of interest: name, version
        items = [
          (item['metadata']['name'], item['status']['kubernetesVersion'])
          for item in res['items']
          if item['status']['ready']
          if item['status']['kubernetesVersion'].startswith(prefix)
        ]
        # sort filtered result by patch version
        items.sort(key=lambda item: item[1].rsplit('.', 1)[-1])
        # select latest
        cs_class_name, cs_version = items[-1]
        self.vars.setdefault('cs_class_name', cs_class_name)
        self.vars.setdefault('cs_version', cs_version)

    def create_cluster(self):
        with kubernetes.client.ApiClient(self.client_config) as api_client:
            if self.config.get('autoVars') == 'syself':
                self.auto_vars_syself(api_client)
            # write out cluster.yaml for purposes of documentation; we won't use kubectl apply -f
            cluster_yaml = self.template_map['cluster'].render(**self.vars)
            cluster_dict = yaml.load(cluster_yaml, Loader=yaml.SafeLoader)
            with open(os.path.join(self.cwd, 'cluster.yaml'), "w") as fileobj:
                fileobj.write(cluster_yaml)
            # kubernetes.utils.create_from_dict(api_client, cluster_dict)
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            # mimic `kubectl apply -f` (it's a bit more involved with the API)
            res = api_instance.create_namespaced_custom_object('cluster.x-k8s.io', 'v1beta1', self.namespace, 'clusters', cluster_dict, field_manager='plugin_clusterstacks')

    def delete_cluster(self):
        cluster_name = self.config['name']
        KindCluster(cluster_name).delete()
