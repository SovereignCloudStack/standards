#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-compliance-check.py
#
# (c) Eduard Itrich <eduard@itrich.net>
# (c) Kurt Garloff <kurt@garloff.de>
# (c) Matthias Büchse <matthias.buechse@alasca.cloud>
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
from itertools import chain
import logging
import yaml

from scs_cert_lib import load_spec, annotate_validity, eval_buckets, TESTCASE_VERDICTS


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
        self.assignment = { "e2e-parallel" : "--e2e-parallel=true" }
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
                if key in self.assignment and key != "e2e-parallel":
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


def compute_results(stdout, permissible_ids=()):
    """pick out test results from stdout lines"""
    result = {}
    for line in stdout:
        parts = line.rsplit(':', 1)
        if len(parts) != 2:
            continue
        value = TESTCASE_VERDICTS.get(parts[1].strip().upper())
        if value is None:
            continue
        testcase_id = parts[0].strip()
        if permissible_ids and testcase_id not in permissible_ids:
            logger.warning(f"ignoring invalid result id: {testcase_id}")
            continue
        result[testcase_id] = value
    return result


class CheckRunner:
    def __init__(self, cwd, assignment, verbosity=0):
        self.cwd = cwd
        self.assignment = assignment
        self.num_abort = 0
        self.num_error = 0
        self.verbosity = verbosity
        self.spamminess = 0

    def run(self, check, testcases=()):
        parameters = check.get('parameters', {})
        assignment = {'testcases': ' '.join(testcases), **self.assignment, **parameters}
        args = check.get('args', '').format(**assignment)
        env = {key: value.format(**assignment) for key, value in check.get('env', {}).items()}
        env_str = " ".join(f"{key}={value}" for key, value in env.items())
        cmd = f"{env_str} {check['executable']} {args}".strip()
        logger.debug(f"running {cmd!r}...")
        check_env = {**os.environ, **env}
        invocation = invoke_check_tool(check["executable"], args, check_env, self.cwd)
        invocation = {
            'id': str(uuid.uuid4()),
            'cmd': cmd,
            'results': compute_results(invocation['stdout'], permissible_ids=testcases),
            **invocation
        }
        if self.verbosity > 1 and invocation["stdout"]:
            print("\n".join(invocation["stdout"]))
            self.spamminess += 1
        # the following check used to be "> 0", but this is quite verbose...
        if invocation['rc'] or self.verbosity > 1 and invocation["stderr"]:
            print("\n".join(invocation["stderr"]))
            self.spamminess += 1
        logger.debug(f".. rc {invocation['rc']}, {invocation['critical']} critical, {invocation['error']} error")
        self.num_abort += invocation["critical"]
        self.num_error += invocation["error"]
        # count failed testcases because they need not be reported redundantly on the error channel
        self.num_error + len([value for value in invocation['results'].values() if value < 0])
        return invocation


def print_report(testcase_lookup: dict, targets: dict, results: dict, partial=False, verbose=False):
    for tname, tc_ids in targets.items():
        by_value = eval_buckets(results, tc_ids)
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
            if category == 'MISSING' and partial:
                continue  # do not report each missing testcase if a filter was used
            if not offenders:
                continue
            print(f"  - {category}:")
            for tc_id in offenders:
                print(f"    - {tc_id}:")
                testcase = testcase_lookup[tc_id]
                if 'description' in testcase:
                    print(f"      > {testcase['description']}")
                if 'url' in testcase:
                    print(f"      > {testcase['url']}")


def create_report(argv, config, spec, invocations):
    return {
        # these fields are essential:
        # results are no longer specific to version!
        # omit the field `version` because it's just redundant; simply parse invocations (see below)
        "spec": {
            "uuid": spec['uuid'],
            "name": spec['name'],
            "url": spec['url'],
        },
        "checked_at": datetime.datetime.now(),
        "reference_date": config.checkdate,
        "subject": config.subject,
        # this field is mostly for debugging:
        "run": {
            "uuid": str(uuid.uuid4()),
            "argv": argv,
            "assignment": config.assignment,
            "sections": config.sections,
            "forced_version": config.version or None,
            "forced_tests": None if config.tests is None else config.tests.pattern,
            "invocations": {invocation['id']: invocation for invocation in invocations},
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
    title, partial = spec['name'], False
    if config.sections:
        title += f" [sections: {', '.join(config.sections)}]"
        partial = True
    if config.tests:
        title += f" [tests: '{config.tests.pattern}']"
        partial = True
    # collect all testcases we need
    all_testcase_ids = set()
    for version in versions:
        for testcase_ids in version['targets'].values():
            all_testcase_ids.update(testcase_ids)
    # collect scripts to be run
    testcase_lookup = spec['testcases']
    tc_script_lookup = spec['tc_scripts']
    script_info = {}
    for tc_id in all_testcase_ids:
        script = tc_script_lookup[tc_id]
        if 'executable' not in script:
            continue  # manual check
        if config.sections and script.get('section') not in config.sections:
            continue
        if config.tests and not config.tests.match(tc_id):
            continue
        item = script_info.get(id(script))
        if item is None:
            _, testcase_ids = script_info[id(script)] = (script, [])
        else:
            _, testcase_ids = item
        testcase_ids.append(tc_id)
    # run scripts
    invocations = [
        runner.run(script, testcases=sorted(testcases))
        for script, testcases in script_info.values()
    ]
    results = {}
    for invocation in invocations:
        results.update(invocation['results'])
    # now report: to console if requested, and likewise for yaml output
    if not config.quiet:
        # print a horizontal line if we had any script output
        if runner.spamminess:
            print("********" * 10)  # 80 characters
        for version in versions:
            print(f"{config.subject} {title} {version['version']}:")
            print_report(testcase_lookup, version['targets'], results, partial, config.verbose)
    if config.output:
        report = create_report(argv, config, spec, invocations)
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
