import logging
import os
import os.path
import time

from jinja2 import Environment, StrictUndefined
from kubernetes.client import ApiClient, ApiException
import yaml

from interface import KubernetesClusterPlugin
import gardener_helper as _gh

logger = logging.getLogger(__name__)
logging.getLogger("kubernetes").setLevel(logging.INFO)


TEMPLATE_KEYS = ('shoot', 'kubeconfig')
TIMEOUTS = [30] * 40 + [0]  # wait at most 1200 seconds (20 minutes); sentinel value at the end


class _ShootOps:
    def __init__(self, namespace: str, name: str):
        self.namespace = namespace
        self.name = name

    def _get_last_operation(self, co_api: _gh.CustomObjectsApi):
        try:
            status = _gh.get_shoot_status(co_api, self.namespace, self.name).get('status', {})
            return status.get('lastOperation', {})
        except ApiException as e:
            if e.status != 404:
                raise
            return None

    def create(self, co_api: _gh.CustomObjectsApi, shoot_dict):
        # Gardener shoot reconciliation is idempotent, so we can just try to create.
        # If it exists, we check its state.
        # repeat this because it's possible that a cluster object exists that is in state Delete
        timeouts = iter(TIMEOUTS)
        while True:
            logger.debug(f"creating shoot object for {self.name}")
            try:
                _gh.create_shoot(co_api, self.namespace, shoot_dict)
            except ApiException as e:
                # 409 means that the object already exists
                if e.status != 409:
                    raise
                # check state: if it's Processing or Succeeded, we are good
                last_op = self._get_last_operation(co_api)
                if last_op is None:
                    logger.debug(f'cluster object for {self.name} was present, has disappeared, retry')
                    continue
                state = last_op.get('state', 'Unknown')
                logger.debug(f"Shoot object for {self.name} already present in state {state}")
                if state in ('Succeeded', 'Processing'):
                    break
                if state == 'Failed':
                    raise RuntimeError(f"Shoot {self.name} is in Failed state. Please check the Gardener dashboard.")

                timeout = next(timeouts)
                if not timeout:
                    raise RuntimeError(f"Timeout error while waiting on shoot {self.name}")
                logger.debug(f'waiting {timeout} s for shoot {self.name} to proceed')
                time.sleep(timeout)
            else:
                break

    def delete(self, co_api: _gh.CustomObjectsApi):
        # Add deletion confirmation annotation to the shoot before deleting.
        # This is required by Gardener.
        try:
            _gh.annotate_shoot_confirm_deletion(co_api, self.namespace, self.name)
            _gh.delete_shoot(co_api, self.namespace, self.name)
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Shoot {self.name} not present")
                return
            raise

        logger.debug(f"Shoot {self.name} deletion requested; waiting 8 s for it to start deleting")
        time.sleep(8)
        timeouts = iter(TIMEOUTS)
        while True:
            last_op = self._get_last_operation(co_api)
            if last_op is None:
                logger.info(f"Shoot {self.name} has been deleted.")
                break

            timeout = next(timeouts)
            if not timeout:
                raise RuntimeError(f"Shoot {self.name} has not gone away in time")

            state = last_op.get('state', 'Unknown')
            if last_op.get('type') != 'Delete':
                logger.debug(f"Shoot {self.name} in unexpected state during deletion: {last_op!r}; waiting {timeout} s")
            elif state == 'Processing':
                progress = last_op.get('progress', 0)
                logger.debug(f"Shoot {self.name} is being deleted (progress: {progress} %); waiting {timeout} s")
            elif state == 'Succeeded':
                logger.info(f"Shoot {self.name} deletion succeeded, but object still exists. Waiting {timeout} s for it to vanish.")
            else:
                raise RuntimeError(f"Shoot {self.name} in unexpected state during deletion: state={state}")
            time.sleep(timeout)

    def get_kubeconfig(self, api_client: ApiClient):
        return _gh.request_kubeconfig(api_client, self.namespace, self.name)

    def wait_for_shoot_ready(self, co_api: _gh.CustomObjectsApi):
        timeouts = iter(TIMEOUTS)
        while True:
            last_op = self._get_last_operation(co_api)
            if last_op is None:
                raise RuntimeError(f"Shoot {self.name} object disappeared")

            state = last_op.get('state', 'Unknown')
            if state == 'Succeeded':
                logger.debug(f'shoot {self.name} appears to be ready')
                return
            if state not in ('Unknown', 'Processing'):
                raise RuntimeError(f"Shoot {self.name} object in unexpected state {last_op.get('state')}")

            timeout = next(timeouts)
            if not timeout:
                raise RuntimeError(f"Shoot {self.name} has not become ready in time")
            progress = last_op.get('progress', 0)
            logger.debug(f'waiting {timeout} s for shoot {self.name} to become ready (current state: {state}, progress: {progress}%)')
            time.sleep(timeout)


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


