import base64
import logging
import os
import os.path
import time

from jinja2 import Environment
import kubernetes
from kubernetes.client.exceptions import ApiException
import yaml

from interface import KubernetesClusterPlugin

logger = logging.getLogger(__name__)


TEMPLATE_KEYS = ('cluster', 'clusterstack', 'kubeconfig')


def _setup_client_config(client_config, kubeconfig, cwd='.'):
    """transfer authentication data from kubeconfig to client_config, creating file `ca.crt`s"""
    token = kubeconfig['users'][0]['user']['token']
    client_config.api_key['authorization'] = 'Bearer {}'.format(token)
    client_config.host = kubeconfig['clusters'][0]['cluster']['server']
    client_config.ssl_ca_cert = os.path.abspath(os.path.join(cwd, 'ca.crt'))
    with open(client_config.ssl_ca_cert, "wb") as fileobj:
        fileobj.write(base64.standard_b64decode(
            kubeconfig['clusters'][0]['cluster']['certificate-authority-data'].encode()
        ))


def _kubectl_apply_cr(api_client, namespace, resource_dict):
    """mimic `kubectl apply` with a custom resource"""
    api_instance = kubernetes.client.CustomObjectsApi(api_client)
    group, ver = resource_dict['apiVersion'].split('/', 1)
    plural = resource_dict['kind'].lower() + 's'
    return api_instance.create_namespaced_custom_object(
        group, ver, namespace, plural, resource_dict, field_manager='plugin_clusterstacks',
    )


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
        self.kubeconfig = yaml.load(self._render_template('kubeconfig'), Loader=yaml.SafeLoader)
        self.client_config = kubernetes.client.Configuration()
        _setup_client_config(self.client_config, self.kubeconfig, cwd=self.cwd)
        self.namespace = self.kubeconfig['contexts'][0]['context']['namespace']

    def _render_template(self, key):
        return self.template_map[key].render(**self.vars, **self.secrets)

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
            # write out cluster.yaml for purposes of documentation
            # we will however use the dict instead of calling the shell with `kubectl apply -f`
            cluster_yaml = self._render_template('cluster')
            cluster_dict = yaml.load(cluster_yaml, Loader=yaml.SafeLoader)
            with open(os.path.join(self.cwd, 'cluster.yaml'), "w") as fileobj:
                fileobj.write(cluster_yaml)
            try:
                _kubectl_apply_cr(api_client, self.namespace, cluster_dict)
            except ApiException as e:
                # 409 means that the object already exists; don't treat that as error
                if e.status != 409:
                    raise
            name = self.config['name']
            secret_name = f'{name}-kubeconfig'
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            while True:
                # mimic `kubectl get machines` (it's a bit more involved with the API)
                res = api_instance.list_namespaced_custom_object('cluster.x-k8s.io', 'v1beta1', self.namespace, 'machines')
                items = [
                    (item['metadata']['name'], item['status']['phase'].lower())
                    for item in res['items']
                    if item['spec']['clusterName'] == name
                ]
                working = [item[0] for item in items if item[1] != 'provisioned']
                if not working:
                    break
                logger.debug('waiting 30 s for machines to become ready:', items)
                time.sleep(30)
            # mimic `kubectl get secrets NAME -o=jsonpath='{.data.value}' | base64 -d  > kubeconfig.yaml`
            res = kubernetes.client.CoreV1Api(api_client).read_namespaced_secret(secret_name, self.namespace)
            with open(os.path.join(self.cwd, 'kubeconfig.yaml'), 'wb') as fileobj:
                fileobj.write(base64.standard_b64decode(res.data['value'].encode()))

    def delete_cluster(self):
        pass  # TODO
