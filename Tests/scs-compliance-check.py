#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-compliance-check.py
#
# (c) Eduard Itrich <eduard@itrich.net>
# (c) Kurt Garloff <kurt@garloff.de>
# SPDX-License-Identifier: Apache-2.0

"""Master SCS compliance checker
reads SCS certification requirements from e.g. scs-compatible.yaml
and performs all the checks for the specified level and outputs a
verdict from all tests (which is reflected in the exit code)
The tests require the OpenStack SDK (and in the future probably
also k8s python bindings) to be installed and access to IaaS
(for the iaas layer tests) via configure clouds/secure.yaml
which are passed in OS_CLOUD (or --os-cloud cmdline param).
In the future als access to a cluster with KUBECONFIG pointing
to a working file.
The goal is to work without any special admin privileges.
(If we find things that can't be tested as normal user, we
would split these tests out.)
"""

import os
import os.path
import sys
import shlex
import getopt
# import time
import datetime
import subprocess
import copy
from functools import partial
from itertools import chain
import yaml


# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('name', 'url', 'versions', 'prerequisite'),
    'version': ('version', 'standards', 'stabilized_at', 'obsoleted_at'),
    'standard': ('check_tools', 'url', 'name', 'condition'),
    'checktool': ('executable', 'args', 'condition', 'classification'),
}


def usage(file=sys.stdout):
    """Output usage information"""
    print("""Usage: scs-compliance-check.py [options] compliance-spec.yaml
Options: -v/--verbose: More verbose output
 -q/--quiet: Don't output anything but errors
 -s/--single-scope: Don't perform required checks for prerequisite scopes
 -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
 -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
 -c/--os-cloud CLOUD: Use specified cloud env (instead of OS_CLOUD env var)
 -o/--output REPORT_PATH: Generate yaml report of compliance check under given path
 -C/--critical-only: Only return critical errors in return code

With -C, the return code will be nonzero precisely when the tests couldn't be run to completion.
""".strip(), file=file)


def run_check_tool(executable, args, env=None, cwd=None):
    """Run executable and return `CompletedProcess` instance"""
    if executable.startswith("http://") or executable.startswith("https://"):
        # TODO: When we start supporting this, consider security concerns
        # Running downloaded code is always risky
        # - Certificate pinning for https downloads
        # - Refuse http
        # - Check sha256/512 or gpg signature
        raise NotImplementedError(f"remote check_tool {executable} not yet supported")
    if executable.startswith("file://"):
        executable = executable[7:]
    exe = [os.path.abspath(os.path.join(cwd or ".", executable)), *shlex.split(args)]
    return subprocess.run(
        exe, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='UTF-8', check=False, env=env, cwd=cwd,
    )


def errcode_to_text(err):
    "translate error code to text"
    return f"{err} ERRORS" if err else "PASSED"


class Config:
    def __init__(self):
        self.arg0 = None
        self.verbose = False
        self.quiet = False
        self.os_cloud = os.environ.get("OS_CLOUD")
        self.checkdate = datetime.date.today()
        self.version = None
        self.output = None
        self.classes = ["light", "medium", "heavy"]
        self.critical_only = False

    def apply_argv(self, argv):
        """Parse options. May exit the program."""
        try:
            opts, args = getopt.gnu_getopt(argv, "hvqd:V:sc:o:r:C", (
                "help", "verbose", "quiet", "date=", "version=",
                "os-cloud=", "output=", "resource-usage=", "critical-only"
            ))
        except getopt.GetoptError as exc:
            print(f"Option error: {exc}", file=sys.stderr)
            usage()
            sys.exit(1)
        for opt in opts:
            if opt[0] == "-h" or opt[0] == "--help":
                usage()
                sys.exit(0)
            elif opt[0] == "-v" or opt[0] == "--verbose":
                self.verbose = True
            elif opt[0] == "-q" or opt[0] == "--quiet":
                self.quiet = True
            elif opt[0] == "-d" or opt[0] == "--date":
                self.checkdate = datetime.date.fromisoformat(opt[1])
            elif opt[0] == "-V" or opt[0] == "--version":
                self.version = opt[1]
            elif opt[0] == "-c" or opt[0] == "--os-cloud":
                self.os_cloud = opt[1]
            elif opt[0] == "-o" or opt[0] == "--output":
                self.output = opt[1]
            elif opt[0] == "-r" or opt[0] == "--resource-usage":
                self.classes = [x.strip() for x in opt[1].split(",")]
            elif opt[0] == "-C" or opt[0] == "--critical-only":
                self.critical_only = True
            else:
                print(f"Error: Unknown argument {opt[0]}", file=sys.stderr)
        if len(args) < 1:
            usage(file=sys.stderr)
            sys.exit(1)
        self.arg0 = args[0]


def condition_optional(cond, default=False):
    """
    check whether condition is in dict cond
       - If set to mandatory, return False
       - If set to optional, return True
       - If set to something else, error out
       - If unset, return default
    """
    value = cond.get("condition")
    value = {None: default, "optional": True, "mandatory": False}.get(value)
    if value is None:
        print(f"ERROR in spec parsing condition: {cond['condition']}", file=sys.stderr)
        value = default
    return value


def check_keywords(ctx, d):
    valid = KEYWORDS[ctx]
    invalid = [k for k in d if k not in valid]
    if invalid:
        print(f"ERROR in spec: {ctx} uses unknown keywords: {','.join(invalid)}", file=sys.stderr)
    return len(invalid)


