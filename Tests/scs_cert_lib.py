#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs_cert_lib.py
#
# (c) Matthias Büchse <matthias.buechse@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from datetime import datetime, date, timedelta
import logging
import uuid


logger = logging.getLogger(__name__)
__VERSION__ = "20260623"

# valid keywords for various parts of the spec, to be checked using `check_keywords`
KEYWORDS = {
    'spec': ('uuid', 'name', 'url', 'versions', 'prerequisite', 'variables', 'scripts', 'groups', 'timeline'),
    'scripts': ('executable', 'env', 'args', 'testcases'),
    'versions': ('version', 'test'),
    'groups': ('id', 'url', 'name', 'include'),
    'testcases': ('lifetime', 'section', 'id', 'description', 'url'),
}
# The canonical result values are -1, 0, and 1, for FAIL, ABORT, and PASS, respectively;
# -- in addition, None is used to encode a missing value, but must not be included in a formal report! --
# these concrete numbers are important because we do rely on their ordering.
TESTCASE_VERDICTS = {'PASS': 1, 'ABORT': 0, 'FAIL': -1}


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


def _collect_testcases(test, result_list):
    if 'attn' in test:
        result_list.append(test)
    for child in test.get('include', ()):
        _collect_testcases(child, result_list)
    return result_list


def collect_testcases(*tests):
    result_list = []
    for test in tests:
        _collect_testcases(test, result_list)
    return result_list


def _resolve_spec(spec: dict):
    """rewire `spec` so as to make most lookups via name unnecessary, and to find name errors early"""
    if isinstance(spec['versions'], dict):
        raise RuntimeError('spec dict already in resolved form')
    # there are currently two types of objects that are being referenced by name or id
    # - modules, referenced by id
    # - versions, referenced by name (unfortunately, the field is called "version")
    # step 1. build lookups
    testcase_lookup = {}
    tc_script_lookup = {}
    for idx, script in enumerate(spec.get('scripts', ())):
        script['_idx'] = idx
        for testcase in script.get('testcases', ()):
            id_ = testcase['id']
            if id_ in testcase_lookup:
                raise RuntimeError(f"duplicate testcase {id_}")
            testcase['attn'] = 0  # count: how many stable versions list this in target 'main'?
            testcase_lookup[id_] = testcase
            tc_script_lookup[id_] = script
    group_lookup = {group['id']: group for group in spec['groups']}
    test_lookup = dict(**group_lookup, **testcase_lookup)
    version_lookup = {version['version']: version for version in spec['versions']}
    # step 2. check for duplicates:
    if len(group_lookup) != len(spec['groups']):
        raise RuntimeError("spec contains duplicate module ids")
    if len(version_lookup) != len(spec['versions']):
        raise RuntimeError("spec contains duplicate version ids")
    # step 3. replace fields 'groups' and 'versions' by respective lookups
    spec['groups'] = group_lookup
    spec['versions'] = version_lookup
    # step 3a. add testcase lookup
    spec['testcases'] = testcase_lookup
    spec['tc_scripts'] = tc_script_lookup
    # step 4. resolve references
    # step 4a. resolve 'include' in groups
    for group in spec['groups'].values():
        # empty group need not specify include.
        # next to resolving references, also ensure here that attribute exists
        include = group.get('include', ())
        group['include'] = [test_lookup[inc] for inc in include]
    # step 4b. resolve 'test' in versions
    for idx, version in enumerate(spec['versions'].values()):
        version['_idx'] = idx
        test = test_lookup[version['test']]
        testcases = collect_testcases(test)
        if version.get('stabilized_at'):
            for testcase in testcases:
                testcase['attn'] += 1
        version['test'] = test
        version['testcase_ids'] = [testcase['id'] for testcase in testcases]
    # step 4b. resolve references to versions in timeline
    # on second thought, let's not go there: it's a canonical extension map, and it should remain that way.
    # however, we still have to look for name errors
    for entry in spec['timeline']:
        for vname in entry['versions']:
            # trigger KeyError
            _ = version_lookup[vname]
    # step 5. unify variables declaration (the list may contain strings as well as singleton dicts)
    variables = []
    defaults = {}
    for var_decl in spec.get('variables', ()):
        if isinstance(var_decl, dict):
            defaults.update(var_decl)
        if isinstance(var_decl, str):
            variables.append(var_decl)
    variables.extend(defaults)
    spec['variables'] = variables
    spec['var_defaults'] = defaults


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
    if period == 'year':
        if dt.month == 11:
            return datetime(dt.year + 2, 1, 1)
        if dt.month == 12:
            return datetime(dt.year + 2, 2, 1)
        return datetime(dt.year + 1, dt.month + 2, 1)
    raise RuntimeError(f'unknown period: {period}')


def eval_buckets(results, testcase_ids) -> dict:
    """
    returns buckets of test cases by means of a mapping

    None: list of missing testcases
    -1: list of failed testcases
    0: list of aborted testcases
    1: list of passed testcases
    """
    by_value = defaultdict(list)
    for testcase_id in testcase_ids:
        value = results.get(testcase_id, {})
        if isinstance(value, dict):
            value = value.get('result')
        by_value[value].append(testcase_id)
    return by_value


def evaluate(results, testcase_ids) -> int:
    """returns overall result"""
    buckets = eval_buckets(results, testcase_ids)
    for value in (-1, None, 0):
        if buckets[value]:
            return value
    return 1


def make_report(scopeuuid, subject, results, log, creator=None, checked_at=None):
    if creator is None:
        creator = f"SCS test suite; version={__VERSION__}"
    return {
        "uuid": str(uuid.uuid4()),
        "creator": creator,
        "scope": scopeuuid,
        "checked_at": checked_at or datetime.now(),
        "subject": subject,
        "tests": {
            testcase_id: {
                "result": value,
            }
            for testcase_id, value in results.items()
        },
        "log": log,
    }
