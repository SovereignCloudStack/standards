#!/usr/bin/env python3

"""PersistentVolumeClaims checker

Return codes:
0:    Default StorageClass is available, and setup to SCS standard
1:    Not able to connect to k8s api

31:   Default storage class has no provisioner
32:   None or more then one default Storage Class is defined

41:   Not able to bind PersitantVolume to PersitantVolumeClaim
42:   ReadWriteOnce is not a supported access mode

All return codes between (and including) 1-19 as well as all return codes ending on 9
can be seen as failures.

Check given cloud for conformance with SCS standard regarding
Default StorageClass and PersistentVolumeClaims, to be found under /Standards/scs-0211-v1-kaas-default-storage-class.md

"""

import getopt
import sys
import time
import json
import logging

from kubernetes import client, config
from helper import gen_sonobuoy_result_file

import logging.config

logger = logging.getLogger("k8s-default-storage-class-check")


def setup_k8s_client(kubeconfigfile=None):

    if kubeconfigfile:
        logger.debug(f"using kubeconfig file '{kubeconfigfile}'")
        config.load_kube_config(kubeconfigfile)
    else:
        logger.debug(" useing system kubeconfig")
        config.load_kube_config()

    k8s_api_client = client.CoreV1Api()
    k8s_storage_client = client.StorageV1Api()

    return (
        k8s_api_client,
        k8s_storage_client,
    )


def print_usage(file=sys.stderr):
    """Help output"""
    print(
        """Usage: k8s_storageclass_check.py [options]
This tool checks the requested k8s default storage class according to the SCS Standard 0211 "kaas-default-storage-class".
Options:
 [-k/--kubeconfig PATH_TO_KUBECONFIG] sets kubeconfig file to access kubernetes api
 [-d/--debug] enables DEBUG logging channel
""",
        end="",
        file=file,
    )


def initialize_logging():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class SCSTestException(Exception):
    """Raised when an Specific test did not pass"""

    def __init__(self, *args, return_code: int):
        self.return_code = return_code


def check_default_storageclass(k8s_client_storage):

    api_response = k8s_client_storage.list_storage_class(_preload_content=False)
    storageclasses = api_response.read().decode("utf-8")
    storageclasses_dict = json.loads(storageclasses)

    ndefault_class = 0

    for item in storageclasses_dict["items"]:
        storage_class_name = item["metadata"]["name"]
        annotations = item["metadata"]["annotations"]

        if annotations["storageclass.kubernetes.io/is-default-class"] == "true":
            ndefault_class += 1
            default_storage_class = storage_class_name
            provisioner = item["provisioner"]

    if provisioner == "kubernetes.io/no-provisioner":
        raise SCSTestException(
            f"Provisioner is set to: {provisioner}.",
            "This means the default storage class has no provisioner.",
            return_code=31,
        )

    if ndefault_class != 1:
        raise SCSTestException(
            "More then one or none default StorageClass is defined! ",
            f"Number of defined default StorageClasses = {ndefault_class} ",
            return_code=32,
        )

    logger.info(f"One default Storage Class found:'{default_storage_class}'")
    return default_storage_class


