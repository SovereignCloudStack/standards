"""helper functions for Gardener plugin"""
import base64
import json
import os

from kubernetes.client import Configuration, CustomObjectsApi, ApiClient


GARDENER_GROUP = 'core.gardener.cloud'
GARDENER_VERSION = 'v1beta1'
GARDENER_PLURAL = 'shoots'


def setup_client_config(client_config: Configuration, kubeconfig, cwd='.'):
    """transfer authentication data from kubeconfig to client_config, creating file `ca.crt`s"""
    token = kubeconfig['users'][0]['user']['token']
    client_config.api_key['authorization'] = 'Bearer {}'.format(token)
    client_config.host = kubeconfig['clusters'][0]['cluster']['server']
    client_config.ssl_ca_cert = os.path.abspath(os.path.join(cwd, 'ca.crt'))
    with open(client_config.ssl_ca_cert, "wb") as fileobj:
        fileobj.write(base64.standard_b64decode(
            kubeconfig['clusters'][0]['cluster']['certificate-authority-data'].encode()
        ))


def create_shoot(co_api: CustomObjectsApi, namespace: str, body: dict):
    return co_api.create_namespaced_custom_object(
        group=GARDENER_GROUP,
        version=GARDENER_VERSION,
        namespace=namespace,
        plural=GARDENER_PLURAL,
        body=body,
    )


def delete_shoot(co_api: CustomObjectsApi, namespace: str, name: str):
    return co_api.delete_namespaced_custom_object(
        group=GARDENER_GROUP, version=GARDENER_VERSION, namespace=namespace, plural=GARDENER_PLURAL, name=name,
    )


def annotate_shoot_confirm_deletion(co_api: CustomObjectsApi, namespace: str, name: str):
    shoot_patch = {
        "metadata": {
            "annotations": {
                "confirmation.gardener.cloud/deletion": "true",
            }
        }
    }
    co_api.patch_namespaced_custom_object(
        group=GARDENER_GROUP,
        version=GARDENER_VERSION,
        namespace=namespace,
        plural=GARDENER_PLURAL,
        name=name,
        body=shoot_patch,
    )


def get_shoot_status(co_api: CustomObjectsApi, namespace: str, name: str):
    # Don't use get_namespace_custom_object_status because somehow we're not permitted to do so!
    # The fn get_namespaced_custom_object will do the trick just as well, maybe less efficient?
    return co_api.get_namespaced_custom_object(
        group=GARDENER_GROUP,
        version=GARDENER_VERSION,
        namespace=namespace,
        plural=GARDENER_PLURAL,
        name=name,
    )


def request_kubeconfig(api_client: ApiClient, namespace: str, name: str, expiration_seconds=8*3600):
    # adapted from
    # https://gardener.cloud/docs/gardener/shoot/shoot_access/#shoots-adminkubeconfig-subresource
    kubeconfig_request = {
        'apiVersion': 'authentication.gardener.cloud/v1alpha1',
        'kind': 'AdminKubeconfigRequest',
        'spec': {
            'expirationSeconds': expiration_seconds,
        }
    }
    response = api_client.call_api(
        resource_path=f'/apis/core.gardener.cloud/v1beta1/namespaces/{namespace}/shoots/{name}/adminkubeconfig',
        method='POST',
        body=kubeconfig_request,
        auth_settings=['BearerToken'],
        _preload_content=False,
        _return_http_data_only=True,
    )
    return base64.standard_b64decode(json.loads(response.data)["status"]["kubeconfig"])
