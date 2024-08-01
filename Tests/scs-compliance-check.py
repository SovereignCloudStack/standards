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
from itertools import chain
import logging
import yaml


logger = logging.getLogger(__name__)

# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables', 'modules', 'timeline'),
    'versions': ('version', 'include', 'targets', 'stabilized_at'),
    'modules': ('id', 'run', 'testcases', 'url', 'name', 'parameters'),
    'run': ('executable', 'env', 'args', 'section'),
    'testcases': ('lifetime', 'id', 'description', 'tags'),
    'include': ('id', 'parameters'),
}
TESTCASE_VERDICTS = {'PASS': 1, 'FAIL': -1}
NIL_RESULT = {'result': 0}


def usage(file=sys.stdout):
    """Output usage information"""
    print("""Usage: scs-compliance-check.py [options] SPEC_YAML

Arguments:
  SPEC_YAML: yaml file specifying the certificate scope

Options:
  -v/--verbose: More verbose output
  -q/--quiet: Don't output anything but errors
     --debug: enables DEBUG logging channel
  -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
  -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
  -s/--subject SUBJECT: Name of the subject (cloud) under test, for the report
  -S/--sections SECTION_LIST: comma-separated list of sections to test (default: all sections)
  -t/--tests REGEX: regular expression to select individual testcases based on their ids
  -o/--output REPORT_PATH: Generate yaml report of compliance check under given path
  -C/--critical-only: Only return critical errors in return code
  -a/--assign KEY=VALUE: assign variable to be used for the run (as required by yaml file)

With -C, the return code will be nonzero precisely when the tests couldn't be run to completion.
""", file=file)


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
                "subject=", "output=", "sections=", "critical-only", "assign=", "tests=",
            ))
        except getopt.GetoptError:
            usage(file=sys.stderr)
            raise
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
                logger.error(f"Unknown argument {opt[0]}")
        if len(args) != 1:
            usage(file=sys.stderr)
            raise RuntimeError("need precisely one argument")
        self.arg0 = args[0]


def check_keywords(ctx, d, keywords=KEYWORDS):
    """
    Recursively check `d` (usually a `dict`, but maybe a `list` or a `tuple`) for correctness.

    Returns number of errors.

    Here, correctness means that the dict may only use keywords as given via `keywords`.
    """
    valid = keywords.get(ctx)
    if valid is None:
        return 0  # stop recursion
    if isinstance(d, (list, tuple)):
        return sum(check_keywords(ctx, v, keywords=keywords) for v in d)
    if not isinstance(d, dict):
        return 0
    invalid = [k for k in d if k not in valid]
    if invalid:
        logger.error(f"{ctx} uses unknown keywords: {','.join(invalid)}")
    return len(invalid) + sum(check_keywords(k, v, keywords=keywords) for k, v in d.items())


def resolve_spec(spec: dict):
    """rewire `spec` so as to make most lookups via name unnecessary, and to find name errors early"""
    if isinstance(spec['versions'], dict):
        raise RuntimeError('spec dict already in resolved form')
    # there are currently two types of objects that are being referenced by name or id
    # - modules, referenced by id
    # - versions, referenced by name (unfortunately, the field is called "version")
    # step 1. build lookups
    module_lookup = {module['id']: module for module in spec['modules']}
    version_lookup = {version['version']: version for version in spec['versions']}
    # step 2. check for duplicates:
    if len(module_lookup) != len(spec['modules']):
        raise RuntimeError("spec contains duplicate module ids")
    if len(version_lookup) != len(spec['versions']):
        raise RuntimeError("spec contains duplicate version ids")
    # step 3. replace fields 'modules' and 'versions' by respective lookups
    spec['modules'] = module_lookup
    spec['versions'] = version_lookup
    # step 4. resolve references
    # step 4a. resolve references to modules in includes
    # in this step, we also normalize the include form
    for version in spec['versions'].values():
        version['include'] = [
            {'module': module_lookup[inc], 'parameters': {}} if isinstance(inc, str) else
            {'module': module_lookup[inc['id']], 'parameters': inc.get('parameters', {})}
            for inc in version['include']
        ]
    # step 4b. resolve references to versions in timeline
    # on second thought, let's not go there: it's a canonical extension map, and it should remain that way.
    # however, we still have to look for name errors
    for entry in spec['timeline']:
        for vname in entry['versions']:
            # trigger KeyError
            _ = version_lookup[vname]


def annotate_validity(timeline: list, versions: dict, checkdate: datetime.date):
    """annotate `versions` with validity info from `timeline` (note that this depends on `checkdate`)"""
    validity_lookup = max(
        (entry for entry in timeline if entry['date'] <= checkdate),
        key=lambda entry: entry['date'],
        default={},
    ).get('versions', {})
    for vname, version in versions.items():
        version['validity'] = validity_lookup.get(vname, 'deprecated')


def select_valid(versions: list, valid=('effective', 'warn', 'draft')) -> list:
    return [version for version in versions if version['validity'] in valid]


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
        self.num_error = 0
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
            # the following check used to be "> 0", but this is quite verbose...
            if self.verbosity > 1 and invocation["stderr"]:
                print("\n".join(invocation["stderr"]))
            self.memo[memo_key] = invocation
        logger.debug(f".. rc {invocation['rc']}, {invocation['critical']} critical, {invocation['error']} error")
        self.num_abort += invocation["critical"]
        self.num_error += invocation["error"]
        # count failed testcases because they need not be reported redundantly on the error channel
        self.num_error + len([value for value in invocation['results'].values() if value < 0])
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
        self.partial = False

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


