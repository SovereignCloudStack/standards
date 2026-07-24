import base64
import logging
import os
import os.path
import time
from typing import Any, cast

from jinja2 import Environment, Template
from kubernetes.client import ApiClient, ApiException, Configuration, CoreV1Api, CustomObjectsApi, V1Secret
import yaml

from interface import KubernetesClusterPlugin
import k8s_helper

logger = logging.getLogger(__name__)
logging.getLogger("kubernetes").setLevel(logging.INFO)


TIMEOUTS = [30] * 60 + [0]  # wait at most 30 minutes; sentinel value at the end

HR_GROUP = "helm.toolkit.fluxcd.io"
HR_VERSION = "v2"
HR_PLURAL = "helmreleases"


class PluginT8s(KubernetesClusterPlugin):
    """
    Plugin to provision Kubernetes clusters on the t8s (teuto k8s) management cluster
    via a Flux HelmRelease.

    Creates a HelmRelease on mgmt-bfe2-prod and waits for the resulting cluster's
    kubeconfig to appear in the secret scs-kaas-certification-kubeconfig.

    Expected config keys:
      kubernetesVersion: '1.35'        (major.minor)
      version_patch:     2             (patch component of the k8s version)
      templates:
        kubeconfig: t8s-kubeconfig.yaml  (management cluster kubeconfig template)
      secrets:
        token: '{{ clouds_conf.teuto_mgmt_token }}'
    """

    def __init__(self, config: dict[str, Any], basepath: str = ".", cwd: str = ".") -> None:
        self.basepath = basepath
        self.cwd = cwd
        self.env = Environment()

        # All of these are mandated by the ValidatingAdmissionPolicy on the management cluster
        # and cannot be changed without updating both the VAP and the RBAC. They are instance
        # (rather than module-level) attributes because, in principle, different certification
        # targets could be configured with different values here.
        self.hr_name = "scs-kaas-certification"
        self.hr_namespace = "scs-kaas-certification"
        self.hr_kubeconfig_secret = "scs-kaas-certification-kubeconfig"
        self.hr_chart_ref: dict[str, str] = {
            "kind": "HelmChart",
            "name": "scs-kaas-certification",
            "namespace": "flux-system",
        }
        self.hr_values_fixed: dict[str, Any] = {
            "cloud": "bfe2-prod",
            "controlPlane": {"hosted": True},
            "metadata": {
                "customerID": 1111,
                "customerName": "teuto.net Netzdienste GmbH",
                "friendlyName": "scs-kaas-certification",
                "serviceLevelAgreement": "None",
            },
            "nodePools": {
                "pool-0": {"flavor": "standard.2.1905", "replicas": 2},
            },
        }

        fn: str = config["templates"]["kubeconfig"]
        with open(os.path.join(basepath, fn), "r") as f:
            self.kubeconfig_template: Template = self.env.from_string(f.read())
        self.secrets: dict[str, Any] = config.get("secrets", {})

        major, minor = (int(x) for x in config["kubernetesVersion"].split("."))
        self.k8s_version: dict[str, int] = {
            "major": major,
            "minor": minor,
            "patch": int(config.get("version_patch", 0)),
        }

        kubeconfig = cast(dict[str, Any], yaml.load(
            self.kubeconfig_template.render(**self.secrets), Loader=yaml.SafeLoader
        ))
        self.client_config: Configuration = Configuration()
        k8s_helper.setup_client_config(self.client_config, kubeconfig, cwd=self.cwd)

    def _build_helmrelease(self) -> dict[str, Any]:
        return {
            "apiVersion": f"{HR_GROUP}/{HR_VERSION}",
            "kind": "HelmRelease",
            "metadata": {"name": self.hr_name, "namespace": self.hr_namespace},
            "spec": {
                "chartRef": self.hr_chart_ref,
                "driftDetection": {"mode": "enabled"},
                "interval": "1m",
                "values": {**self.hr_values_fixed, "version": self.k8s_version},
            },
        }

    def _delete_helmrelease(self, co_api: CustomObjectsApi) -> None:
        try:
            co_api.delete_namespaced_custom_object(
                HR_GROUP,
                HR_VERSION,
                self.hr_namespace,
                HR_PLURAL,
                self.hr_name,
            )
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"HelmRelease {self.hr_name} not present, nothing to delete")
                return
            raise
        # Give Flux time to begin deletion before we try to recreate
        logger.debug(f"HelmRelease {self.hr_name} deletion requested; waiting 30s")
        time.sleep(30)

    def _apply_helmrelease(self, api_client: ApiClient) -> None:
        """Server-side apply the HelmRelease (creates or updates).

        Uses PATCH with application/apply-patch+yaml so the resource name is
        part of the URL — meaning resourceNames RBAC constraints are evaluated
        correctly, unlike POST (create) where the name is only in the body.
        """
        hr = self._build_helmrelease()
        api_client.call_api(
            '/apis/{group}/{version}/namespaces/{namespace}/{plural}/{name}',
            'PATCH',
            path_params={
                'group': HR_GROUP,
                'version': HR_VERSION,
                'namespace': self.hr_namespace,
                'plural': HR_PLURAL,
                'name': self.hr_name,
            },
            query_params=[('fieldManager', 'plugin_t8s'), ('force', 'true')],
            header_params={
                'Accept': 'application/json',
                'Content-Type': 'application/apply-patch+yaml',
            },
            body=hr,
            post_params=[],
            files={},
            response_type='object',
            auth_settings=['BearerToken'],
            _return_http_data_only=True,
        )
        logger.debug(f"HelmRelease {self.hr_name} applied")

    def _get_kubeconfig_from_secret(self, core_api: CoreV1Api) -> bytes:
        secret = cast(V1Secret, core_api.read_namespaced_secret(self.hr_kubeconfig_secret, self.hr_namespace))
        data: dict[str, str] = secret.data or {}
        if "value" in data:
            return base64.standard_b64decode(data["value"].encode())
        raise RuntimeError(
            f"kubeconfig secret {self.hr_kubeconfig_secret} is missing key 'value'; has keys: {list(data)}"
        )

    def _wait_for_kubeconfig_secret(self, core_api: CoreV1Api) -> bytes:
        timeouts = iter(TIMEOUTS)
        while True:
            try:
                return self._get_kubeconfig_from_secret(core_api)
            except ApiException as e:
                if e.status != 404:
                    raise
            timeout = next(timeouts)
            if not timeout:
                raise RuntimeError(
                    f"Timeout waiting for kubeconfig secret {self.hr_kubeconfig_secret}"
                )
            logger.debug(
                f"waiting {timeout}s for kubeconfig secret {self.hr_kubeconfig_secret}"
            )
            time.sleep(timeout)

    def _write_kubeconfig(self, data: bytes) -> None:
        path = os.path.join(self.cwd, "kubeconfig.yaml")
        logger.debug(f"writing {path}")
        with open(path, "wb") as f:
            f.write(data)

    def create_cluster(self) -> None:
        with ApiClient(self.client_config) as api_client:
            core_api = CoreV1Api(api_client)
            self._apply_helmrelease(api_client)
            kubeconfig = self._wait_for_kubeconfig_secret(core_api)
            self._write_kubeconfig(kubeconfig)

    def delete_cluster(self) -> None:
        with ApiClient(self.client_config) as api_client:
            co_api = CustomObjectsApi(api_client)
            self._delete_helmrelease(co_api)
