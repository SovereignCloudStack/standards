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
import os

from kubernetes import client
from kubernetes.client.rest import ApiException
from helper import gen_sonobuoy_result_file
from helper import SCSTestException
from helper import initialize_logging
from helper import print_usage
from helper import setup_k8s_client

import logging.config

logger = logging.getLogger("k8s-default-storage-class-check")

NUM_RETRIES = 30
NAMESPACE = "default"
PVC_NAME = "test-pvc"
PV_NAME = "test-pv"
POD_NAME = "test-pod"

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

def cleanup(k8s_api_instance,namespace, pod_name, pvc_name):
    logger.debug(f"delete pod:{pod_name}")
    api_response = k8s_api_instance.delete_namespaced_pod(pod_name, namespace)
    logger.debug(f"delete pvc:{pvc_name}")
    api_response = k8s_api_instance.delete_namespaced_persistent_volume_claim(
        pvc_name, namespace
    )

def check_default_persistentvolumeclaim_readwriteonce(k8s_api_instance, storage_class):
    """
    1. Create PersistantVolumeClaim
    2. Create pod which uses the PersitantVolumeClaim
    3. Check if PV got succesfully created using ReadWriteOnce
    4. Delete resources used for testing
    """
    # 1. Create PersistantVolumeClaim
    logger.debug(f"create pvc: {PVC_NAME}")

    pvc_meta = client.V1ObjectMeta(name=PVC_NAME)
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
        NAMESPACE, body_pvc
    )

    # 2. Create a pod which makes use of the PersitantVolumeClaim
    logger.debug(f"create pod: {POD_NAME}")

    pod_vol = client.V1Volume(
        name=PV_NAME,
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(PVC_NAME),
    )
    pod_con = client.V1Container(
        name="nginx",
        image="nginx",
        ports=[client.V1ContainerPort(container_port=80)],
        volume_mounts=[
            client.V1VolumeMount(name=PV_NAME, mount_path="/usr/share/nginx/html")
        ],
    )
    pod_spec = client.V1PodSpec(volumes=[pod_vol], containers=[pod_con])
    pod_body = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(name=POD_NAME),
        spec=pod_spec,
    )

    api_response = k8s_api_instance.create_namespaced_pod(
        NAMESPACE, pod_body, _preload_content=False
    )
    pod_info = json.loads(api_response.read().decode("utf-8"))
    pod_status = pod_info["status"]["phase"]

    retries = 0
    while pod_status != "Running" and retries <= NUM_RETRIES:
        api_response = k8s_api_instance.read_namespaced_pod(
            POD_NAME, NAMESPACE, _preload_content=False
        )
        pod_info = json.loads(api_response.read().decode("utf-8"))
        pod_status = pod_info["status"]["phase"]
        logger.debug(f"retries:{retries} status:{pod_status}")
        time.sleep(1)
        retries += 1

    # assert pod_status == "Running"
    if pod_status != "Running":
        cleanup(k8s_api_instance, NAMESPACE, POD_NAME, PVC_NAME)
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
        if pv["spec"]["claimRef"]["name"] == PVC_NAME:
            logger.debug(f"found pv to pvc: {PVC_NAME}")

            if pv["status"]["phase"] != "Bound":
                raise SCSTestException(
                    "Not able to bind pv to pvc",
                    cleanup(k8s_api_instance, NAMESPACE, POD_NAME, PVC_NAME),
                    return_code=41,
                )

            if "ReadWriteOnce" not in pv["spec"]["accessModes"]:
                raise SCSTestException(
                    "access mode 'ReadWriteOnce' is not supported",
                    cleanup(k8s_api_instance, NAMESPACE, POD_NAME, PVC_NAME),
                    return_code=42,
                )

    # 4. Delete resources used for testing
    cleanup(k8s_api_instance, NAMESPACE, POD_NAME, PVC_NAME)

    return 0


def main(argv):
    initialize_logging()
    return_code = 0
    return_message = "return_message: FAILED"

    try:
        opts, args = getopt.gnu_getopt(argv, "k:hd:", ["kubeconfig=", "help","debug"])
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
        if opt[0] == "-d" or opt[0] == "--debug":
            logging.getLogger().setLevel(logging.DEBUG)
    if not kubeconfig:
        logger.critical("You need to have OS_CLOUD set or pass --kubeconfig=CLOUD.")
        return 2


    # Setup kubernetes client
    try:
        logger.debug("setup_k8s_client(kubeconfig)")
        k8s_core_api, k8s_storage_api = setup_k8s_client(kubeconfig)
    except Exception as exception_message:
        logger.info(f"L228 {exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    # Check if default storage class is defined (MANDATORY)
    try:
        logger.info("check_default_storageclass()")
        default_class_name = check_default_storageclass(k8s_storage_api)
    except SCSTestException as test_exception:
        logger.info(f"L237 {test_exception}")
        return_message = f"{test_exception}"
        return_code = test_exception.return_code
    except Exception as exception_message:
        logger.info(f"L241 {exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    # Check if default_persistent volume has ReadWriteOnce defined (MANDATORY)
    try:
        logger.info("check_default_persistentvolume_readwriteonce()")
        return_code = check_default_persistentvolumeclaim_readwriteonce(
            k8s_core_api, default_class_name
        )
    except SCSTestException as test_exception:
        logger.info(f"L252 {test_exception}")
        return_message = f"{test_exception}"
        return_code = test_exception.return_code
    except ApiException as api_exception:
      if api_exception.status == 409:
          print("(409) conflicting resources, try to cleaning up left overs")
          cleanup(k8s_core_api, NAMESPACE, POD_NAME, PVC_NAME)
      else:
          print(f"An API error occurred: {api_exception}")
      return_code = 1
    except Exception as exception_message:
        logger.info(f"{exception_message}")
        return_message = f"{exception_message}"
        return_code = 1

    logger.debug(f"return_code:{return_code}")

    if return_code == 0:
        return_message = "all tests passed"

    gen_sonobuoy_result_file(return_code, return_message, os.path.basename(__file__))

    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
