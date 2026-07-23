import base64
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml
from kubernetes.client import ApiException, V1Secret

from plugin_t8s import (
    HR_GROUP,
    HR_VERSION,
    PluginT8s,
)


MINIMAL_KUBECONFIG = {
    "apiVersion": "v1",
    "kind": "Config",
    "clusters": [{"cluster": {
        "certificate-authority-data": base64.b64encode(b"fake-ca").decode(),
        "server": "https://test:6443",
    }, "name": "test"}],
    "contexts": [{"context": {"cluster": "test", "namespace": "scs-kaas-certification", "user": "test"}, "name": "default"}],
    "current-context": "default",
    "users": [{"name": "test", "user": {"token": "test-token"}}],
}

KUBECONFIG_TEMPLATE = yaml.dump(MINIMAL_KUBECONFIG)


@pytest.fixture
def plugin(tmp_path):
    tpl = tmp_path / "t8s-kubeconfig.yaml"
    tpl.write_text(KUBECONFIG_TEMPLATE)
    config = {
        "kubernetesVersion": "1.35",
        "version_patch": 2,
        "templates": {"kubeconfig": tpl.name},
        "secrets": {},
    }
    with patch("k8s_helper.setup_client_config"):
        return PluginT8s(config, basepath=str(tmp_path), cwd=str(tmp_path))


# --- _build_helmrelease ---

def test_helmrelease_apiversion(plugin):
    hr = plugin._build_helmrelease()
    assert hr["apiVersion"] == f"{HR_GROUP}/{HR_VERSION}"


def test_helmrelease_kind(plugin):
    hr = plugin._build_helmrelease()
    assert hr["kind"] == "HelmRelease"


def test_helmrelease_name_namespace(plugin):
    hr = plugin._build_helmrelease()
    assert hr["metadata"]["name"] == plugin.hr_name
    assert hr["metadata"]["namespace"] == plugin.hr_namespace


def test_helmrelease_chartref(plugin):
    hr = plugin._build_helmrelease()
    assert hr["spec"]["chartRef"] == plugin.hr_chart_ref
    assert hr["spec"]["chartRef"]["kind"] == "HelmChart"
    assert hr["spec"]["chartRef"]["name"] == "scs-kaas-certification"
    assert hr["spec"]["chartRef"]["namespace"] == "flux-system"


def test_helmrelease_drift_detection(plugin):
    hr = plugin._build_helmrelease()
    assert hr["spec"]["driftDetection"]["mode"] == "enabled"


def test_helmrelease_interval(plugin):
    hr = plugin._build_helmrelease()
    assert hr["spec"]["interval"] == "1m"


def test_helmrelease_values_cloud(plugin):
    assert plugin._build_helmrelease()["spec"]["values"]["cloud"] == "bfe2-prod"


def test_helmrelease_values_control_plane(plugin):
    assert plugin._build_helmrelease()["spec"]["values"]["controlPlane"]["hosted"] is True


def test_helmrelease_values_metadata(plugin):
    meta = plugin._build_helmrelease()["spec"]["values"]["metadata"]
    assert meta["customerID"] == 1111
    assert meta["customerName"] == "teuto.net Netzdienste GmbH"
    assert meta["friendlyName"] == "scs-kaas-certification"
    assert meta["serviceLevelAgreement"] == "None"


def test_helmrelease_values_nodepool(plugin):
    pool = plugin._build_helmrelease()["spec"]["values"]["nodePools"]["pool-0"]
    assert pool["flavor"] == "standard.2.1905"
    assert pool["replicas"] == 2


def test_helmrelease_values_version_135(plugin):
    v = plugin._build_helmrelease()["spec"]["values"]["version"]
    assert v == {"major": 1, "minor": 35, "patch": 2}


def test_helmrelease_values_no_extra_keys(plugin):
    allowed = {"cloud", "controlPlane", "metadata", "nodePools", "version"}
    assert set(plugin._build_helmrelease()["spec"]["values"].keys()) == allowed


def test_helmrelease_metadata_no_extra_keys(plugin):
    allowed = {"customerID", "customerName", "friendlyName", "serviceLevelAgreement"}
    assert set(plugin._build_helmrelease()["spec"]["values"]["metadata"].keys()) == allowed


def test_helmrelease_nodepool_no_extra_keys(plugin):
    assert set(plugin._build_helmrelease()["spec"]["values"]["nodePools"]["pool-0"].keys()) == {"flavor", "replicas"}


