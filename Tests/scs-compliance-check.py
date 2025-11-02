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
from collections import defaultdict
from itertools import chain
import logging
import yaml

from scs_cert_lib import load_spec, annotate_validity, compile_suite, TestSuite, TESTCASE_VERDICTS


logger = logging.getLogger(__name__)


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
    # use the same interpreter for Python in order to inherit virtual env
    # necessary in cases where the interpreter is used from a virtual env that has not been activated
    # (I think this case should be supported if possible with little effort)
    if exe and exe[0].endswith('.py'):
        # logger.debug(f'using interpreter {sys.executable}')
        exe.insert(0, sys.executable)
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
                if self.verbose:
                    logger.setLevel(logging.DEBUG)
                self.verbose = True
            elif opt[0] == "--debug":
                logger.setLevel(logging.DEBUG)
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


def select_valid(versions: list) -> list:
    return [version for version in versions if version['_explicit_validity']]


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
        self.spamminess = 0

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
                'cmd': memo_key,
                'result': 0,  # keep this for backwards compatibility
                'results': compute_results(invocation['stdout']),
                **invocation
            }
            if self.verbosity > 1 and invocation["stdout"]:
                print("\n".join(invocation["stdout"]))
                self.spamminess += 1
            # the following check used to be "> 0", but this is quite verbose...
            if invocation['rc'] or self.verbosity > 1 and invocation["stderr"]:
                print("\n".join(invocation["stderr"]))
                self.spamminess += 1
            self.memo[memo_key] = invocation
        logger.debug(f".. rc {invocation['rc']}, {invocation['critical']} critical, {invocation['error']} error")
        self.num_abort += invocation["critical"]
        self.num_error += invocation["error"]
        # count failed testcases because they need not be reported redundantly on the error channel
        self.num_error + len([value for value in invocation['results'].values() if value < 0])
        return invocation

    def get_invocations(self):
        return {invocation['id']: invocation for invocation in self.memo.values()}


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


def run_suite(suite: TestSuite, runner: CheckRunner):
    """run all checks of `suite` using `runner`, returning results dict via `ResultBuilder`"""
    suite.check_sanity()
    builder = ResultBuilder(suite.name)
    for check in suite.checks:
        invocation = runner.run(check)
        for id_, value in invocation["results"].items():
            builder.record(id_, result=value, invocation=invocation['id'])
    return builder.finalize(permissible_ids=suite.ids)


def print_report(subject: str, suite: TestSuite, targets: dict, results: dict, verbose=False):
    print(f"{subject} {suite.name}:")
    for tname, target_spec in targets.items():
        by_value = suite.select(tname, target_spec).eval_buckets(results)
        missing, failed, aborted, passed = by_value[None], by_value[-1], by_value[0], by_value[1]
        verdict = 'FAIL' if failed or aborted else 'TENTATIVE pass' if missing else 'PASS'
        summary_parts = [f"{len(passed)} passed"]
        if failed:
            summary_parts.append(f"{len(failed)} failed")
        if aborted:
            summary_parts.append(f"{len(aborted)} aborted")
        if missing:
            summary_parts.append(f"{len(missing)} missing")
        verdict += f" ({', '.join(summary_parts)})"
        print(f"- {tname}: {verdict}")
        reportcateg = [(failed, 'FAILED'), (aborted, 'ABORTED'), (missing, 'MISSING')]
        if verbose:
            reportcateg.append((passed, 'PASSED'))
        for offenders, category in reportcateg:
            if category == 'MISSING' and suite.partial:
                continue  # do not report each missing testcase if a filter was used
            if not offenders:
                continue
            print(f"  - {category}:")
            for testcase in offenders:
                print(f"    - {testcase['id']}:")
                if 'description' in testcase:  # used to be `verbose and ...`, but users need the URL!
                    print(f"      > {testcase['description'].strip()}")


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
        spec = load_spec(yaml.load(specfile, Loader=yaml.SafeLoader))
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
    # collect report data as tuples (version, suite, results) before printing them
    report_data = []
    for version in versions:
        vname = version['version']
        suite = compile_suite(
            f"{spec['name']} {vname} ({version['validity']})",
            version['include'],
            config.sections,
            config.tests,
        )
        report_data.append((version, suite, run_suite(suite, runner)))
    # now report: to console if requested, and likewise for yaml output
    if not config.quiet:
        # print a horizontal line if we had any script output
        if runner.spamminess:
            print("********" * 10)  # 80 characters
        for version, suite, results in report_data:
            print_report(config.subject, suite, version['targets'], results, config.verbose)
    if config.output:
        version_report = {version['version']: results for version, _, results in report_data}
        report = create_report(argv, config, spec, version_report, runner.get_invocations())
        with open(config.output, 'w', encoding='UTF-8') as fileobj:
            yaml.safe_dump(report, fileobj, default_flow_style=False, sort_keys=False, explicit_start=True)
    return min(127, runner.num_abort + (0 if config.critical_only else runner.num_error))


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        logger.critical(f"{str(exc) or repr(exc)}")
        raise
