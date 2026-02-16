from collections import Counter
import logging
import re
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
    return ', '.join(f"{counter.get(key, 0)} {key}" for key in ('passed', 'failed', 'failed_ok', 'skipped'))


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
        scs_sonobuoy_config_yaml="kaas/sonobuoy-config.yaml",
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
        if not os.path.exists(scs_sonobuoy_config_yaml):
            raise RuntimeError(f"scs_sonobuoy_config_yaml {scs_sonobuoy_config_yaml} does not exist.")
        self.scs_sonobuoy_config_yaml = scs_sonobuoy_config_yaml
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
        log each failure as ERROR. Return summary dict.
        """
        logger.debug(f"retrieving results to {self.result_dir_name}")
        result_dir = os.path.join(self.working_directory, self.result_dir_name)
        os.makedirs(result_dir, exist_ok=True)

        self._invoke_sonobuoy("retrieve", "-x", result_dir)
        yaml_path = os.path.join(result_dir, 'plugins', plugin, 'sonobuoy_results.yaml')
        logger.debug(f"parsing results from {yaml_path}")
        ok_to_fail_regex_list = _load_ok_to_fail_regex_list(self.scs_sonobuoy_config_yaml)

        return sonobuoy_parse_result(plugin, yaml_path, ok_to_fail_regex_list)

    def run(self):
        """
        This method is to be called to run the plugin
        """
        logger.info(f"running sonobuoy for testcase {self.check_name}")
        self._preflight_check()
        try:
            self._sonobuoy_run()
            counter = self._sonobuoy_retrieve_result()
            return_code = self._eval_result(counter)
            print(self.check_name + ": " + ("PASS", "FAIL")[min(1, return_code)])
            return return_code
        except BaseException:
            logger.exception("something went wrong")
            return 112
        finally:
            self._sonobuoy_delete()


def sonobuoy_parse_result(plugin, sonobuoy_results_yaml_path, ok_to_fail_regex_list):
    with open(sonobuoy_results_yaml_path, "r") as fileobj:
        result_obj = yaml.load(fileobj.read(), yaml.SafeLoader)

    counter = Counter()
    for item1 in result_obj.get("items", ()):
        # file ...
        for item2 in item1.get("items", ()):
            # suite ...
            for item in item2.get("items", ()):
                # testcase ... or so
                status = item.get("status", "skipped")
                if status == "failed":
                    if ok_to_fail(ok_to_fail_regex_list, item["name"]):
                        status = "failed_ok"
                    else:
                        logger.error(f"FAILED: {item['name']}")
                counter[status] += 1

    logger.info(f"{plugin} results: {_fmt_result(counter)}")
    return counter


def _load_ok_to_fail_regex_list(scs_sonobuoy_config_yaml):
    with open(scs_sonobuoy_config_yaml, "r") as fileobj:
        config_obj = yaml.load(fileobj.read(), yaml.SafeLoader) or {}
    if not isinstance(config_obj, dict):
        raise ValueError(f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: top-level YAML object must be a mapping")
    allowed_top_level_keys = {"okToFail"}
    unknown_top_level_keys = set(config_obj) - allowed_top_level_keys
    if unknown_top_level_keys:
        raise ValueError(
            f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: unknown top-level keys: {sorted(unknown_top_level_keys)}"
        )
    ok_to_fail_items = config_obj.get("okToFail", ())
    if not isinstance(ok_to_fail_items, list):
        raise ValueError(f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: okToFail must be a list")

    ok_to_fail_regex_list = []
    for idx, entry in enumerate(ok_to_fail_items):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: okToFail[{idx}] must be a mapping"
            )
        allowed_entry_keys = {"regex", "reason"}
        unknown_entry_keys = set(entry) - allowed_entry_keys
        if unknown_entry_keys:
            raise ValueError(
                f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: okToFail[{idx}] has unknown keys: {sorted(unknown_entry_keys)}"
            )
        regex = entry.get("regex")
        if not isinstance(regex, str) or not regex.strip():
            raise ValueError(
                f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: okToFail[{idx}].regex must be a non-empty string"
            )
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"Invalid sonobuoy config format in {scs_sonobuoy_config_yaml}: okToFail[{idx}].reason must be a non-empty string"
            )
        ok_to_fail_regex_list.append((re.compile(regex), reason))
    return ok_to_fail_regex_list


def ok_to_fail(ok_to_fail_regex_list, test_name):
    name = test_name
    for regex, _ in ok_to_fail_regex_list:
        if re.search(regex, name):
            return True
    return False


def check_sonobuoy_result(scs_sonobuoy_config_yaml, result_yaml):
    ok_to_fail_regex_list = _load_ok_to_fail_regex_list(scs_sonobuoy_config_yaml)
    counter = sonobuoy_parse_result("", result_yaml, ok_to_fail_regex_list)
    for key, value in counter.items():
        print(f"{key}: {value}")
