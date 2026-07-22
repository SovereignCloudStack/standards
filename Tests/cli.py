#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import os
import os.path
import re
import sys
import tempfile
import uuid

import click
import yaml

from scs_cert_lib import load_spec, annotate_validity, add_period, normalize_scope


HERE = os.path.dirname(__file__)
DEFAULT_SPECPATH = {
    '50393e6f-2ae1-4c5c-a62c-3b75f2abef3f': os.path.join(HERE, 'scs-compatible-iaas.yaml'),
    '1fffebe6-fd4b-44d3-a36c-fc58b4bb0180': os.path.join(HERE, 'scs-compatible-kaas.yaml'),
}

logger = logging.getLogger(__name__)


def _load_spec(specpath):
    specpath = DEFAULT_SPECPATH.get(normalize_scope(specpath), specpath)
    with open(specpath, "r", encoding="UTF-8") as fileobj:
        return load_spec(yaml.load(fileobj, Loader=yaml.SafeLoader))


def select_valid(versions: list) -> list:
    return [version for version in versions if version['_explicit_validity']]


@click.group()
def cli():
    return


@cli.command()
@click.option('--version', '-V', 'version', type=str, default=None)
@click.option('--tests', '-t', 'tests', type=str, default=None)
@click.option('--section', '-S', 'sections', type=str, multiple=True)
@click.argument('specpath', type=str)
def select(specpath, version, sections, tests):
    spec = _load_spec(specpath)
    checkdate = datetime.date.today()
    annotate_validity(spec['timeline'], spec['versions'], checkdate)
    if version is None:
        versions = select_valid(spec['versions'].values())
    else:
        versions = [spec['versions'].get(version)]
        if versions[0] is None:
            raise RuntimeError(f"Requested version '{version}' not found")
    if not versions:
        raise RuntimeError(f"No valid version found for {checkdate}")
    title = spec['name']
    if sections:
        title += f" [sections: {', '.join(sections)}]"
    if tests:
        title += f" [tests: '{tests}']"
        tests_re = re.compile(tests)
    # collect all testcases we need
    testcase_lookup = spec['testcases']
    all_testcase_ids = set()
    for version in versions:
        for tc_id in version['testcase_ids']:
            if sections and testcase_lookup.get(tc_id, {}).get('section') not in sections:
                continue
            if tests and not tests_re.match(tc_id):
                continue
            all_testcase_ids.add(tc_id)
    logger.info(f"{title}: {len(all_testcase_ids)} testcases")
    if all_testcase_ids:
        print('\n'.join(sorted(all_testcase_ids)))


def _update_scorecard(scorecard, report, testcase_lookup):
    subject = report['subject']
    scopeuuid = report['scope']
    if subject != scorecard.setdefault('subject', subject):
        raise RuntimeError('subjects do not match')
    if scopeuuid != scorecard.setdefault('scope', scopeuuid):
        raise RuntimeError('scopes do not match')
    scores = scorecard.setdefault('results', {})
    uuid = report['uuid']
    checked_at = report['checked_at']
    checked_at_str = str(checked_at)[:19]
    for tc_id, result in report.get('tests', {}).items():
        score = scores.get(tc_id)
        if score is None or score['checked_at'] < checked_at_str:
            testcase = testcase_lookup.get(tc_id)
            lifetime = testcase.get('lifetime')  # leave None if not present; to be handled by add_period
            expires_at = add_period(checked_at, lifetime)
            scores[tc_id] = {
                'report': uuid,
                'checked_at': checked_at_str,
                'expires_at': str(expires_at),
                **result
            }


def _prune_scorecard(scorecard, testcase_lookup, grace_period_days=7):
    scores = scorecard.setdefault('results', {})
    now_str = str(datetime.datetime.now())[:19]
    grace_str = str(datetime.datetime.now() - datetime.timedelta(days=grace_period_days))[:19]
    for tc_id in list(scores):
        score = scores[tc_id]
        # keep results for known testcases if they haven't expired
        if tc_id in testcase_lookup and score['expires_at'] < now_str:
            continue
        # keep results for unknown testcases for a week to leave time for migration
        if score['checked_at'] > grace_str:
            continue
        del scores[tc_id]


def _atomic_write(path, text):
    with tempfile.NamedTemporaryFile(
        mode='w', encoding='UTF-8',
        dir=os.path.dirname(path) or '.',
        delete=False, delete_on_close=False,
    ) as fileobj:
        fileobj.write(text)
    os.rename(fileobj.name, path)


def _dump(o):
    return yaml.safe_dump(o, default_flow_style=False, sort_keys=False, explicit_start=True)


@cli.command()
@click.option('--subject', '-s', 'subject', type=str)
@click.option('--score', '-S', 'score_yaml', type=click.Path(exists=False), default=None)
@click.option('-o', '--output', 'report_yaml', type=click.Path(exists=False), default=None)
@click.option('--spec', 'specpath', type=click.Path(exists=True))
def score(specpath, subject, score_yaml, report_yaml):
    scorecard = {}
    if score_yaml and os.path.exists(score_yaml):
        with open(score_yaml, "r", encoding="UTF-8") as fileobj:
            scorecard = yaml.load(fileobj, Loader=yaml.SafeLoader)
        if not subject:
            subject = scorecard['subject']
        if not specpath:
            specpath = scorecard['scope']
    elif not subject:
        raise click.UsageError('need to supply at least one of -s or -S')
    elif not specpath:
        raise click.UsageError('need to supply at least one of --spec or -S')
    spec = _load_spec(specpath)
    scopeuuid = spec['uuid']
    snippet = yaml.load(sys.stdin.read(), Loader=yaml.SafeLoader)
    if not snippet:
        logger.warning('Empty report snippet. Bailing')
        return
    report = {
        'uuid': str(uuid.uuid4()),
        'subject': subject,
        'scope': scopeuuid,
        **snippet
    }
    if report_yaml is None:
        ts = str(report['checked_at'])[:19]
        ts = ts.replace(':', '').replace('-', '').replace(' ', 'T')
        report_yaml = f'report-{ts}-{subject}.yaml'
    _atomic_write(report_yaml, _dump(report))
    if score_yaml:
        _prune_scorecard(scorecard, spec['testcases'])
        _update_scorecard(scorecard, report, spec['testcases'])
        _atomic_write(score_yaml, _dump(scorecard))
        # collect report uuids
        # prune reports


@cli.command()
@click.option('--subject', '-s', 'subject', type=str)
@click.option('--spec', 'specpath', type=click.Path(exists=True))
@click.argument('score_yaml', type=click.Path(exists=False))
def init(specpath, subject, score_yaml):
    spec = _load_spec(specpath)
    scorecard = {
        'subject': subject,
        'scope': spec['uuid'],
        'results': {},
    }
    _atomic_write(score_yaml, _dump(scorecard))


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli()
