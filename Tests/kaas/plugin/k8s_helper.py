"""helper functions shared by the Kubernetes-based cluster plugins"""
import base64
import os

from kubernetes.client import Configuration


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
