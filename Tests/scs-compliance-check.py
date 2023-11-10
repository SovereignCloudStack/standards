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
import sys
import shlex
import getopt
# import time
import datetime
import subprocess
import copy
from itertools import chain
import yaml


KEYWORDS_SPEC = ('name', 'url', 'versions', 'prerequisite')
KEYWORDS_VERSION = ('version', 'standards', 'stabilized_at', 'obsoleted_at')
KEYWORDS_STANDARD = ('check_tools', 'url', 'name', 'condition')
KEYWORDS_CHECKTOOL = ('executable', 'args', 'condition', 'classification')


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


MYPATH = "."


def add_search_path(arg0):
    """Store path of scs-compliance-check.py to search path, as check tools
       referenced in compliance.spec might be relative to it.
    """
    global MYPATH
    arg0_pidx = arg0.rfind('/')
    if arg0_pidx == -1:
        # this can happen when you call this script via "python3 scs-compliance-check.py"
        # then the search path is already fine
        return
    MYPATH = arg0[:arg0_pidx]
    # os.environ['PATH'] += ":" + MYPATH


def run_check_tool(executable, args, os_cloud, verbose=False, quiet=False):
    "Run executable and return exit code"
    if executable.startswith("http://") or executable.startswith("https://"):
        print(f"ERROR: remote check_tool {executable} not yet supported", file=sys.stderr)
        # TODO: When we start supporting this, consider security concerns
        # Running downloaded code is always risky
        # - Certificate pinning for https downloads
        # - Refuse http
        # - Check sha256/512 or gpg signature
        return 999999
    if executable.startswith("file://"):
        executable = executable[7:]
    if executable[0] == "/":
        exe = [executable, ]
    else:
        exe = [MYPATH + "/" + executable, ]
    if args:
        exe.extend(shlex.split(args))
    # print(f"{exe}")
    # compl = subprocess.run(exe, capture_output=True, text=True, check=False)
    env = {'OS_CLOUD': os_cloud, **os.environ}
    compl = subprocess.run(
        exe, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='UTF-8', check=False, env=env,
    )
    if verbose:
        print(compl.stdout)
    if not quiet:
        print(compl.stderr, file=sys.stderr)
    return compl


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
        """
        Parse options. May exit the program.
        """
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
    """check whether condition is in dict cond
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


def check_keywords(d, ctx, valid=()):
    invalid = [k for k in d if k not in valid]
    if invalid:
        print(f"ERROR in spec: {ctx} uses unknown keywords: {','.join(invalid)}", file=sys.stderr)


def main(argv):
    """Entry point for the checker"""
    config = Config()
    config.apply_argv(argv)
    if not config.os_cloud:
        print("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
        return 1
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        specdict = yaml.load(specfile, Loader=yaml.SafeLoader)
    allaborts = 0
    allerrors = 0
    report = copy.deepcopy(specdict)
    check_keywords(report, 'spec', KEYWORDS_SPEC)
    run_report = report["run"] = {}
    run_report["os_cloud"] = config.os_cloud
    # TODO: Add kubeconfig context as well
    run_report["checked_at"] = config.checkdate
    run_report["classes"] = config.classes
    if config.version:
        run_report["forced_version"] = config.version
        report["versions"] = [vd for vd in report["versions"] if vd["version"] == config.version]
    if "prerequisite" in specdict:
        print("WARNING: prerequisite not yet implemented!", file=sys.stderr)
    memo = run_report["invokations"] = {}  # memoize check tool results
    matches = 0
    for vd in report["versions"]:
        check_keywords(vd, 'version', KEYWORDS_VERSION)
        stb_date = vd.get("stabilized_at")
        obs_date = vd.get("obsoleted_at")
        futuristic = not stb_date or config.checkdate < stb_date
        outdated = obs_date and obs_date < config.checkdate
        vd.update({
            "status": "n/a",
            "passed": False,
        })
        if outdated:
            vd["status"] = "outdated"
        elif futuristic:
            vd["status"] = "preview"
        else:
            vd["status"] = "valid"
        if outdated and not config.version:
            continue
        matches += 1
        if config.version and outdated:
            print(f"WARNING: Forced version {config.version} outdated", file=sys.stderr)
        if config.version and futuristic:
            print(f"INFO: Forced version {config.version} not (yet) stable", file=sys.stderr)
        if not config.quiet:
            print(f"Testing {specdict['name']} version {vd['version']}")
        if "standards" not in vd:
            print(f"WARNING: No standards defined yet for {specdict['name']} version {vd['version']}",
                  file=sys.stderr)
        errors = 0
        aborts = 0
        for standard in vd["standards"]:
            check_keywords(standard, 'standard', KEYWORDS_STANDARD)
            optional = condition_optional(standard)
            if not config.quiet:
                print("*******************************************************")
                print(f"Testing {'optional ' * optional}standard {standard['name']} ...")
                print(f"Reference: {standard['url']} ...")
            if "check_tools" not in standard:
                print(f"WARNING: No compliance check tool implemented yet for {standard['name']}")
                continue
            for check in standard["check_tools"]:
                check_keywords(check, 'checktool', KEYWORDS_CHECKTOOL)
                if check.get("classification", "light") not in config.classes:
                    print(f"skipping check tool '{check['executable']}' because of resource classification")
                    continue
                args = check.get('args', '')
                memo_key = f"{check['executable']} {args}".strip()
                invokation = memo.get(memo_key)
                if invokation is None:
                    compl = run_check_tool(check["executable"], args, config.os_cloud, config.verbose, config.quiet)
                    invokation = {
                        "rc": compl.returncode,
                        "stdout": compl.stdout.splitlines(),
                        "stderr": compl.stderr.splitlines(),
                    }
                    for signal in ('info', 'warning', 'error', 'critical'):
                        invokation[signal] = len([
                            line
                            for line in chain(compl.stderr.splitlines(), compl.stdout.splitlines())
                            if line.lower().startswith(signal)
                        ])
                    memo[memo_key] = invokation
                abort = invokation["critical"]
                error = invokation["error"]
                if not config.quiet:
                    print(f"... returned {error} errors")
                check["aborts"] = abort
                check["errors"] = error
                if not condition_optional(check, optional):
                    aborts += abort
                    errors += error
        vd["aborts"] = errors
        vd["errors"] = errors
        vd["passed"] = not (aborts + errors)
        if not config.quiet:
            print("*******************************************************")
            print(f"Verdict for os_cloud {config.os_cloud}, {specdict['name']}, "
                  f"version {vd['version']}: {errcode_to_text(aborts + errors)}")
        allaborts += aborts
        allerrors += errors
    if not matches:
        print(f"No valid standard found for {config.checkdate}", file=sys.stderr)
        return 2
    if config.output:
        with open(config.output, 'w', encoding='UTF-8') as file:
            yaml.safe_dump(report, file, default_flow_style=False, sort_keys=False)
    return allaborts + (0 if config.critical_only else allerrors)


if __name__ == "__main__":
    add_search_path(sys.argv[0])
    sys.exit(main(sys.argv[1:]))
