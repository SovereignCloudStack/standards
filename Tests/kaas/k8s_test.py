#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:

"""Kubernetes testcase runner

(c) Matthias Büchse <matthias.buechse@alasca.cloud>, 7/2026
SPDX-License-Identifier: CC-BY-SA 4.0
"""

from datetime import datetime
import getopt
import logging
import os
import os.path
import sys
import uuid

import yaml

from scs_0210_version_policy.k8s_version_policy import version_policy_check
from sonobuoy_handler.sonobuoy_handler import SonobuoyHandler


HERE = os.path.dirname(__file__)
SCS_SONOBUOY_CONFIG_PATH = os.path.join(HERE, 'scs-sonobuoy-config-v1.yaml')
KUBECONFIG_ROOT = os.path.join(os.path.expanduser('~'), '.local', 'share', 'scs', 'clusters')

logger = logging.getLogger(__name__)


def usage(rcode=1, file=sys.stderr):
    """help output"""
    print("Usage: k8s_test.py [options] testcase-id1 ... testcase-idN", file=file)
    print("Options:", file=file)
    print("  [-c/--cluster-id CLUSTER_ID] (required)", file=file)
    print("  [-s/--subject SUBJECT]", file=file)
    print("  [--execution-mode MODE] Sonobuoy mode: serial, parallel, or dry", file=file)
    print("Runs specified testcases against the kubeconfig specified via cluster_id.", file=file)
    print("Reports inconsistencies, errors etc.; returns 0 on success.", file=file)
    print("Instead of listing testcase-ids, you can supply a single dash (-)", file=file)
    print("to have them read from stdin, one testcase-id per line.", file=file)
    sys.exit(rcode)


class Config:
    def __init__(self):
        self.cluster_id = None
        self.subject = None
        self.mode = 'serial'
        self.testcases = []

    def apply_argv(self, argv):
        """Parse cli arguments from the script call"""
        try:
            opts, args = getopt.gnu_getopt(argv, "c:s:", ("cluster-id=", "subject=", "execution-mode="))
        except getopt.GetoptError as exc:
            print(f"CRITICAL: {exc!r}", file=sys.stderr)
            usage(1)
        for opt in opts:
            if opt[0] == "-h" or opt[0] == "--help":
                usage(0)
            elif opt[0] == "-c" or opt[0] == "--cluster-id":
                self.cluster_id = opt[1]
            elif opt[0] == "-s" or opt[0] == "--subject":
                self.subject = opt[1]
            elif opt[0] == "--execution-mode":
                self.mode = opt[1]
            else:
                usage(2)
        if len(args) == 1 and args[0] == '-':
            args = sys.stdin.read().splitlines()
        self.testcases = [t for t in args if t in TESTCASES]
        if len(self.testcases) != len(args):
            unknown = [a for a in args if a not in self.testcases]
            logger.warning(f"ignoring unknown testcases: {','.join(unknown)}")
        if not self.cluster_id:
            print("CRITICAL: You need to have KUBECONFIG set or pass --kubeconfig=KUBECONFIG.", file=sys.stderr)
            sys.exit(1)
        if not self.subject:
            self.subject = self.cluster_id

    @property
    def kubeconfig_path(self):
        return os.path.join(KUBECONFIG_ROOT, self.cluster_id, 'kubeconfig.yaml')

    def compute_sono_args(self, *args):
        if self.mode == 'parallel':
            # This is merely a shortcut to simplify commandline in scs-compatible-kaas.yaml
            # For more on parallel execution, see https://github.com/vmware-tanzu/sonobuoy/issues/1435
            args += ('--e2e-parallel=true', )
        elif self.mode == 'dry':
            # mutually exclusive with parallel, it turns out!
            args += ('--plugin-env e2e.E2E_DRYRUN=true', )
        return args + ('--plugin-env e2e.E2E_EXTRA_ARGS=--ginkgo.flake-attempts=2', )


def run_sono(config, testcase, *args):
    return SonobuoyHandler(
        SCS_SONOBUOY_CONFIG_PATH, testcase, config.kubeconfig_path,
        args=config.compute_sono_args(*args),
    ).run()


TESTCASES = {
    'cncf-k8s-conformance': lambda config, name: run_sono(config, name, '--mode=certified-conformance'),
    'kaas-networking-check': lambda config, name: run_sono(config, name, '--e2e-focus "NetworkPolicy"'),
    'version-policy-check': lambda config, _: version_policy_check(config.kubeconfig_path),
}


def harness(name, results, *check_fns):
    """Harness for evaluating testcase `name`.

    Logs beginning and end of computation.
    Calls each fn in `check_fns`.
    Records result to `results`.
    """
    logger.info(f'*** {name}')
    try:
        result = all(check_fn() for check_fn in check_fns)
    except BaseException:
        logger.debug('exception during check', exc_info=True)
        value = 0
    else:
        value = 1 if result else -1
    result = ['FAIL', 'ABORT', 'PASS'][value + 1]
    logger.info(f'+++ {name}: {result}')
    results[name] = value


def run_preflight_checks(kubeconfig):
    # make sure that we can connect to the cloud
    pass


class _LogHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET, log=None):
        super().__init__(level=level)
        self.log = [] if log is None else log

    def handle(self, record):
        self.log.append(f'{record.levelname}: {record.getMessage()}')


def main(argv):
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    config = Config()
    config.apply_argv(argv)

    try:
        run_preflight_checks(config.kubeconfig_path)
    except Exception:
        logger.critical("Pre-flight checks failed.")
        raise

    results = {}
    log = []
    logging.root.addHandler(_LogHandler(level=logging.DEBUG, log=log))
    for testcase in config.testcases:
        harness(testcase, results, lambda: TESTCASES[testcase](config, testcase))
    report = {
        'uuid': str(uuid.uuid4()),
        'creator': 'k8s_test.py v0.1.0',
        'checked_at': datetime.now(),
        'subject': config.subject,
        'scope': '1fffebe6-fd4b-44d3-a36c-fc58b4bb0180',
        'tests': {
            key: {'result': value}
            for key, value in results.items()
        },
        'log': log,
    }
    # don't do explicit_start here because that can easily be done by the caller using "echo ---",
    # and then the caller can even add fields such as uuid, subject, and scope
    yaml.safe_dump(report, sys.stdout, default_flow_style=False, sort_keys=False, explicit_start=False)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        sys.exit(1)