def test_helmrelease_version_no_extra_keys(plugin):
    assert set(plugin._build_helmrelease()["spec"]["values"]["version"].keys()) == {"major", "minor", "patch"}


def test_helmrelease_single_nodepool(plugin):
    nodepools = plugin._build_helmrelease()["spec"]["values"]["nodePools"]
    assert len(nodepools) == 1
    assert "pool-0" in nodepools


# --- version parsing ---

@pytest.mark.parametrize("version,version_patch,expected", [
    ("1.35", 2,  {"major": 1, "minor": 35, "patch": 2}),
    ("1.36", 0,  {"major": 1, "minor": 36, "patch": 0}),
    ("1.34", 10, {"major": 1, "minor": 34, "patch": 10}),
])
def test_version_parsing(tmp_path, version, version_patch, expected):
    tpl = tmp_path / "t8s-kubeconfig.yaml"
    tpl.write_text(KUBECONFIG_TEMPLATE)
    config = {
        "kubernetesVersion": version,
        "version_patch": version_patch,
        "templates": {"kubeconfig": tpl.name},
        "secrets": {},
    }
    with patch("k8s_helper.setup_client_config"):
        p = PluginT8s(config, basepath=str(tmp_path), cwd=str(tmp_path))
    assert p.k8s_version == expected


def test_version_patch_defaults_to_zero(tmp_path):
    tpl = tmp_path / "t8s-kubeconfig.yaml"
    tpl.write_text(KUBECONFIG_TEMPLATE)
    config = {
        "kubernetesVersion": "1.35",
        "templates": {"kubeconfig": tpl.name},
        "secrets": {},
    }
    with patch("k8s_helper.setup_client_config"):
        p = PluginT8s(config, basepath=str(tmp_path), cwd=str(tmp_path))
    assert p.k8s_version["patch"] == 0


# --- _get_kubeconfig_from_secret ---

def test_get_kubeconfig_from_secret(plugin):
    raw = b"apiVersion: v1\nkind: Config\n"
    secret = MagicMock(spec=V1Secret)
    secret.data = {"value": base64.b64encode(raw).decode()}
    core_api = MagicMock()
    core_api.read_namespaced_secret.return_value = secret
    assert plugin._get_kubeconfig_from_secret(core_api) == raw
    core_api.read_namespaced_secret.assert_called_once_with(plugin.hr_kubeconfig_secret, plugin.hr_namespace)


def test_get_kubeconfig_from_secret_null_data(plugin):
    secret = MagicMock(spec=V1Secret)
    secret.data = None
    core_api = MagicMock()
    core_api.read_namespaced_secret.return_value = secret
    with pytest.raises(RuntimeError, match="missing key 'value'"):
        plugin._get_kubeconfig_from_secret(core_api)


def test_get_kubeconfig_from_secret_wrong_key(plugin):
    secret = MagicMock(spec=V1Secret)
    secret.data = {"kubeconfig": base64.b64encode(b"x").decode()}
    core_api = MagicMock()
    core_api.read_namespaced_secret.return_value = secret
    with pytest.raises(RuntimeError, match="missing key 'value'"):
        plugin._get_kubeconfig_from_secret(core_api)


# --- _wait_for_kubeconfig_secret ---

def test_wait_retries_on_404(plugin):
    raw = b"kubeconfig-data"
    secret = MagicMock(spec=V1Secret)
    secret.data = {"value": base64.b64encode(raw).decode()}
    not_found = ApiException(status=404)
    core_api = MagicMock()
    core_api.read_namespaced_secret.side_effect = [not_found, not_found, secret]

    with patch("plugin_t8s.TIMEOUTS", [0.01, 0.01, 0]):
        with patch("time.sleep"):
            # _get_kubeconfig_from_secret is called, but read_namespaced_secret side_effect
            # drives it — patch TIMEOUTS so we don't wait 30s
            # Need to make the third call return the secret not raise
            core_api.read_namespaced_secret.side_effect = [not_found, not_found, secret]
            result = plugin._wait_for_kubeconfig_secret(core_api)
    assert result == raw


def test_wait_raises_on_non_404(plugin):
    core_api = MagicMock()
    core_api.read_namespaced_secret.side_effect = ApiException(status=403)
    with pytest.raises(ApiException):
        plugin._wait_for_kubeconfig_secret(core_api)
