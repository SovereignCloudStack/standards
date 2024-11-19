from kubernetes import client, config
import os
import subprocess
import logging
from junitparser import JUnitXml
import json

logger = logging.getLogger(__name__)


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


class SonobuoyHandler:
    """
    A class that handles both the execution of sonobuoy and
    the generation of the results for a test report
    """

    kubeconfig_path = None
    working_directory = None

    def __init__(
        self,
        check_name="sonobuoy_handler",
        kubeconfig=None,
        result_dir_name="sonobuoy_results",
        args=None,
    ):
        self.check_name = check_name
        logger.info(f"Inital {__name__} for {self.check_name}")
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
        self.args = args

    def _build_command(self, process, args):
        command = (
            [
                "sonobuoy",
                "--kubeconfig",
                self.kubeconfig_path,
            ] + [process] + args
        )
        command_string = ""
        for entry in command:
            command_string += entry + " "
        return command_string

    def _sonobuoy_run(self):
        logger.debug("sonobuoy run")
        check_args = ["--wait"]
        check_args += [str(arg) for arg in self.args]
        subprocess.run(
            self._build_command("run", check_args),
            shell=True,
            capture_output=True,
            check=True,
        )

    def _sonobouy_delete(self):
        logger.info("removing sonobuoy resources from cluster")
        subprocess.run(
            self._build_command("delete", ["--wait"]),
            shell=True,
            capture_output=True,
            check=True,
        )

    def _sonobouy_status_result(self):
        logger.debug("sonobuoy status")
        process = subprocess.run(
            self._build_command("status", ["--json"]),
            shell=True,
            capture_output=True,
            check=True,
        )
        json_data = json.loads(process.stdout)
        for entry in json_data["plugins"]:
            print(f"plugin:{entry['plugin']}:{entry['result-status']}")
        failed_test_cases = 0
        passed_test_cases = 0
        skipped_test_cases = 0
        for result, count in json_data["plugins"][0]["result-counts"].items():
            if result == "passed":
                passed_test_cases = count
            if result == "failed":
                failed_test_cases = count
                logger.error(f"ERROR: failed: {count}")
            if result == "skipped":
                skipped_test_cases = count
                logger.error(f"ERROR: skipped: {count}")
        result_message = f" {passed_test_cases} passed, {failed_test_cases} failed, {skipped_test_cases} skipped"
        if failed_test_cases == 0 and skipped_test_cases == 0:
            logger.info(result_message)
            self.return_code = 0
        else:
            logger.error("ERROR:" + result_message)
            self.return_code = 3

    def _preflight_check(self):
        """
        Prefligth test to ensure that everything is set up correctly for execution
        :param: None
        :return: None
        """
        logger.info("check kubeconfig")
        print("check kubeconfig")
        self.k8s_api_client = setup_k8s_client(self.kubeconfig_path)

        for api in client.ApisApi().get_api_versions().groups:
            versions = []
            for v in api.versions:
                name = ""
                if v.version == api.preferred_version.version and len(api.versions) > 1:
                    name += "*"
                name += v.version
                versions.append(name)
            logger.info(f"[supported api]: {api.name:<40} {','.join(versions)}")

        logger.debug("checks if sonobuoy is availabe")
        return_value = os.system(
            f"sonobuoy version --kubeconfig='{self.kubeconfig_path}'"
        )
        if return_value != 0:
            raise Exception("sonobuoy is not installed")

    def _sonobuoy_retrieve_result(self):
        """
        This method invokes sonobouy to store the results in a subdirectory of
        the working directory. The Junit results file contained in it is then
        analyzed in order to interpret the relevant information it containes
        :param: result_file_name:
        :return: None
        """
        logger.debug(f"retrieving results to {self.result_dir_name}")
        print(f"retrieving results to {self.result_dir_name}")
        result_dir = self.working_directory + "/" + self.result_dir_name
        if os.path.exists(result_dir):
            raise Exception("result directory allready excisting")
        else:
            os.mkdir(result_dir)

        os.system(
            # ~ f"sonobuoy retrieve {result_dir} -x --filename='{result_dir}' --kubeconfig='{self.kubeconfig_path}'"
            f"sonobuoy retrieve {result_dir} --kubeconfig='{self.kubeconfig_path}'"
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
                    print(f"ERROR: {case.name}")

        result_message = f" {passed_test_cases} passed, {failed_test_cases} failed, {skipped_test_cases} skipped"
        if failed_test_cases == 0 and skipped_test_cases == 0:
            logger.info(result_message)
            self.return_code = 0
        else:
            logger.error("ERROR:" + result_message)
            self.return_code = 3

    def run(self):
        """
        This method is to be called to run the plugin
        """
        self.return_code = 11
        self._preflight_check()
        self._sonobuoy_run()
        self._sonobouy_status_result()

        # ERROR: currently disabled do to: "error retrieving results: unexpected EOF"
        #  migth be related to following bug: https://github.com/vmware-tanzu/sonobuoy/issues/1633
        # self._sonobuoy_retrieve_result(self)

        self._sonobouy_delete()
        print(self.check_name + ": " + ("PASS", "FAIL")[min(1, self.return_code)])
        return self.return_code
