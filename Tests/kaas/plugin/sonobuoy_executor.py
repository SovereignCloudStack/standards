from typing import final
from kubernetes import client, config
import os
import logging
from junitparser import JUnitXml

logger = logging.getLogger("sonobuoy_executor")


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


class SonobuoyExecutor:
    """
    An abstract base class for custom Kubernetes cluster provider plugins.
    It represents an interface class from which the api provider-specific
    plugins must be derived as child classes
    """

    kubeconfig_path = None
    working_directory = None

    @final
    def __init__(
        self,
        check_name="sonobuoy_executor",
        kubeconfig=None,
        result_dir_name="sonobuoy_results",
    ):
        self.check_name = check_name
        logger.info(f"Inital SonobuoyExecutor for {self.check_name}")
        logger.debug(f"kubeconfig: {kubeconfig} ")
        if kubeconfig is None:
            raise Exception("No kubeconfig provided")
        else:
            self.kubeconfig_path = kubeconfig
        self.working_directory = os.getcwd()
        self.result_dir_name = result_dir_name
        logger.debug(
            f"Working from {self.working_directory} placing results at {self.result_dir_name}"
        )

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
        return_value = os.system(
            f"sonobuoy version --kubeconfig='{self.kubeconfig_path}'"
        )
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
    def _retrieve_result(self):
        """
        This method invokes sonobouy to store the results in a subdirectory of
        the working directory. The Junit results file contained in it is then
        analyzed in order to interpret the relevant information it containes
        :param: result_file_name:
        :return: None
        """
        logger.debug(f"retrieving results to {self.result_dir_name}")
        result_dir = self.working_directory + "/" + self.result_dir_name
        if os.path.exists(result_dir):
            os.system(f"rm -rf {result_dir}/*")
        else:
            os.mkdir(result_dir)
        os.system(
            f"sonobuoy retrieve {result_dir} -x --filename='{result_dir}' --kubeconfig='{self.kubeconfig_path}'"
        )
        logger.debug(
            f"parsing JUnit result from {result_dir + '/plugins/e2e/results/global/junit_01.xml'} "
        )
        xml = JUnitXml.fromfile(result_dir + "/plugins/e2e/results/global/junit_01.xml")
        failed_test_cases = 0
        passed_test_cases = 0
        skipped_test_cases = 0
        for suite in xml:
            for case in suite:
                if case.is_passed is True:
                    passed_test_cases += 1
                elif case.is_skipped is True:
                    skipped_test_cases += 1
                    # ~ logger.warning(f"SKIPPED:{case.name}")  # TODO:!!! decide if skipped is error or warning only ?
                else:
                    failed_test_cases += 1
                    logger.error(f"ERROR: {case.name}")

        result_message = f" {passed_test_cases} passed, {failed_test_cases} failed, {skipped_test_cases} skipped"
        if failed_test_cases == 0 and skipped_test_cases == 0:
            logger.info(result_message)
            self.return_code = 0
        else:
            logger.error("ERROR:" + result_message)
            self.return_code = 3

    @final
    def run(self):
        """
        This method is to be called to run the plugin
        """
        self.return_code = 11
        try:
            self._preflight_check()
            self._test_k8s_cncf_conformance()
            self._retrieve_result()
        except Exception as e:
            logging.error(e)
            self.return_code = 1
        finally:
            self._cleanup_sonobuoy_resources()
            print(self.check_name + ": " + ("PASS", "FAIL")[min(1, self.return_code)])
            return self.return_code
