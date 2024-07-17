#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-compliance-check.py
#
# (c) Eduard Itrich <eduard@itrich.net>
# (c) Kurt Garloff <kurt@garloff.de>
# (c) Matthias Büchse <matthias.buechse@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0

"""Main SCS compliance checker
reads SCS certification requirements from e.g. scs-compatible.yaml
and performs all the checks for the specified level and outputs a
verdict from all tests (which is reflected in the exit code).
The goal is to work without any special admin privileges.
(If we find things that can't be tested as normal user, we
would split these tests out.)
"""

import os
import os.path
import uuid
import re
import sys
import shlex
import getopt
import datetime
import subprocess
from functools import partial
from itertools import chain
import yaml


# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables'),
    'version': ('version', 'standards', 'stabilized_at', 'deprecated_at'),
    'standard': ('checks', 'url', 'name', 'condition', 'parameters'),
    'check': ('executable', 'env', 'args', 'condition', 'lifetime', 'id', 'section'),
}


def usage(file=sys.stdout):
    """Output usage information"""
    print("""Usage: scs-compliance-check.py [options] compliance-spec.yaml
Options: -v/--verbose: More verbose output
 -q/--quiet: Don't output anything but errors
 -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
 -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
 -s/--subject SUBJECT: Name of the subject (cloud) under test, for the report
 -S/--sections SECTION_LIST: comma-separated list of sections to test (default: all sections)
 -t/--tests REGEX: regular expression to select individual tests
 -o/--output REPORT_PATH: Generate yaml report of compliance check under given path
 -C/--critical-only: Only return critical errors in return code
 -a/--assign KEY=VALUE: assign variable to be used for the run (as required by yaml file)

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
        self.subject = ""
        self.assignment = {}
        self.checkdate = datetime.date.today()
        self.version = None
        self.output = None
        self.sections = None
        self.critical_only = False
        self.tests = None

    def apply_argv(self, argv):
        """Parse options. May exit the program."""
        try:
            opts, args = getopt.gnu_getopt(argv, "hvqd:V:s:o:S:Ca:t:", (
                "help", "verbose", "quiet", "date=", "version=",
                "subject=", "output=", "sections=", "critical-only", "assign", "tests",
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
            elif opt[0] == "-s" or opt[0] == "--subject":
                self.subject = opt[1]
            elif opt[0] == "-o" or opt[0] == "--output":
                self.output = opt[1]
            elif opt[0] == "-S" or opt[0] == "--sections":
                self.sections = [x.strip() for x in opt[1].split(",")]
            elif opt[0] == "-C" or opt[0] == "--critical-only":
                self.critical_only = True
            elif opt[0] == "-a" or opt[0] == "--assign":
                key, value = opt[1].split("=", 1)
                if key in self.assignment:
                    raise ValueError(f"Double assignment for {key!r}")
                self.assignment[key] = value
            elif opt[0] == "-t" or opt[0] == "--tests":
                self.tests = re.compile(opt[1])
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


def invoke_check_tool(exe, args, env, cwd):
    """run check tool and return invokation dict to use in the report"""
    try:
        compl = run_check_tool(exe, args, env, cwd)
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


def compute_result(num_abort, num_error):
    """compute check result given number of abort messages and number of error messages"""
    if num_error:
        return -1  # equivalent to FAIL
    if num_abort:
        return 0  # equivalent to DNF
    return 1  # equivalent to PASS


def main(argv):
    """Entry point for the checker"""
    config = Config()
    try:
        config.apply_argv(argv)
    except Exception as exc:
        print(f"CRITICAL: {exc}", file=sys.stderr)
        return 1
    if not config.subject:
        print("You need pass --subject=SUBJECT.", file=sys.stderr)
        return 1
    printv = suppress if not config.verbose else partial(print, file=sys.stderr)
    printnq = suppress if config.quiet else partial(print, file=sys.stderr)
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        spec = yaml.load(specfile, Loader=yaml.SafeLoader)
    missing_vars = [v for v in spec.get("variables", ()) if v not in config.assignment]
    if missing_vars:
        print(f"Missing variable assignments (via -a) for: {', '.join(missing_vars)}")
        return 1
    check_cwd = os.path.dirname(config.arg0) or os.getcwd()
    allaborts = 0
    allerrors = 0
    critical = 0
    report = {
        # these fields are essential:
        "spec": {
            "uuid": spec['uuid'],
            "name": spec['name'],
            "url": spec['url'],
        },
        "checked_at": datetime.datetime.now(),
        "reference_date": config.checkdate,
        "subject": config.subject,
        "versions": {},
        # this field is mostly for debugging:
        "run": {
            "uuid": str(uuid.uuid4()),
            "argv": argv,
            "assignment": config.assignment,
            "sections": config.sections,
            "forced_version": config.version or None,
            "forced_tests": None if config.tests is None else config.tests.pattern,
            "invocations": {},
        },
    }
    check_keywords('spec', spec)
    if config.version:
        spec["versions"] = [vd for vd in spec["versions"] if vd["version"] == config.version]
    if "prerequisite" in spec:
        print("WARNING: prerequisite not yet implemented!", file=sys.stderr)
    vrs = report["versions"]
    memo = report["run"]["invocations"]  # memoize check tool results
    matches = 0
    for vd in spec["versions"]:
        check_keywords('version', vd)
        stb_date = vd.get("stabilized_at")
        dep_date = vd.get("deprecated_at")
        futuristic = not stb_date or config.checkdate < stb_date
        outdated = dep_date and dep_date < config.checkdate
        if outdated and not config.version:
            continue
        vr = vrs[vd["version"]] = {}
        matches += 1
        if config.version and outdated:
            print(f"WARNING: Forced version {config.version} outdated", file=sys.stderr)
        if config.version and futuristic:
            print(f"INFO: Forced version {config.version} not (yet) stable", file=sys.stderr)
        printnq(f"Testing {spec['name']} version {vd['version']}")
        if "standards" not in vd:
            print(f"WARNING: No standards defined yet for {spec['name']} version {vd['version']}",
                  file=sys.stderr)
        seen_ids = set()
        errors = 0
        aborts = 0
        for standard in vd.get("standards", ()):
            check_keywords('standard', standard)
            optional = condition_optional(standard)
            if config.tests is None:
                printnq("*******************************************************")
                printnq(f"Testing {'optional ' * optional}standard {standard['name']} ...")
                printnq(f"Reference: {standard['url']} ...")
            checks = standard.get("checks", ())
            if not checks and config.tests is None:
                printnq(f"WARNING: No check tool specified for {standard['name']}", file=sys.stderr)
            for check in checks:
                check_keywords('check', check)
                if 'id' not in check:
                    raise RuntimeError(f"check descriptor missing id field: {check}")
                id_ = check['id']
                if id_ in seen_ids:
                    raise RuntimeError(f"duplicate id: {id_}")
                seen_ids.add(id_)
                if config.tests is not None:
                    if not config.tests.match(id_):
                        # print(f"skipping check '{id_}': doesn't match tests selector")
                        continue
                    printnq("*******************************************************")
                    print(f"running check {id_}")
                if 'executable' not in check:
                    # most probably a manual check
                    print(f"skipping check '{id_}': no executable given")
                    continue
                section = check.get('section', check.get('lifetime', 'day'))
                if config.sections and section not in config.sections:
                    print(f"skipping check '{id_}': not in selected sections")
                    continue
                assignment = config.assignment
                if "parameters" in standard:
                    assignment = {**assignment, **standard['parameters']}
                args = check.get('args', '').format(**assignment)
                env = {key: value.format(**assignment) for key, value in check.get('env', {}).items()}
                env_str = " ".join(f"{key}={value}" for key, value in env.items())
                memo_key = f"{env_str} {check['executable']} {args}".strip()
                invokation = memo.get(memo_key)
                if invokation is None:
                    check_env = {**os.environ, **env}
                    invokation = invoke_check_tool(check["executable"], args, check_env, check_cwd)
                    result = compute_result(invokation["critical"], invokation["error"])
                    if result == 1 and invokation['rc']:
                        print(f"CRITICAL: check {id_} reported neither error nor abort, but had non-zero rc", file=sys.stderr)
                        critical += 1
                        result = 0
                    invokation['result'] = result
                    printv("\n".join(invokation["stdout"]))
                    printnq("\n".join(invokation["stderr"]))
                    memo[memo_key] = invokation
                abort = invokation["critical"]
                error = invokation["error"]
                vr[check['id']] = {'result': invokation['result'], 'invocation': memo_key}
                printnq(f"... returned {error} errors, {abort} aborts")
                if not condition_optional(check, optional):
                    aborts += abort
                    errors += error
        # NOTE: the following verdict may be tentative, depending on whether
        # all tests have been run (which in turn depends on chosen sections);
        # the logic to compute the ultimate verdict should be place further downstream,
        # namely where the reports are gathered and evaluated
        printnq("*******************************************************")
        printnq(f"Verdict for subject {config.subject}, {spec['name']}, "
                f"version {vd['version']}: {errcode_to_text(aborts + errors)}")
        allaborts += aborts
        allerrors += errors
    if not matches:
        print(f"CRITICAL: No valid version found for {config.checkdate}", file=sys.stderr)
        critical += 1
    allaborts += critical  # note: this is after we put the number into the report, so only for return code
    if config.output:
        with open(config.output, 'w', encoding='UTF-8') as file:
            yaml.safe_dump(report, file, default_flow_style=False, sort_keys=False)
    return min(127, allaborts + (0 if config.critical_only else allerrors))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
