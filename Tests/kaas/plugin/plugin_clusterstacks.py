import logging
import os
import os.path
import time

from jinja2 import Environment
from kubernetes.client import ApiClient, ApiException
import yaml

from interface import KubernetesClusterPlugin
import cs_helper as _csh

logger = logging.getLogger(__name__)
logging.getLogger("kubernetes").setLevel(logging.INFO)


TEMPLATE_KEYS = ('cluster', 'clusterstack', 'kubeconfig')


class _ClusterOps:
    def __init__(self, namespace: str, name: str):
        self.namespace = namespace
        self.name = name
        self.secret_name = f'{name}-kubeconfig'

    def _get_condition_ready(self, co_api: _csh.CustomObjectsApi):
        # be defensive here, for none of the fields need exist in early stages of the object's life
        status = _csh.get_cluster_status(co_api, self.namespace, self.name).get('status', {})
        return bool([
            cond
            for cond in status.get('conditions', ())
            if cond.get('type', '').lower() == 'ready'
            if cond.get('status', '').lower() == 'true'
        ])

    def _get_phase(self, co_api: _csh.CustomObjectsApi):
        try:
            status = _csh.get_cluster_status(co_api, self.namespace, self.name).get('status', {})
            return status.get('phase', 'n/a')
        except ApiException as e:
            if e.status != 404:
                raise
            return None

    def create(self, co_api: _csh.CustomObjectsApi, cluster_dict):
        # repeat this because it's possible that a cluster object exists that is in Deleting phase
        while True:
            logger.debug(f'creating cluster object for {self.name}')
            try:
                _csh.create_cr(co_api, self.namespace, cluster_dict)
            except ApiException as e:
                # 409 means that the object already exists
                if e.status != 409:
                    raise
                # check status: if it's provisioning or provisioned, we are good
                phase = self._get_phase(co_api)
                if phase is None:
                    logger.debug(f'cluster object for {self.name} was present, has disappeared, retry')
                    continue
                logger.debug(f'cluster object for {self.name} already present in phase {phase}')
                if phase.lower() in ('provisioned', 'provisioning'):
                    break
                logger.debug(f'waiting 30 s for cluster {self.name} to vanish or become provisioned')
                time.sleep(30)
            else:
                break

    def delete(self, co_api: _csh.CustomObjectsApi):
        try:
            _csh.delete_cluster(co_api, self.namespace, self.name)
        except ApiException as e:
            if e.status == 404:
                logger.debug(f'cluster {self.name} not present')
                return
            raise
        # wait a bit, because the phase attribute seems to be delayed a bit
        # also, wait a bit longer, because if deletion was just requested (as is typical),
        # it will take at least 5 s (and way longer if the cluster is already running)
        logger.debug(f'cluster {self.name} deletion requested; waiting 8 s for it to vanish')
        time.sleep(8)
        while True:
            phase = self._get_phase(co_api)
            if phase is None:
                break
            if phase.lower() != 'deleting':
                raise RuntimeError(f'cluster {self.name} in phase {phase}; expected: Deleting')
            logger.debug(f'cluster {self.name} still deleting; waiting 30 s for it to vanish')
            time.sleep(30)

    def get_kubeconfig(self, core_api: _csh.CoreV1Api):
        return _csh.get_secret_data(core_api, self.namespace, self.secret_name)

    def wait_for_cluster_ready(self, co_api: _csh.CustomObjectsApi):
        while not self._get_condition_ready(co_api):
            logger.debug(f'waiting 30 s for cluster {self.name} to become ready')
            time.sleep(30)
        logger.debug(f'cluster {self.name} appears to be ready')


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
    Plugin to handle the provisioning of Kubernetes clusters based on ClusterStacks approach
    to be used for conformance testing

    So far, tested with Syself implementation only. Other ClusterStacks implementations may
    require a bit of adaptation, e.g., when it comes to the name of the secret that holds
    the created cluster's kubeconfig.
    """
    def __init__(self, config, basepath='.', cwd='.'):
        self.basepath = basepath
        self.cwd = cwd
        self.config = config
        self.env = Environment()
        self.template_map = load_templates(self.env, self.basepath, self.config['templates'])
        self.vars = self.config['vars']
        self.vars['name'] = self.config['name']
        self.secrets = self.config['secrets']
        self.kubeconfig = yaml.load(self._render_template('kubeconfig'), Loader=yaml.SafeLoader)
        self.client_config = _csh.Configuration()
        _csh.setup_client_config(self.client_config, self.kubeconfig, cwd=self.cwd)
        self.namespace = self.kubeconfig['contexts'][0]['context']['namespace']

    def _render_template(self, key):
        return self.template_map[key].render(**self.vars, **self.secrets)

    def _auto_vars_syself(self, api_instance: _csh.CustomObjectsApi):
        logging.debug('using autoVars/syself')
        # filter clusterstackreleases by readiness and kubernetesVersion
        version_prefix = f"v{self.config['kubernetesVersion']}."
        # select fields of interest: name, version
        items = [
            (item['metadata']['name'], item['status']['kubernetesVersion'])
            for item in _csh.get_clusterstackreleases(api_instance, self.namespace)
            if item['status']['ready']
            if item['status']['kubernetesVersion'].startswith(version_prefix)
        ]
        logging.debug(f'matching ClusterStackReleases: {items}')
        if not items:
            raise RuntimeError(f'autoVars/syself failed: no ClusterStackRelease found for {version_prefix}x')
        # select latest patch version (assume patch part is numeric)
        cs_class_name, cs_version = max(items, key=lambda item: int(item[1].rsplit('.', 1)[-1]))
        return {'cs_class_name': cs_class_name, 'cs_version': cs_version}

    def _auto_vars(self, auto_vars_kind, co_api: _csh.CustomObjectsApi):
        # set default values regardless of auto_vars_kind
        self.vars.setdefault('num_control_nodes', 3)
        self.vars.setdefault('num_worker_nodes', 3)
        # now on to specifics
        if not auto_vars_kind:
            return
        if auto_vars_kind == 'syself':
            auto_vars = self._auto_vars_syself(co_api)
        else:
            raise RuntimeError(f'unknown kind of autoVars: {auto_vars_kind}')
        logger.debug(f'applying autoVars/{auto_vars_kind}: {auto_vars}')
        self.vars.update(auto_vars)

    def _write_cluster_yaml(self, cluster_yaml):
        # write out cluster.yaml for purposes of documentation
        # we will however use the dict instead of calling the shell with `kubectl apply -f`
        cluster_yaml_path = os.path.join(self.cwd, 'cluster.yaml')
        logger.debug(f'writing out {cluster_yaml_path}')
        with open(cluster_yaml_path, "w") as fileobj:
            fileobj.write(cluster_yaml)

    def _write_kubeconfig(self, kubeconfig):
        # write out kubeconfig.yaml
        kubeconfig_path = os.path.join(self.cwd, 'kubeconfig.yaml')
        logger.debug(f'writing out {kubeconfig_path}')
        with open(kubeconfig_path, 'wb') as fileobj:
            fileobj.write(kubeconfig)

    def create_cluster(self):
        with ApiClient(self.client_config) as api_client:
            core_api = _csh.CoreV1Api(api_client)
            co_api = _csh.CustomObjectsApi(api_client)
            self._auto_vars(self.config.get('autoVars'), co_api)
            cluster_yaml = self._render_template('cluster')
            cluster_dict = yaml.load(cluster_yaml, Loader=yaml.SafeLoader)
            self._write_cluster_yaml(cluster_yaml)
            cops = _ClusterOps(self.namespace, self.config['name'])
            cops.create(co_api, cluster_dict)
            cops.wait_for_cluster_ready(co_api)
            self._write_kubeconfig(cops.get_kubeconfig(core_api))

    def delete_cluster(self):
        with ApiClient(self.client_config) as api_client:
            co_api = _csh.CustomObjectsApi(api_client)
            _ClusterOps(self.namespace, self.config['name']).delete(co_api)
