"""helper functions for ClusterStacks plugin"""
import base64
import os

from kubernetes.client import Configuration, CoreV1Api, CustomObjectsApi


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


def create_cr(api_instance: CustomObjectsApi, namespace, resource_dict):
    """mimic `kubectl apply` (rather create) with a custom resource"""
    group, ver = resource_dict['apiVersion'].split('/', 1)
    plural = resource_dict['kind'].lower() + 's'
    return api_instance.create_namespaced_custom_object(
        group, ver, namespace, plural, resource_dict, field_manager='plugin_clusterstacks',
    )


def get_clusterstackreleases(api_instance: CustomObjectsApi, namespace):
    """mimic `kubectl get clusterstackreleases`"""
    return api_instance.list_namespaced_custom_object(
        'clusterstack.x-k8s.io', 'v1alpha1', namespace, 'clusterstackreleases',
    )['items']


def get_machines(api_instance: CustomObjectsApi, namespace):
    """mimic `kubectl get machines`"""
    return api_instance.list_namespaced_custom_object(
        'cluster.x-k8s.io', 'v1beta1', namespace, 'machines',
    )['items']


def get_secret_data(api_instance: CoreV1Api, namespace, secret):
    """mimic `kubectl get secrets NAME -o=jsonpath='{.data.value}' | base64 -d  > kubeconfig.yaml`"""
    res = api_instance.read_namespaced_secret(secret, namespace)
    return base64.standard_b64decode(res.data['value'].encode())


def get_cluster_status(api_instance: CustomObjectsApi, namespace, name):
    return api_instance.get_namespaced_custom_object_status(
        'cluster.x-k8s.io', 'v1beta1', namespace, 'clusters', name
    )


def delete_cluster(api_instance: CustomObjectsApi, namespace, name):
    """mimic `kubectl delete cluster`"""
    # beware: do not fiddle with propagation policy here, as this may lead to severe problems
    return api_instance.delete_namespaced_custom_object(
        'cluster.x-k8s.io', 'v1beta1', namespace, 'clusters', name,
    )
