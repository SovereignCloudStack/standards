import base64
from collections import Counter
import logging
import re
import os
import os.path
import shlex
import shutil
import subprocess
import sys
from tempfile import gettempdir

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


def _get_plugins_cm(docs):
    """Locate the sonobuoy-plugins-cm ConfigMap document in the generated sonobuoy manifest."""
    for doc in docs:
        if not doc:
            continue
        if doc.get("kind") != "ConfigMap":
            continue
        if doc.get("metadata", {}).get("name") != "sonobuoy-plugins-cm":
            continue
        return doc
    raise RuntimeError("Failed to locate 'sonobuoy-plugins-cm' ConfigMap in sonobuoy manifest")


def _patch_e2e_plugin_cm(plugins_cm):
    """Patch the 'e2e' plugin definition in sonobuoy-plugins-cm to mount and use admin kubeconfig."""
    data_map = plugins_cm.get("data", {})
    for plugin_key, plugin_raw in data_map.items():
        plugin_data = yaml.safe_load(plugin_raw)
        if not isinstance(plugin_data, dict):
            continue
        if plugin_data.get("sonobuoy-config", {}).get("plugin-name") != "e2e":
            continue

        # Mount the admin-kubeconfig secret into the e2e test pod
        pod_spec = plugin_data.setdefault("podSpec", {})
        pod_spec["volumes"] = pod_spec.get("volumes", []) + [
            {"name": "admin-kubeconfig-vol", "secret": {"secretName": "admin-kubeconfig"}}
        ]
        spec = plugin_data.setdefault("spec", {})
        spec["volumeMounts"] = spec.get("volumeMounts", []) + [
            {"name": "admin-kubeconfig-vol", "mountPath": "/etc/kubernetes/admin.conf", "subPath": "admin.conf"}
        ]

        # Configure e2e test to use the admin kubeconfig:
        # 1. Pass --kubeconfig via E2E_EXTRA_ARGS (later flag wins in Go test runner)
        # 2. Set KUBECONFIG env var for subprocesses and client-go fallback
        envs = spec.setdefault("env", [])
        extra_kubeconfig_arg = "--kubeconfig=/etc/kubernetes/admin.conf"
        for env in envs:
            if env.get("name") == "E2E_EXTRA_ARGS":
                env["value"] = f"{env.get('value', '').strip()} {extra_kubeconfig_arg}".strip()
                break
        else:
            envs.append({"name": "E2E_EXTRA_ARGS", "value": extra_kubeconfig_arg})

        for env in envs:
            if env.get("name") == "KUBECONFIG":
                env["value"] = "/etc/kubernetes/admin.conf"
                break
        else:
            envs.append({"name": "KUBECONFIG", "value": "/etc/kubernetes/admin.conf"})

        data_map[plugin_key] = yaml.dump(plugin_data)
        return

    raise RuntimeError("Failed to locate and patch 'e2e' plugin inside sonobuoy-plugins-cm ConfigMap")


class SonoFixBase:
    """Base strategy for executing Sonobuoy test runs."""

    def __init__(self, handler):
        self.handler = handler

    def run(self):
        raise NotImplementedError


class SonoFixNone(SonoFixBase):
    """Default strategy: run Sonobuoy directly without manifest modifications."""

    def run(self):
        self.handler._invoke_sonobuoy("run", "--wait", *self.handler.args)