def compile_suite(suite: TestSuite, include: list, sections: tuple, tests: re.Pattern):
    if sections:
        suite.name += f" [sections: {', '.join(sections)}]"
        suite.partial = True
    if tests:
        suite.name += f" [tests: '{tests.pattern}']"
        suite.partial = True
    for inc in include:
        module = inc['module']
        # basic sanity
        testcases = module.get('testcases', ())
        checks = module.get('run', ())
        if not testcases or not checks:
            logger.info(f"module {module['id']} missing checks or test cases")
        # always include all testcases (necessary for assessing partial results)
        suite.include_testcases(module)
        # only add checks if they contain desired testcases
        if not tests or any(tests.match(ch['id']) for ch in testcases):
            suite.include_checks(module, inc['parameters'], sections=sections)


def run_suite(suite: TestSuite, runner: CheckRunner, results: ResultBuilder):
    """run all checks of `suite` using `runner`, collecting `results`"""
    suite.check_sanity()
    for check in suite.checks:
        invocation = runner.run(check)
        for id_, value in invocation["results"].items():
            results.record(id_, result=value, invocation=invocation['id'])


def print_report(subject: str, suite: TestSuite, targets: dict, results: dict, verbose=False):
    if verbose:
        print("********" * 10)
    print(f"{subject} {suite.name}:")
    for tname, target_spec in targets.items():
        selectors = [parse_selector(sel_str) for sel_str in target_spec.split(',')]
        by_result = suite.evaluate(results, selectors)
        missing, failed = by_result[0], by_result[-1]
        verdict = 'FAIL' if failed else 'TENTATIVE pass' if missing else 'PASS'
        if failed or missing:
            verdict += f" ({len(failed)} failed, {len(missing)} missing)"
        print(f"- {tname}: {verdict}")
        for offenders, category in ((failed, 'FAILED'), (missing, 'MISSING')):
            if category == 'MISSING' and suite.partial:
                continue  # do not report each missing testcase if a filter was used
            for testcase in offenders:
                print(f"  - {category} {testcase['id']}")
                if verbose and 'description' in testcase:
                    print('    ' + testcase['description'])


def create_report(argv, config, spec, versions, invocations):
    return {
        # these fields are essential:
        "spec": {
            "uuid": spec['uuid'],
            "name": spec['name'],
            "url": spec['url'],
        },
        "checked_at": datetime.datetime.now(),
        "reference_date": config.checkdate,
        "subject": config.subject,
        "versions": versions,
        # this field is mostly for debugging:
        "run": {
            "uuid": str(uuid.uuid4()),
            "argv": argv,
            "assignment": config.assignment,
            "sections": config.sections,
            "forced_version": config.version or None,
            "forced_tests": None if config.tests is None else config.tests.pattern,
            "invocations": invocations,
        },
    }


def main(argv):
    """Entry point for the checker"""
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    config = Config()
    config.apply_argv(argv)
    if not config.subject:
        raise RuntimeError("You need pass --subject=SUBJECT.")
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        spec = yaml.load(specfile, Loader=yaml.SafeLoader)
    if check_keywords('spec', spec):
        # super simple syntax check (recursive)
        raise RuntimeError('syntax problems in spec file. bailing')
    resolve_spec(spec)
    missing_vars = [v for v in spec.get("variables", ()) if v not in config.assignment]
    if missing_vars:
        raise RuntimeError(f"Missing variable assignments (via -a) for: {', '.join(missing_vars)}")
    if "prerequisite" in spec:
        logger.warning("prerequisite not yet implemented!")
    annotate_validity(spec['timeline'], spec['versions'], config.checkdate)
    if config.version is None:
        versions = select_valid(spec['versions'].values())
    else:
        versions = [spec['versions'].get(config.version)]
        if versions[0] is None:
            raise RuntimeError(f"Requested version '{config.version}' not found")
    if not versions:
        raise RuntimeError(f"No valid version found for {config.checkdate}")
    check_cwd = os.path.dirname(config.arg0) or os.getcwd()
    runner = CheckRunner(check_cwd, config.assignment, verbosity=config.verbose and 2 or not config.quiet)
    version_report = {}
    for version in versions:
        vname = version['version']
        suite = TestSuite(f"{spec['name']} {vname} ({version['validity']})")
        compile_suite(suite, version['include'], config.sections, config.tests)
        builder = ResultBuilder(suite.name)
        run_suite(suite, runner, builder)
        results = version_report[vname] = builder.finalize(permissible_ids=suite.ids)
        if not config.quiet:
            print_report(config.subject, suite, version['targets'], results, verbose=config.verbose)
    if config.output:
        report = create_report(argv, config, spec, version_report, runner.get_invocations())
        with open(config.output, 'w', encoding='UTF-8') as fileobj:
            yaml.safe_dump(report, fileobj, default_flow_style=False, sort_keys=False)
    return min(127, runner.num_abort + (0 if config.critical_only else runner.num_error))


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        logger.critical(f"{str(exc) or repr(exc)}")
        sys.exit(1)
