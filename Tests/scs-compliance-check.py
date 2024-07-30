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
import logging
import yaml


logger = logging.getLogger(__name__)

# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables', 'modules', 'timeline'),
    'version': ('version', 'include', 'targets', 'stabilized_at'),
    'module': ('id', 'run', 'testcases', 'url', 'name', 'parameters'),
    'run': ('executable', 'env', 'args', 'section'),
    'testcase': ('lifetime', 'id', 'description'),
    'include': ('id', 'parameters'),
}
TESTCASE_VERDICTS = {'PASS': 1, 'FAIL': -1}
NIL_RESULT = {'result': 0}


def usage(file=sys.stdout):
    """Output usage information"""
    print("""Usage: scs-compliance-check.py [options] compliance-spec.yaml
Options:
 -v/--verbose: More verbose output
 -q/--quiet: Don't output anything but errors
    --debug: enables DEBUG logging channel
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
                "help", "verbose", "quiet", "date=", "version=", "debug",
                "subject=", "output=", "sections=", "critical-only", "assign", "tests",
            ))
        except getopt.GetoptError as exc:
            logger.critical(f"Option error: {exc}", file=sys.stderr)
            usage()
            sys.exit(1)
        for opt in opts:
            if opt[0] == "-h" or opt[0] == "--help":
                usage()
                sys.exit(0)
            elif opt[0] == "-v" or opt[0] == "--verbose":
                self.verbose = True
            elif opt[0] == "--debug":
                logging.getLogger().setLevel(logging.DEBUG)
            elif opt[0] == "-q" or opt[0] == "--quiet":
                self.quiet = True
                logging.getLogger().setLevel(logging.ERROR)
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
                logger.error(f"Unknown argument {opt[0]}", file=sys.stderr)
        if len(args) < 1:
            usage(file=sys.stderr)
            sys.exit(1)
        self.arg0 = args[0]


def check_keywords(ctx, d):
    valid = KEYWORDS[ctx]
    invalid = [k for k in d if k not in valid]
    if invalid:
        logger.error(f"{ctx} uses unknown keywords: {','.join(invalid)}", file=sys.stderr)
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


def compute_results(stdout):
    """pick out test results from stdout lines"""
    result = {}
    for line in stdout:
        parts = line.rsplit(':', 1)
        if len(parts) != 2:
            continue
        value = TESTCASE_VERDICTS.get(parts[1].strip().upper())
        if value is None:
            continue
        result[parts[0].strip()] = value
    return result


class CheckRunner:
    def __init__(self, cwd, assignment, verbosity=0):
        self.cwd = cwd
        self.assignment = assignment
        self.memo = {}
        self.num_abort = 0
        self.verbosity = verbosity

    def run(self, check):
        parameters = check.get('parameters')
        assignment = {**self.assignment, **parameters} if parameters else self.assignment
        args = check.get('args', '').format(**assignment)
        env = {key: value.format(**assignment) for key, value in check.get('env', {}).items()}
        env_str = " ".join(f"{key}={value}" for key, value in env.items())
        memo_key = f"{env_str} {check['executable']} {args}".strip()
        logger.debug(f"running {memo_key!r}...")
        invocation = self.memo.get(memo_key)
        if invocation is None:
            check_env = {**os.environ, **env}
            invocation = invoke_check_tool(check["executable"], args, check_env, self.cwd)
            invocation = {
                'id': str(uuid.uuid4()),
                'results': compute_results(invocation['stdout']),
                **invocation
            }
            if self.verbosity > 1 and invocation["stdout"]:
                print("\n".join(invocation["stdout"]))
            if self.verbosity > 0 and invocation["stderr"]:
                print("\n".join(invocation["stderr"]))
            self.memo[memo_key] = invocation
        logger.debug(f".. rc {invocation['rc']}, {invocation['critical']} critical, {invocation['error']} error")
        self.num_abort += invocation["critical"]
        return invocation

    def get_invocations(self):
        return dict(self.memo)


class ResultBuilder:
    def __init__(self, name):
        self.name = name
        self._raw = defaultdict(list)

    def record(self, id_, **kwargs):
        self._raw[id_].append(kwargs)

    def finalize(self, permissible_ids=None):
        final = {}
        for id_, ls in self._raw.items():
            if permissible_ids is not None and id_ not in permissible_ids:
                logger.warning(f"ignoring invalid result id: {id_}")
                continue
            # just in case: sort by value (worst first)
            ls.sort(key=lambda item: item['result'])
            winner, runnerups = ls[0], ls[1:]
            if runnerups:
                logger.warning(f"multiple result values for {id_}")
                winner = {**winner, 'runnerups': runnerups}
            final[id_] = winner
        return final


class TestSuite:
    def __init__(self, name):
        self.name = name
        self.checks = []
        self.testcases = []
        self.ids = Counter()
        self.results = {}
        self.aborts = 0

    def check_sanity(self):
        # sanity check: ids must be unique
        duplicates = [key for key, value in self.ids.items() if value > 1]
        if duplicates:
            logger.warning(f"duplicate ids in {self.name}: {', '.join(duplicates)}")

    def include_checks(self, module, parameters, sections=None):
        missing_params = set(module.get('parameters', ())) - set(parameters)
        if missing_params:
            logger.warning(f"module {module['id']}: missing parameters {', '.join(missing_params)}")
            return
        self.checks.extend(
            {**check, 'parameters': parameters}
            for check in module.get('run', ())
            if sections is None or check.get('section') in sections
        )

    def include_testcases(self, module):
        testcases = module.get('testcases', ())
        self.testcases.extend(testcases)
        self.ids.update(testcase["id"] for testcase in testcases)

    def evaluate(self, results, selectors):
        by_result = defaultdict(list)
        for testcase in self.testcases:
            if not test_selectors(selectors, testcase['tags']):
                continue
            result = results.get(testcase['id'], NIL_RESULT)['result']
            by_result[result].append(testcase)
        return by_result


def run_suite(suite: TestSuite, runner: CheckRunner, results: ResultBuilder):
    """run all checks of `suite` using `runner`, collecting `results`"""
    suite.check_sanity()
    for check in suite.checks:
        invocation = runner.run(check)
        for id_, value in invocation["results"].items():
            results.record(id_, result=value, invocation=invocation['id'])


def main(argv):
    """Entry point for the checker"""
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    config = Config()
    try:
        config.apply_argv(argv)
    except Exception as exc:
        logger.critical(f"{exc}")
        return 1
    if not config.subject:
        logger.critical("You need pass --subject=SUBJECT.")
        return 1
    printv = suppress if not config.verbose else partial(print, file=sys.stderr)
    printnq = suppress if config.quiet else partial(print, file=sys.stderr)
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        spec = yaml.load(specfile, Loader=yaml.SafeLoader)
    check_keywords('spec', spec)
    missing_vars = [v for v in spec.get("variables", ()) if v not in config.assignment]
    if missing_vars:
        logger.critical(f"Missing variable assignments (via -a) for: {', '.join(missing_vars)}")
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
    runner = CheckRunner(check_cwd, config.assignment, verbosity=config.verbose and 2 or not config.quiet)
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
            "invocations": [],
        },
    }
    if "prerequisite" in spec:
        logger.warning("prerequisite not yet implemented!")
    vrs = report["versions"]
    num_error = 0
    for vname, validity in versions.items():
        suite = TestSuite(f"{spec['name']} {vname} ({validity})")
        if config.sections:
            suite.name += f" [sections: {', '.join(config.sections)}]"
        if config.tests:
            suite.name += f" [tests: '{config.tests.pattern}']"
        # printnq(f"Testing {suite.name}")
        vd = version_lookup[vname]
        check_keywords('version', vd)
        for inc in vd["include"]:
            if isinstance(inc, str):
                inc = {'id': inc}
            module = module_lookup[inc['id']]
            # basic sanity
            testcases = module.get('testcases', ())
            checks = module.get('run', ())
            if not testcases or not checks:
                logger.info(f"module {module['id']} missing checks or test cases")
                continue
            # always include all testcases (necessary for assessing partial results)
            suite.include_testcases(module)
            # only add checks if they contain desired testcases
            if not config.tests or any(config.tests.match(ch['id']) for ch in testcases):
                suite.include_checks(module, inc.get('parameters', {}), sections=config.sections)
        builder = ResultBuilder(suite.name)
        run_suite(suite, runner, builder)
        results = vrs[vname] = builder.finalize(permissible_ids=suite.ids)
        printv("********" * 10)
        printnq(f"{config.subject} {suite.name}:")
        for tname, target_spec in vd['targets'].items():
            selectors = [parse_selector(sel_str) for sel_str in target_spec.split(',')]
            by_result = suite.evaluate(results, selectors)
            missing, failed = by_result[0], by_result[-1]
            verdict = 'FAIL' if failed else 'TENTATIVE pass' if missing else 'PASS'
            if failed or missing:
                verdict += f" ({len(failed)} failed, {len(missing)} missing)"
            printnq(f"- {tname}: {verdict}")
            if tname == 'main':
                num_error += len(failed)
            for offenders, category in ((failed, 'FAILED'), (missing, 'MISSING')):
                if category == 'MISSING' and (config.sections or config.tests):
                    continue  # do not report missing testcases if a filter was used
                for testcase in offenders:
                    printnq(f"  - {category} {testcase['id']}")
                    if 'description' in testcase:
                        printv('    ' + testcase['description'])
    report['run']['invocations'] = runner.get_invocations()
    num_abort = runner.num_abort
    if not versions:
        logger.critical(f"No valid version found for {config.checkdate}", file=sys.stderr)
        num_abort += 1
    if config.output:
        with open(config.output, 'w', encoding='UTF-8') as file:
            yaml.safe_dump(report, file, default_flow_style=False, sort_keys=False)
    return min(127, num_abort + (0 if config.critical_only else num_error))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
