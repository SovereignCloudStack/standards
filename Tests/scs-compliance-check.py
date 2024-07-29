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
from collections import Counter, defaultdict
from functools import partial
from itertools import chain
import yaml


# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables', 'modules', 'timeline'),
    'version': ('version', 'include', 'targets', 'stabilized_at'),
    'module': ('id', 'run', 'testcases', 'url', 'name', 'parameters'),
    'run': ('executable', 'env', 'args', 'section'),
    'testcase': ('lifetime', 'id', 'description'),
    'include': ('id', 'parameters'),
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


def parse_selector(selector_str: str) -> list[list[str]]:
    # a selector is a list of terms,
    # a term is a list of atoms,
    # an atom is a string that optionally starts with "!"
    return [term_str.strip().split('/') for term_str in selector_str.split()]


def test_atom(atom: str, tags: list[str]):
    if atom.startswith("!"):
        return atom[1:] not in tags
    return atom in tags


def test_selector(selector: list[list[str]], tags: list[str]):
    return all(any(test_atom(atom, tags) for atom in term) for term in selector)


def test_selectors(selectors: list[list[list[str]]], tags: list[str]):
    return any(test_selector(selector, tags) for selector in selectors)


NIL_RESULT = {'result': 0}
VERDICTS = {'PASS': 1, 'FAIL': -1}


def compute_results(stdout):
    """pick out test results from stdout lines"""
    result = {}
    for line in stdout:
        parts = line.rsplit(':', 1)
        if len(parts) != 2:
            continue
        value = VERDICTS.get(parts[1].strip().upper())
        if value is None:
            continue
        result[parts[0].strip()] = value
    return result


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
    check_keywords('spec', spec)
    missing_vars = [v for v in spec.get("variables", ()) if v not in config.assignment]
    if missing_vars:
        print(f"Missing variable assignments (via -a) for: {', '.join(missing_vars)}")
        return 1
    module_lookup = {module["id"]: module for module in spec["modules"]}
    version_lookup = {version["version"]: version for version in spec["versions"]}
    if config.version is None:
        versions = max(
            (entry for entry in spec["timeline"] if entry["date"] <= config.checkdate),
            key=lambda entry: entry["date"],
        )["versions"]
    else:
        versions = {config.version: "effective"}
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
    if "prerequisite" in spec:
        print("WARNING: prerequisite not yet implemented!", file=sys.stderr)
    vrs = report["versions"]
    memo = report["run"]["invocations"]  # memoize check tool results
    for vname, validity in versions.items():
        vd = version_lookup[vname]
        check_keywords('version', vd)
        # each include can be given as a mere string (its id) or as an object with id and parameters
        includes = [{"id": inc} if isinstance(inc, str) else inc for inc in vd["include"]]
        testcases = [
            testcase
            for inc in includes
            for testcase in module_lookup[inc["id"]].get("testcases", ())
        ]
        # sanity check: ids must be unique within one version
        ids = Counter(testcase["id"] for testcase in testcases)
        duplicates = [key for key, value in ids.items() if value > 1]
        if duplicates:
            print(f"duplicate ids in version {vname}: {', '.join(duplicates)}", file=sys.stderr)
        vr = vrs[vname] = {}
        printnq(f"Testing {spec['name']} version {vname} ({validity})")
        errors = 0
        aborts = 0
        for include in includes:
            include.setdefault("parameters", {})  # default value to reduce number of possible cases
            module = module_lookup[include['id']]
            check_keywords('module', module)
            if config.tests is not None:
                matches = [ch for ch in module.get('testcases', ()) if config.tests.match(ch['id'])]
                if not matches:
                    continue
            checks = module.get('run', ())
            if not checks and config.tests is None:
                printnq(f"WARNING: No check tool specified for {module['id']}", file=sys.stderr)
            for check in checks:
                check_keywords('run', check)
                section = check.get('section')
                if config.sections and section not in config.sections:
                    print("skipping run: not in selected sections")
                    continue
                assignment = config.assignment
                missing = set(include['parameters']) - set(module.get('parameters', ()))
                if missing:
                    print(f"skipping run: missing parameters {', '.join(missing)}")
                    continue
                if "parameters" in include:
                    assignment = {**assignment, **include['parameters']}
                args = check.get('args', '').format(**assignment)
                env = {key: value.format(**assignment) for key, value in check.get('env', {}).items()}
                env_str = " ".join(f"{key}={value}" for key, value in env.items())
                memo_key = f"{env_str} {check['executable']} {args}".strip()
                printnq(f"invoking {memo_key}...")
                invokation = memo.get(memo_key)
                if invokation is None:
                    check_env = {**os.environ, **env}
                    invokation = invoke_check_tool(check["executable"], args, check_env, check_cwd)
                    invokation["results"] = compute_results(invokation['stdout'])
                    if not config.output:
                        printv("\n".join(invokation["stdout"]))
                        printnq("\n".join(invokation["stderr"]))
                    memo[memo_key] = invokation
                if invokation["results"]:
                    printnq("... returned results:")
                for id_, value in invokation["results"].items():
                    if id_ not in ids:
                        print(f"invalid id in module {include['id']}: {id_}")
                    if id_ in vr:
                        print(f"id already seen in module {include['id']}: {id_}")
                    vr[id_] = {'result': value, 'invocation': memo_key}
                    printnq(f"{config.subject} {vname} {id_} [{include['id']}] = {value}")
                abort = invokation["critical"]
                error = invokation["error"]
                printnq(f"... returned {error} errors, {abort} aborts")
                aborts += abort
                errors += error
        # NOTE: the following verdict may be tentative, depending on whether
        # all tests have been run (which in turn depends on chosen sections);
        # the logic to compute the ultimate verdict should be place further downstream,
        # namely where the reports are gathered and evaluated
        printnq("*******************************************************")
        print(f"{config.subject} {spec['name']} {vname}:")
        for tname, target_spec in vd['targets'].items():
            match_fn = partial(test_selectors, [
                parse_selector(sel_str)
                for sel_str in target_spec.split(',')
            ])
            selected = [testcase for testcase in testcases if match_fn(testcase['tags'])]
            by_result = defaultdict(list)
            for testcase in selected:
                id_ = testcase['id']
                result = vr.get(id_, NIL_RESULT)['result']
                by_result[result].append(testcase)
            print(f"- {tname}: {'FAIL' if by_result[-1] else 'PASS'}")
            for result, category in ((-1, 'FAILED'), (0, 'MISSING')):
                for testcase in by_result[result]:
                    print(f"  - {category} {testcase['id']}")
                    if 'description' in testcase:
                        printnq('    ' + testcase['description'])
            if by_result[0]:
                print("  Verdict TENTATIVE due to missing test cases!")
        allaborts += aborts
        allerrors += errors
    if not versions:
        print(f"CRITICAL: No valid version found for {config.checkdate}", file=sys.stderr)
        critical += 1
    allaborts += critical  # note: this is after we put the number into the report, so only for return code
    if config.output:
        with open(config.output, 'w', encoding='UTF-8') as file:
            yaml.safe_dump(report, file, default_flow_style=False, sort_keys=False)
    return min(127, allaborts + (0 if config.critical_only else allerrors))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
