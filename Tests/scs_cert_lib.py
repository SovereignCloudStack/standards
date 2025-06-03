#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs_cert_lib.py
#
# (c) Matthias Büchse <matthias.buechse@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0

from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
import logging
import re


logger = logging.getLogger(__name__)

# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables', 'modules', 'timeline'),
    'versions': ('version', 'include', 'targets', 'stabilized_at'),
    'modules': ('id', 'run', 'testcases', 'url', 'name', 'parameters'),
    'run': ('executable', 'env', 'args', 'section'),
    'testcases': ('lifetime', 'id', 'description', 'tags'),
    'include': ('ref', 'parameters'),
}
# The canonical result values are -1, 0, and 1, for FAIL, MISS (or DNF), and PASS, respectively;
# these concrete numbers are important because we do rely on their ordering. Note that MISS/DNF should
# not be reported because it is tantamount to a result being absent. (Therefore the NIL_RESULT default
# value below.)
TESTCASE_VERDICTS = {'PASS': 1, 'FAIL': -1}
NIL_RESULT = {'result': 0}


def _check_keywords(ctx, d, keywords=KEYWORDS):
    """
    Recursively check `d` (usually a `dict`, but maybe a `list` or a `tuple`) for correctness.

    Returns number of errors.

    Here, correctness means that the dict may only use keywords as given via `keywords`.
    """
    valid = keywords.get(ctx)
    if valid is None:
        return 0  # stop recursion
    if isinstance(d, (list, tuple)):
        return sum(_check_keywords(ctx, v, keywords=keywords) for v in d)
    if not isinstance(d, dict):
        return 0
    invalid = [k for k in d if k not in valid]
    if invalid:
        logger.error(f"{ctx} uses unknown keywords: {','.join(invalid)}")
    return len(invalid) + sum(_check_keywords(k, v, keywords=keywords) for k, v in d.items())


def _resolve_spec(spec: dict):
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
            {'module': module_lookup[inc['ref']], 'parameters': inc.get('parameters', {})}
            for inc in version['include']
        ]
    # step 4b. resolve references to versions in timeline
    # on second thought, let's not go there: it's a canonical extension map, and it should remain that way.
    # however, we still have to look for name errors
    for entry in spec['timeline']:
        for vname in entry['versions']:
            # trigger KeyError
            _ = version_lookup[vname]


def load_spec(document: dict) -> dict:
    """check `document` (usually parsed YAML) and convert for further usage"""
    if _check_keywords('spec', document):
        # super simple syntax check (recursive)
        raise RuntimeError('syntax problems in spec file. bailing')
    _resolve_spec(document)
    return document


def annotate_validity(timeline: list, versions: dict, checkdate: date):
    """annotate `versions` with validity info from `timeline` (note that this depends on `checkdate`)"""
    validity_lookup = max(
        (entry for entry in timeline if entry['date'] <= checkdate),
        key=lambda entry: entry['date'],
        default={},
    ).get('versions', {})
    for vname, version in versions.items():
        validity = validity_lookup.get(vname)
        version['validity'] = validity or 'deprecated'
        version['_explicit_validity'] = validity


def add_period(dt: datetime, period: str) -> datetime:
    """
    Given a `datetime` instance `dt` and a `str` instance `period`, compute the `datetime` when this period
    expires, where period is one of: "day", "week", "month", or "quarter". For instance, with a period
    of (calendar) "week", this period expires on midnight the next monday after `dt` + 7 days. This
    computation is used to implement Regulations 2 and 3 of the standard scs-0004 -- see

    https://docs.scs.community/standards/scs-0004-v1-achieving-certification#regulations
    """
    # compute the moment of expiry (so we are valid before that point, but not on that point)
    if period == 'day':
        dt += timedelta(days=2)
        return datetime(dt.year, dt.month, dt.day)  # omit time so as to arrive at midnight
    # week is default, so use it if period is None
    if period is None or period == 'week':
        dt += timedelta(days=14 - dt.weekday())
        return datetime(dt.year, dt.month, dt.day)  # omit time so as to arrive at midnight
    if period == 'month':
        if dt.month == 11:
            return datetime(dt.year + 1, 1, 1)
        if dt.month == 12:
            return datetime(dt.year + 1, 2, 1)
        return datetime(dt.year, dt.month + 2, 1)
    if period == 'quarter':
        if dt.month >= 10:
            return datetime(dt.year + 1, 4, 1)
        if dt.month >= 7:
            return datetime(dt.year + 1, 1, 1)
        if dt.month >= 4:
            return datetime(dt.year, 10, 1)
        return datetime(dt.year, 7, 1)
    if period == 'infinite':
        # admittedly HACKY, but this case is better handled by caller
        return datetime(dt.year + 1000, 1, 1)


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


class TestSuite:
    def __init__(self, name):
        self.name = name
        self.checks = []
        self.testcases = []
        self.ids = Counter()
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

    def include_testcases(self, testcases):
        self.testcases.extend(testcases)
        self.ids.update(testcase["id"] for testcase in testcases)

    def select(self, name, selectors):
        suite = TestSuite(name)
        if isinstance(selectors, str):
            # convenience: allow callers to supply serialized form (they don't care, rightly so)
            selectors = [parse_selector(sel_str) for sel_str in selectors.split(',')]
        suite.include_testcases([tc for tc in self.testcases if test_selectors(selectors, tc['tags'])])
        return suite

    def eval_buckets(self, results) -> tuple[list[dict], list[dict], list[dict]]:
        """returns lists of (failed, missing, passed) test cases"""
        by_value = defaultdict(list)
        for testcase in self.testcases:
            value = results.get(testcase['id'], NIL_RESULT).get('result', 0)
            by_value[value].append(testcase)
        return by_value[-1], by_value[0], by_value[1]

    def evaluate(self, results) -> int:
        """returns overall result"""
        return min([
            results.get(testcase['id'], NIL_RESULT).get('result', 0)
            for testcase in self.testcases
        ], default=0)


def compile_suite(basename: str, include: list, sections: tuple = (), tests: re.Pattern = None) -> TestSuite:
    suite = TestSuite(basename)
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
        suite.include_testcases(testcases)
        # only add checks if they contain desired testcases
        if not tests or any(tests.match(ch['id']) for ch in testcases):
            suite.include_checks(module, inc['parameters'], sections=sections)
    return suite
