from collections import Counter
import json
import logging
import os
import os.path
import shlex
import shutil
import subprocess

import yaml

logger = logging.getLogger(__name__)


def _find_sonobuoy():
    """find sonobuoy in PATH, but also in a fixed location at ~/.local/bin to simplify use with Ansible"""
    result = shutil.which('sonobuoy')
    if result:
        return result
    logger.debug('sonobuoy not in PATH, trying $HOME/.local/bin')
    result = os.path.join(os.path.expanduser('~'), '.local', 'bin', 'sonobuoy')
    if os.path.exists(result):
        return result
    logger.debug('sonobuoy executable not found; expect errors')


def _fmt_result(counter):
    return ', '.join(f"{counter.get(key, 0)} {key}" for key in ('passed', 'failed', 'skipped'))


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
            raise RuntimeError("No kubeconfig provided")
        self.kubeconfig_path = kubeconfig
        self.working_directory = os.getcwd()
        self.result_dir_name = result_dir_name
        self.sonobuoy = _find_sonobuoy()
        logger.debug(f"working from {self.working_directory}")
        logger.debug(f"placing results at {self.result_dir_name}")
        logger.debug(f"sonobuoy executable at {self.sonobuoy}")
        self.args = (arg0 for arg in args for arg0 in shlex.split(str(arg)))

    def _invoke_sonobuoy(self, *args, **kwargs):
        inv_args = (self.sonobuoy, "--kubeconfig", self.kubeconfig_path) + args
        logger.debug(f'invoking {" ".join(inv_args)}')
        # we had capture_output=True, but I don't see why -- let the caller decide
        return subprocess.run(args=inv_args, check=True, **kwargs)

    def _sonobuoy_run(self):
        self._invoke_sonobuoy("run", "--wait", *self.args)

    def _sonobuoy_delete(self):
        self._invoke_sonobuoy("delete", "--wait")

    def _sonobuoy_status_result(self):
        process = self._invoke_sonobuoy("status", "--json", capture_output=True)
        json_data = json.loads(process.stdout)
        counter = Counter()
        for entry in json_data["plugins"]:
            logger.debug(f"plugin {entry['plugin']}: {_fmt_result(entry['result-counts'])}")
            for key, value in entry["result-counts"].items():
                counter[key] += value
        return counter

    def _eval_result(self, counter):
        """evaluate test results and return return code"""
        result_message = f"sonobuoy reports {_fmt_result(counter)}"
        if counter['failed']:
            logger.error(result_message)
            return 3
        logger.info(result_message)
        return 0

    def _preflight_check(self):
        """
        Preflight test to ensure that everything is set up correctly for execution
        """
        if not self.sonobuoy:
            raise RuntimeError("sonobuoy executable not found; is it in PATH?")

    def _sonobuoy_retrieve_result(self, plugin='e2e'):
        """
        Invoke sonobuoy to retrieve results and to store them in a subdirectory of
        the working directory. Analyze the results yaml file for given `plugin` and
        log each failure as ERROR. Return summary dict like `_sonobuoy_status_result`.
        """
        logger.debug(f"retrieving results to {self.result_dir_name}")
        result_dir = os.path.join(self.working_directory, self.result_dir_name)
        os.makedirs(result_dir, exist_ok=True)

        self._invoke_sonobuoy("retrieve", "-x", result_dir)
        yaml_path = os.path.join(result_dir, 'plugins', plugin, 'sonobuoy_results.yaml')
        logger.debug(f"parsing results from {yaml_path}")
        with open(yaml_path, "r") as fileobj:
            result_obj = yaml.load(fileobj.read(), yaml.SafeLoader)
        counter = Counter()
        for item1 in result_obj.get('items', ()):
            # file ...
            for item2 in item1.get('items', ()):
                # suite ...
                for item in item2.get('items', ()):
                    # testcase ... or so
                    status = item.get('status', 'skipped')
                    counter[status] += 1
                    if status == 'failed':
                        logger.error(f"FAILED: {item['name']}")  # <-- this is why this method exists!
        logger.info(f"{plugin} results: {_fmt_result(counter)}")
        return counter

    def run(self):
        """
        This method is to be called to run the plugin
        """
        logger.info(f"running sonobuoy for testcase {self.check_name}")
        self._preflight_check()
        try:
            self._sonobuoy_run()
            return_code = self._eval_result(self._sonobuoy_status_result())
            print(self.check_name + ": " + ("PASS", "FAIL")[min(1, return_code)])
            try:
                self._sonobuoy_retrieve_result()
            except Exception:
                # swallow exception for the time being
                logger.debug('problem retrieving results', exc_info=True)
            return return_code
        except BaseException:
            logger.exception("something went wrong")
            return 112
        finally:
            self._sonobuoy_delete()