class SonoFixInjectKubeconfig(SonoFixBase):
    """Strategy to inject admin kubeconfig into Sonobuoy e2e test pod."""

    def run(self):
        logger.info("Generating Sonobuoy manifest with mounted admin kubeconfig")
        try:
            gen_proc = self.handler._invoke_sonobuoy(
                "gen", *self.handler.args, stdout=subprocess.PIPE, text=True
            )
        except subprocess.CalledProcessError as exc:
            logger.error(f"sonobuoy gen failed: {exc}")
            raise

        docs = [d for d in yaml.safe_load_all(gen_proc.stdout) if d is not None]

        # Extract namespace from manifest and set it on handler so subsequent
        # run, wait, retrieve, and delete calls target this namespace
        namespace_idx = next(
            (idx for idx, d in enumerate(docs) if d.get("kind") == "Namespace"), None
        )
        if namespace_idx is None:
            raise RuntimeError("generated sonobuoy manifest contains no Namespace")
        self.handler.namespace = docs[namespace_idx]["metadata"]["name"]
        logger.debug(f"sonobuoy namespace: {self.handler.namespace}")

        # Insert Secret containing admin kubeconfig into manifest so sonobuoy lifecycle owns it
        with open(self.handler.kubeconfig_path, "rb") as kf:
            kdata = base64.b64encode(kf.read()).decode("ascii")

        secret_doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "admin-kubeconfig",
                "namespace": self.handler.namespace,
                "labels": {
                    "component": "sonobuoy",
                },
            },
            "data": {
                "admin.conf": kdata,
            },
        }
        docs.insert(namespace_idx + 1, secret_doc)

        # Patch e2e plugin in sonobuoy-plugins-cm ConfigMap
        plugins_cm = _get_plugins_cm(docs)
        _patch_e2e_plugin_cm(plugins_cm)

        modified_manifest = yaml.dump_all(docs)

        # Launch Sonobuoy via stdin (-f -)
        self.handler._invoke_sonobuoy("run", "-f", "-", input=modified_manifest, text=True)

        # Waiting is unconditional, but it has to be a separate step: `run -f - --wait`
        # makes sonobuoy re-read the manifest from stdin to determine the namespace,
        # which is already consumed by then. Bare `--wait` means 1440 minutes; without
        # it the flag defaults to 0, which means "do not wait" and exits non-zero.
        self.handler._invoke_sonobuoy("wait", "--wait")


class SonobuoyHandler:
    """
    A class that handles both the execution of sonobuoy and
    the generation of the results for a test report
    """

    kubeconfig_path = None
    working_directory = None

    def __init__(
        self,
        scs_sonobuoy_config_yaml,
        check_name="sonobuoy_handler",
        kubeconfig=None,
        result_dir_name=None,
        args=(),
        sonobuoy_fix="none",
    ):
        self.check_name = check_name
        logger.debug(f"kubeconfig: {kubeconfig} ")
        if kubeconfig is None:
            raise RuntimeError("No kubeconfig provided")
        self.kubeconfig_path = kubeconfig
        self.working_directory = os.getcwd()
        if result_dir_name is None:
            result_dir_name = os.path.join(gettempdir(), check_name)
        self.result_dir_name = result_dir_name
        self.sonobuoy = _find_sonobuoy()
        logger.debug(f"working from {self.working_directory}")
        logger.debug(f"placing results at {self.result_dir_name}")
        logger.debug(f"sonobuoy executable at {self.sonobuoy}")
        if not os.path.exists(scs_sonobuoy_config_yaml):
            raise RuntimeError(f"scs_sonobuoy_config_yaml {scs_sonobuoy_config_yaml} does not exist.")
        self.scs_sonobuoy_config_yaml = scs_sonobuoy_config_yaml
        self.args = tuple(arg0 for arg in args for arg0 in shlex.split(str(arg)))
        # Dynamically populated by fix strategies (e.g., SonoFixInjectKubeconfig)
        # to ensure subsequent wait/retrieve/delete calls target the exact namespace.
        self.namespace = None

        if sonobuoy_fix == "inject-kubeconfig":
            self.sonobuoy_fix = SonoFixInjectKubeconfig(self)
        elif sonobuoy_fix in (None, "none", ""):
            self.sonobuoy_fix = SonoFixNone(self)
        else:
            raise ValueError(f"Unknown sonobuoy fix: {sonobuoy_fix}")

    @property
    def sono_args(self):
        cmd = (self.sonobuoy, "--kubeconfig", self.kubeconfig_path)
        if self.namespace:
            cmd += ("-n", self.namespace)
        return cmd

    def _invoke_sonobuoy(self, *args, stdout=sys.stderr, **kwargs):
        inv_args = self.sono_args + args
        logger.debug(f'invoking {" ".join(inv_args)}')
        # we had capture_output=True, but I don't see why -- let the caller decide
        return subprocess.run(args=inv_args, check=True, stdout=stdout, **kwargs)

    def _sonobuoy_run(self):
        self.sonobuoy_fix.run()

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
            self._sonobuoy_delete()  # remove leftovers from previous run, if any
            self._sonobuoy_run()
            counter = self._sonobuoy_retrieve_result()
            return_code = self._eval_result(counter)
            logger.debug(self.check_name + ": " + ("PASS", "FAIL")[min(1, return_code)])
            return return_code
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
