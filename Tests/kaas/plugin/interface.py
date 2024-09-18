from abc import ABC, abstractmethod
from typing import final
from kubernetes import client, config
import os
import logging
from junitparser import JUnitXml

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("interface")


def setup_k8s_client(kubeconfigfile=None):

    if kubeconfigfile:
        logger.debug(f"loading kubeconfig file '{kubeconfigfile}'")
        config.load_kube_config(kubeconfigfile)
        logger.info("kubeconfigfile loaded successfully")
    else:
        logger.error("no kubeconfig file provided")
        return None

    k8s_api_client = client.CoreV1Api()

    return k8s_api_client


class KubernetesClusterPlugin(ABC):
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes
    """

    kubeconfig_path = None
    cluster_name = None
    k8s_api_client = None
    working_directory = None
    plugin_result_directory = "plugins/e2e/results/global"

    @final
    def __init__(self, config=None):
        logger.debug(config)
        self.working_directory = os.getcwd()
        logger.debug(f"Working from {self.working_directory}")

    @final
    def _preflight_check(self):
        """
        Prefligth test to ensure that everything is set up correctly for execution
        :param: None
        :return: None
        """
        logger.info("check kubeconfig")
        self.k8s_api_client = setup_k8s_client(self.kubeconfig_path)

        for api in client.ApisApi().get_api_versions().groups:
            versions = []
            for v in api.versions:
                name = ""
                if v.version == api.preferred_version.version and len(api.versions) > 1:
                    name += "*"
                name += v.version
                versions.append(name)
            logger.debug(f"[supported api]: {api.name:<40} {','.join(versions)}")

        logger.debug("checks if sonobuoy is availabe")
        return_value = os.system(f"sonobuoy version --kubeconfig='{self.kubeconfig_path}'")
        if return_value != 0:
            raise Exception("sonobuoy is not installed")

    @final
    def _test_k8s_cncf_conformance(self):
        """
        This method invokes the conformance tests with sononbuoy
        :param: None
        :return: None
        """
        logger.info(" invoke cncf conformance test")
        # ~ os.system(f"sonobuoy run --wait --mode=certified-conformance --kubeconfig='{self.kubeconfig_path}'")
        # TODO:!!! switch to the real test on the final merge !!!
        # Only one test is currently being carried out for development purposes
        os.system(
            f"sonobuoy run --wait --plugin-env e2e.E2E_FOCUS=pods --plugin-env e2e.E2E_DRYRUN=true --kubeconfig='{self.kubeconfig_path}'"
        )

    @final
    def _test_scs_kaas_conformance(self):
        """
        This method invokes SCS's very own conformance tests by using sononbuoy
        :param: None
        :return: None
        """
        raise NotImplementedError

    @final
    def _cleanup_sonobuoy_resources(self):
        """
        This method deletes all resources that sonobuoy has created in a k8s cluster for a test
        :param: None
        :return: None
        """
        logger.info("removing sonobuoy tests from cluster")
        os.system(f"sonobuoy delete --wait --kubeconfig='{self.kubeconfig_path}'")

    @final
    def _retrieve_result(self, result_file_name):
        """
        This method invokes sonobouy to store the results in a subdirectory of
        the working directory. The Junit results file contained in it is then
        analyzed in order to interpret the relevant information it containes
        :param: result_file_name:
        :return: None
        """
        logger.debug(f"retrieving results to {result_file_name}")
        result_directory = self.working_directory + "/" + result_file_name
        if os.path.exists(result_directory):
            os.system(f"rm -rf {result_directory}/*")
        else:
            os.mkdir(result_directory)
        os.chdir(result_directory)
        os.system(
            f"sonobuoy retrieve -x --filename='{result_file_name}' --kubeconfig='{self.kubeconfig_path}'"
        )

        logger.debug(
            f"parsing JUnit result from {result_directory + '/' +  self.plugin_result_directory + '/junit_01.xml' } "
        )
        xml = JUnitXml.fromfile(
            result_directory + "/" + self.plugin_result_directory + "/junit_01.xml"
        )
        failed_test_cases = 0
        passed_test_cases = 0
        skipped_test_cases = 0
        for suite in xml:
            for case in suite:
                if case.is_passed:
                    passed_test_cases += 1
                else:
                    failed_test_cases += 1
                if case.is_skipped:
                    skipped_test_cases += 1

        logger.info(
            f" {passed_test_cases} passed, {failed_test_cases} failed of which {skipped_test_cases} were skipped"
        )
        os.chdir(self.working_directory)

    @abstractmethod
    def _create_cluster(self, cluster_name) -> (str, int):
        """
        Create a Kubernetes cluster to test aggainst.
        :param: cluster_name:
        :return: kubeconfig: kubeconfig of the cluster used for testing
        """
        pass

    @abstractmethod
    def _delete_cluster(self, cluster_name) -> (str, int):
        """
        Delete the Kubernetes cluster.
        :param: cluster_name:
        :return: None
        """
        pass

    @final
    def run(self):
        """
        This method is to be called to run the plugin
        """

        try:
            self._create_cluster()
            self._preflight_check()
            self._test_k8s_cncf_conformance()
            self._retrieve_result("cncf_result")
            self._cleanup_sonobuoy_resources()
            # self._test_scs_kaas_conformance()
            # self._retrieve_result("scs_kaas_result")
        except Exception as e:
            logging.error(e)

        try:
            self._cleanup_sonobuoy_resources()
        except Exception as e:
            logging.error(e)
        finally:
            self._delete_cluster()