class PluginGardener(KubernetesClusterPlugin):
    """
    Plugin to handle the provisioning of Kubernetes clusters via Gardener
    to be used for conformance testing.
    """
    def __init__(self, plugin_config, basepath='.', cwd='.', name=None):
        self.basepath = basepath
        self.cwd = cwd
        self.config = plugin_config
        self.env = Environment(undefined=StrictUndefined)
        self.template_map = load_templates(self.env, self.basepath, self.config['templates'])
        self.vars = self.config['vars']
        self.vars['name'] = self.config['name']
        self.secrets = self.config['secrets']
        self.kubeconfig = yaml.load(self._render_template('kubeconfig'), Loader=yaml.SafeLoader)
        self.client_config = _gh.Configuration()
        _gh.setup_client_config(self.client_config, self.kubeconfig, cwd=self.cwd)
        self.namespace = self.kubeconfig['contexts'][0]['context']['namespace']

    def _render_template(self, key):
        return self.template_map[key].render(**self.vars, **self.secrets)

    def _auto_vars_noris(self, api_instance: _gh.CustomObjectsApi):
        logging.debug('using autoVars/noris')
        cloud_profile = _gh.get_cloudprofile(api_instance, self.namespace, self.vars['cloud_profile_name'])
        version_items = cloud_profile['spec']['kubernetes']['versions']
        # filter by kubernetesVersion and classification==supported
        version_prefix = f"{self.config['kubernetesVersion']}."
        versions = [
            item['version']
            for item in version_items
            if item['classification'] == 'supported'
            if item['version'].startswith(version_prefix)
        ]
        logging.debug(f'matching k8s versions: {versions}')
        if not versions:
            raise RuntimeError(f'autoVars/noris failed: no versions found for v{version_prefix}x')
        # select latest patch version (assume patch part is numeric)
        selected_version = max(versions, key=lambda ver: int(ver.rsplit('.', 1)[-1]))
        return {'kubernetes_version': selected_version}

    def _auto_vars(self, auto_vars_kind, co_api: _gh.CustomObjectsApi):
        # set default values regardless of auto_vars_kind
        self.vars.setdefault('num_worker_nodes', 3)
        # now on to specifics
        if not auto_vars_kind:
            return
        if auto_vars_kind == 'noris':
            auto_vars = self._auto_vars_noris(co_api)
        else:
            raise RuntimeError(f'unknown kind of autoVars: {auto_vars_kind}')
        logger.debug(f'applying autoVars/{auto_vars_kind}: {auto_vars}')
        self.vars.update(auto_vars)

    def _write_shoot_yaml(self, shoot_yaml):
        # write out shoot.yaml for purposes of documentation
        # we will however use the dict instead of calling the shell with `kubectl apply -f`
        shoot_yaml_path = os.path.join(self.cwd, 'shoot.yaml')
        logger.debug(f'writing out {shoot_yaml_path}')
        with open(shoot_yaml_path, "w") as fileobj:
            fileobj.write(shoot_yaml)

    def _write_kubeconfig(self, kubeconfig):
        # write out kubeconfig.yaml
        kubeconfig_path = os.path.join(self.cwd, 'kubeconfig.yaml')
        logger.debug(f'writing out {kubeconfig_path}')
        with open(kubeconfig_path, 'wb') as fileobj:
            fileobj.write(kubeconfig)

    def create_cluster(self):
        with ApiClient(self.client_config) as api_client:
            co_api = _gh.CustomObjectsApi(api_client)
            self._auto_vars(self.config.get('autoVars'), co_api)
            shoot_yaml = self._render_template('shoot')
            shoot_dict = yaml.load(shoot_yaml, Loader=yaml.SafeLoader)
            self._write_shoot_yaml(shoot_yaml)
            sops = _ShootOps(self.namespace, self.config['name'])
            sops.create(co_api=co_api, shoot_dict=shoot_dict)
            sops.wait_for_shoot_ready(co_api)
            self._write_kubeconfig(sops.get_kubeconfig(api_client))

    def delete_cluster(self):
        with ApiClient(self.client_config) as api_client:
            co_api = _gh.CustomObjectsApi(api_client)
            _ShootOps(self.namespace, self.config['name']).delete(co_api)
