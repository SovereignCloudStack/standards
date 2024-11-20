from collections import Counter
import json
import logging
import os
import shlex
import shutil
import subprocess

from junitparser import JUnitXml

logger = logging.getLogger(__name__)


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
        args=(),
    ):
        self.check_name = check_name
        logger.debug(f"kubeconfig: {kubeconfig} ")
        if kubeconfig is None:
            raise Exception("No kubeconfig provided")
        else:
            self.kubeconfig_path = kubeconfig
        self.working_directory = os.getcwd()
        self.result_dir_name = result_dir_name
        self.sonobuoy = shutil.which('sonobuoy')
        logger.debug(f"working from {self.working_directory}")
        logger.debug(f"placing results at {self.result_dir_name}")
        logger.debug(f"sonobuoy executable at {self.sonobuoy}")
        self.args = (arg0 for arg in args for arg0 in shlex.split(str(arg)))

    def _invoke_sonobuoy(self, *args, **kwargs):
        inv_args = (self.sonobuoy, "--kubeconfig", self.kubeconfig_path) + args
        logger.debug(f'invoking {" ".join(inv_args)}')
        return subprocess.run(args=inv_args, capture_output=True, check=True, **kwargs)

    def _sonobuoy_run(self):
        self._invoke_sonobuoy("run", "--wait", *self.args)

    def _sonobuoy_delete(self):
        self._invoke_sonobuoy("delete", "--wait")

    def _sonobuoy_status_result(self):
        process = self._invoke_sonobuoy("status", "--json")
        json_data = json.loads(process.stdout)
        counter = Counter()
        for entry in json_data["plugins"]:
            logger.debug(f"plugin:{entry['plugin']}:{entry['result-status']}")
            for result, count in entry["result-counts"].items():
                counter[result] += count
        return counter

    def _eval_result(self, counter):
        result_str = ', '.join(f"{counter[key]} {key}" for key in ('passed', 'failed', 'skipped'))
        result_message = f"sonobuoy reports {result_str}"
        if counter['failed']:
            logger.error(result_message)
            self.return_code = 3
        else:
            logger.info(result_message)
            self.return_code = 0

    def _preflight_check(self):
        """
        Preflight test to ensure that everything is set up correctly for execution
        """
        if not self.sonobuoy:
            raise RuntimeError("sonobuoy executable not found; is it in PATH?")

    def _sonobuoy_retrieve_result(self):
        """
        This method invokes sonobuoy to store the results in a subdirectory of
        the working directory. The Junit results file contained in it is then
        analyzed in order to interpret the relevant information it containes
        """
        logger.debug(f"retrieving results to {self.result_dir_name}")
        result_dir = os.path.join(self.working_directory, self.result_dir_name)
        if os.path.exists(result_dir):
            raise Exception("result directory already existing")
        os.mkdir(result_dir)

        # XXX use self._invoke_sonobuoy
        os.system(
            # ~ f"sonobuoy retrieve {result_dir} -x --filename='{result_dir}' --kubeconfig='{self.kubeconfig_path}'"
            f"sonobuoy retrieve {result_dir} --kubeconfig='{self.kubeconfig_path}'"
        )
        logger.debug(
            f"parsing JUnit result from {result_dir + '/plugins/e2e/results/global/junit_01.xml'} "
        )
        xml = JUnitXml.fromfile(result_dir + "/plugins/e2e/results/global/junit_01.xml")
        counter = Counter()
        for suite in xml:
            for case in suite:
                if case.is_passed is True:  # XXX why `is True`???
                    counter['passed'] += 1
                elif case.is_skipped is True:
                    counter['skipped'] += 1
                else:
                    counter['failed'] += 1
                    logger.error(f"{case.name}")
        return counter

    def run(self):
        """
        This method is to be called to run the plugin
        """
        logger.info(f"running sonobuoy for testcase {self.check_name}")
        self.return_code = 11
        self._preflight_check()
        self._sonobuoy_run()
        self._eval_result(self._sonobuoy_status_result())

        # ERROR: currently disabled do to: "error retrieving results: unexpected EOF"
        #  might be related to following bug: https://github.com/vmware-tanzu/sonobuoy/issues/1633
        # self._sonobuoy_retrieve_result(self)

        self._sonobuoy_delete()
        print(self.check_name + ": " + ("PASS", "FAIL")[min(1, self.return_code)])
        return self.return_code
