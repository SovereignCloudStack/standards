"""helper functions for Gardener plugin"""
import base64
import os

from kubernetes.client import Configuration, CoreV1Api, CustomObjectsApi


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
    return co_api.get_namespaced_custom_object_status(
        group=GARDENER_GROUP,
        version=GARDENER_VERSION,
        namespace=namespace,
        plural=GARDENER_PLURAL,
        name=name,
    )


# def get_secret_data(core_api: CoreV1Api, namespace: str, name: str):
#     secret = core_api.read_namespaced_secret(name, namespace)
#     return base64.b64decode(secret.data['kubeconfig'])
def get_secret_data(api_instance: CoreV1Api, namespace, secret):
    """mimic `kubectl get secrets NAME -o=jsonpath='{.data.value}' | base64 -d  > kubeconfig.yaml`"""
    res = api_instance.read_namespaced_secret(secret, namespace)
    return base64.standard_b64decode(res.data['value'].encode())