def suppress(*args, **kwargs):
    return


def invoke_check_tool(check, check_env, check_cwd):
    """run check tool and return invokation dict to use in the report"""
    try:
        compl = run_check_tool(check["executable"], check.get("args", ''), env=check_env, cwd=check_cwd)
    except Exception as e:
        invokation = {
            "rc": 127,
            "stdout": [],
            "stderr": [f"CRITICAL: {e!s}"],
        }
    else:
        invokation = {
            "rc": compl.returncode,
            "stdout": compl.stdout.splitlines(),
            "stderr": compl.stderr.splitlines(),
        }
    for signal in ('info', 'warning', 'error', 'critical'):
        invokation[signal] = len([
            line
            for line in chain(invokation["stderr"], invokation["stdout"])
            if line.lower().startswith(signal)
        ])
    return invokation


def main(argv):
    """Entry point for the checker"""
    config = Config()
    config.apply_argv(argv)
    if not config.os_cloud:
        print("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        return 1
    printv = suppress if not config.verbose else partial(print, file=sys.stderr)
    printnq = suppress if config.quiet else partial(print, file=sys.stderr)
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        spec = yaml.load(specfile, Loader=yaml.SafeLoader)
    check_env = {'OS_CLOUD': config.os_cloud, **os.environ}
    check_cwd = os.path.dirname(config.arg0) or os.getcwd()
    allaborts = 0
    allerrors = 0
    report = {
        "spec": copy.deepcopy(spec),
        "run": {
            "argv": argv,
            "os_cloud": config.os_cloud,
            # TODO: Add kubeconfig context as well
            "checked_at": config.checkdate,
            "classes": config.classes,
            "forced_version": config.version or None,
            "aborts": 0,
            "errors": 0,
            "versions": {},
            "invocations": {},
        },
    }
    check_keywords('spec', spec)
    if config.version:
        spec["versions"] = [vd for vd in spec["versions"] if vd["version"] == config.version]
    if "prerequisite" in spec:
        print("WARNING: prerequisite not yet implemented!", file=sys.stderr)
    vrs = report["run"]["versions"]
    memo = report["run"]["invocations"]  # memoize check tool results
    matches = 0
    for vd in spec["versions"]:
        check_keywords('version', vd)
        stb_date = vd.get("stabilized_at")
        obs_date = vd.get("obsoleted_at")
        futuristic = not stb_date or config.checkdate < stb_date
        outdated = obs_date and obs_date < config.checkdate
        vr = vrs[vd["version"]] = {
            "status": outdated and "outdated" or futuristic and "preview" or "valid",
            "passed": False,
            "aborts": 0,
            "errors": 0,
            "invocations": [],
        }
        if outdated and not config.version:
            continue
        matches += 1
        if config.version and outdated:
            print(f"WARNING: Forced version {config.version} outdated", file=sys.stderr)
        if config.version and futuristic:
            print(f"INFO: Forced version {config.version} not (yet) stable", file=sys.stderr)
        printnq(f"Testing {spec['name']} version {vd['version']}")
        if "standards" not in vd:
            print(f"WARNING: No standards defined yet for {spec['name']} version {vd['version']}",
                  file=sys.stderr)
        errors = 0
        aborts = 0
        invocations = vr["invocations"]
        for standard in vd.get("standards", ()):
            check_keywords('standard', standard)
            optional = condition_optional(standard)
            printnq("*******************************************************")
            printnq(f"Testing {'optional ' * optional}standard {standard['name']} ...")
            printnq(f"Reference: {standard['url']} ...")
            if "check_tools" not in standard:
                printnq(f"WARNING: No check tool specified for {standard['name']}", file=sys.stderr)
            for check in standard.get("check_tools", ()):
                check_keywords('checktool', check)
                if check.get("classification", "light") not in config.classes:
                    print(f"skipping check tool '{check['executable']}' because of resource classification")
                    continue
                args = check.get('args', '')
                memo_key = f"{check['executable']} {args}".strip()
                invokation = memo.get(memo_key)
                if invokation is None:
                    invokation = invoke_check_tool(check, check_env, check_cwd)
                    printv("\n".join(invokation["stdout"]))
                    printnq("\n".join(invokation["stderr"]))
                    memo[memo_key] = invokation
                invocations.append(memo_key)
                abort = invokation["critical"]
                error = invokation["error"]
                printnq(f"... returned {error} errors, {abort} aborts")
                if not condition_optional(check, optional):
                    aborts += abort
                    errors += error
        vr["aborts"] = aborts
        vr["errors"] = errors
        vr["passed"] = not (aborts + errors)
        printnq("*******************************************************")
        printnq(f"Verdict for os_cloud {config.os_cloud}, {spec['name']}, "
                f"version {vd['version']}: {errcode_to_text(aborts + errors)}")
        allaborts += aborts
        allerrors += errors
    report["run"]["aborts"] = allaborts
    report["run"]["errors"] = allerrors
    if not matches:
        print(f"CRITICAL: No valid scope found for {config.checkdate}", file=sys.stderr)
        allaborts += 1  # note: this is after we put the number into the report, so only for return code
    if config.output:
        with open(config.output, 'w', encoding='UTF-8') as file:
            yaml.safe_dump(report, file, default_flow_style=False, sort_keys=False)
    return min(127, allaborts + (0 if config.critical_only else allerrors))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