def check_default_persistentvolumeclaim_readwriteonce(k8s_api_instance, storage_class):
    """
    1. Create PersistantVolumeClaim
    2. Create pod which uses the PersitantVolumeClaim
    3. Check if PV got succesfully created using ReadWriteOnce
    4. Delete resources used for testing
    """

    namespace = "default"
    pvc_name = "test-pvc"
    pv_name = "test-pv"
    pod_name = "test-pod"

    # 1. Create PersistantVolumeClaim
    logger.debug(f"create pvc: {pvc_name}")

    pvc_meta = client.V1ObjectMeta(name=pvc_name)
    pvc_resources = client.V1ResourceRequirements(
        requests={"storage": "1Gi"},
    )
    pvc_spec = client.V1PersistentVolumeClaimSpec(
        access_modes=["ReadWriteOnce"],
        storage_class_name=storage_class,
        resources=pvc_resources,
    )
    body_pvc = client.V1PersistentVolumeClaim(
        api_version="v1", kind="PersistentVolumeClaim", metadata=pvc_meta, spec=pvc_spec
    )

    api_response = k8s_api_instance.create_namespaced_persistent_volume_claim(
        namespace, body_pvc
    )

    # 2. Create a pod which makes use of the PersitantVolumeClaim
    logger.debug(f"create pod: {pod_name}")

    pod_vol = client.V1Volume(
        name=pv_name,
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(pvc_name),
    )
    pod_con = client.V1Container(
        name="nginx",
        image="nginx",
        ports=[client.V1ContainerPort(container_port=80)],
        volume_mounts=[
            client.V1VolumeMount(name=pv_name, mount_path="/usr/share/nginx/html")
        ],
    )
    pod_spec = client.V1PodSpec(volumes=[pod_vol], containers=[pod_con])
    pod_body = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=pod_spec,
    )

    api_response = k8s_api_instance.create_namespaced_pod(
        namespace, pod_body, _preload_content=False
    )
    pod_info = json.loads(api_response.read().decode("utf-8"))
    pod_status = pod_info["status"]["phase"]

    # Check if pod is up and running:
    retries = 0
    while pod_status != "Running" and retries <= 30:

        api_response = k8s_api_instance.read_namespaced_pod(
            pod_name, namespace, _preload_content=False
        )
        pod_info = json.loads(api_response.read().decode("utf-8"))
        pod_status = pod_info["status"]["phase"]
        logger.debug(f"retries:{retries} status:{pod_status}")
        time.sleep(1)
        retries += 1

    # assert pod_status == "Running"
    if pod_status != "Running":
        raise SCSTestException(
            "pod is not Running not able to setup test Enviornment",
            return_code=13,
        )

    # 3. Check if PV got succesfully created using ReadWriteOnce
    logger.debug("check if the created PV supports ReadWriteOnce")

    api_response = k8s_api_instance.list_persistent_volume(_preload_content=False)

    pv_info = json.loads(api_response.read().decode("utf-8"))
    pv_list = pv_info["items"]

    logger.debug("searching for corresponding pv")
    for pv in pv_list:
        logger.debug(f"parsing pv: {pv['metadata']['name']}")
        if pv["spec"]["claimRef"]["name"] == pvc_name:
            logger.debug(f"found pv to pvc: {pvc_name}")

            if pv["status"]["phase"] != "Bound":
                raise SCSTestException(
                    "Not able to bind pv to pvc",
                    return_code=41,
                )

            if "ReadWriteOnce" not in pv["spec"]["accessModes"]:
                raise SCSTestException(
                    "access mode 'ReadWriteOnce' is not supported",
                    return_code=42,
                )

    # 4. Delete resources used for testing
    logger.debug(f"delete pod:{pod_name}")
    api_response = k8s_api_instance.delete_namespaced_pod(pod_name, namespace)
    logger.debug(f"delete pvc:{pvc_name}")
    api_response = k8s_api_instance.delete_namespaced_persistent_volume_claim(
        pvc_name, namespace
    )

    return 0


def main(argv):

    initialize_logging()
    return_code = 0
    return_message = "return_message: FAILED"

    try:
        opts, args = getopt.gnu_getopt(argv, "k:h", ["kubeconfig=", "help"])
    except getopt.GetoptError as exc:
        logger.debug(f"{exc}", file=sys.stderr)
        print_usage()
        return 1

    kubeconfig = None

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-k" or opt[0] == "--kubeconfig":
            kubeconfig = opt[1]
        else:
            print_usage(kubeconfig)
            return 2

    print(return_code, return_message, __file__)

    # Setup kubernetes client
    try:
        logger.debug("setup_k8s_client(kubeconfig)")
        k8s_core_api, k8s_storage_api = setup_k8s_client(kubeconfig)
    except Exception as exception_message:
        logger.info(f"{exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    print(return_code, return_message, __file__)

    # Check if default storage class is defined (MENTETORY)
    try:
        logger.info("check_default_storageclass()")
        default_class_name = check_default_storageclass(k8s_storage_api)
    except SCSTestException as test_exception:
        logger.info(f"{test_exception}")
        return_message = f"{test_exception}"
        return_code = test_exception.return_code
    except Exception as exception_message:
        logger.info(f"{exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    # Check if default_persistent volume has ReadWriteOnce defined (MENTETORY)
    try:
        logger.info("check_default_persistentvolume_readwriteonce()")
        return_code = check_default_persistentvolumeclaim_readwriteonce(
            k8s_core_api, default_class_name
        )
    except SCSTestException as test_exception:
        logger.info(f"{test_exception}")
        return_message = f"{test_exception}"
        return_code = test_exception.return_code
    except Exception as exception_message:
        logger.info(f"{exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    logger.debug(f"return_code:{return_code}")

    if return_code == 0:
        return_message = "all tests passed"

    gen_sonobuoy_result_file(return_code, return_message, __file__)

    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
