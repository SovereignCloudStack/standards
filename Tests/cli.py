#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile

import click
import yaml

from scs_cert_lib import load_spec, annotate_validity, add_period, normalize_scope


MONITOR_URL = "https://compliance.sovereignit.cloud/"
HERE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'scs')
STATE_PATH = os.path.join(os.path.expanduser('~'), '.local', 'share', 'scs')
KEYFILE_PATH = os.path.join(CONFIG_PATH, '.secret', 'keyfile')
TOKENFILE_PATH = os.path.join(CONFIG_PATH, '.secret', 'tokenfile')
DEFAULT_SPECPATH = {
    '50393e6f-2ae1-4c5c-a62c-3b75f2abef3f': os.path.join(HERE, 'scs-compatible-iaas.yaml'),
    '1fffebe6-fd4b-44d3-a36c-fc58b4bb0180': os.path.join(HERE, 'scs-compatible-kaas.yaml'),
}
SCOPE_DIR = {
    '50393e6f-2ae1-4c5c-a62c-3b75f2abef3f': 'scs-compatible-iaas',
    '1fffebe6-fd4b-44d3-a36c-fc58b4bb0180': 'scs-compatible-kaas',
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


def _sign_report(target_path):
    return subprocess.run([
        shutil.which('ssh-keygen'),
        '-Y', 'sign',
        '-f', KEYFILE_PATH,
        '-n', 'report',
        target_path,
    ]).returncode


def _upload_report(target_path, monitor_url):
    try:
        with open(TOKENFILE_PATH, "r") as fileobj:
            auth_token = fileobj.read().strip()
    except Exception as e:
        logger.error(f"Unable to load token ({e!s}). Aborting upload to compliance monitor")
        return 1
    return subprocess.run([
        shutil.which('curl'),
        '--fail-with-body',
        '--data-binary', f'@{target_path}.sig',
        '--data-binary', f'@{target_path}',
        '-H', 'Content-Type: application/x-signed-yaml',
        '-H', f'Authorization: Basic {auth_token}',
        f"{monitor_url.removesuffix('/')}/reports",
    ]).returncode


def _update_scorecard(scorecard, report, testcase_lookup):
    subject = report['subject']
    scopeuuid = report['scope']
    if subject != scorecard['subject']:
        raise RuntimeError('subjects do not match')
    if scopeuuid != scorecard['scope']:
        raise RuntimeError('scopes do not match')
    scores = scorecard['results']
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
        print(tc_id, score['expires_at'], now_str, score['checked_at'], grace_str)
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


@cli.command(name='import')
@click.option('--monitor-url', 'monitor_url', type=str, default=MONITOR_URL)
def import_report(monitor_url):
    report = yaml.load(sys.stdin.read(), Loader=yaml.SafeLoader)
    if not report:
        logger.warning('Empty report. Bailing')
        return
    uuid = report['uuid']
    subject = report['subject']
    scopeuuid = report['scope']
    basepath = os.path.join(STATE_PATH, SCOPE_DIR[scopeuuid], subject)
    os.makedirs(basepath, exist_ok=True)
    # save report
    report_yaml = os.path.join(basepath, f'report-{uuid}.yaml')
    if os.path.exists(report_yaml):
        raise RuntimeError(f"File 'report-{uuid}.yaml' already exists; report uuid NOT UNIQUE?")
    _atomic_write(report_yaml, _dump(report))
    _sign_report(report_yaml)
    _upload_report(report_yaml, monitor_url)
    # handle scorecard
    score_yaml = os.path.join(basepath, 'scorecard.yaml')
    if os.path.exists(score_yaml):
        with open(score_yaml, "r", encoding="UTF-8") as fileobj:
            scorecard = yaml.load(fileobj, Loader=yaml.SafeLoader)
    else:
        scorecard = {'subject': subject, 'scope': scopeuuid, 'results': {}}
    spec = _load_spec(scopeuuid)
    _prune_scorecard(scorecard, spec['testcases'])
    _update_scorecard(scorecard, report, spec['testcases'])
    _atomic_write(score_yaml, _dump(scorecard))
    # prune reports that don't occur in scorecard (i.e., old ones)
    report_uuids = set(result['report'] for result in scorecard['results'].values())
    fns = os.listdir(basepath)
    for fn in fns:
        if not fn.startswith('report-'):
            continue
        uuid = fn.removeprefix('report-').removesuffix('.sig').removesuffix('.yaml')
        if len(uuid) != 36 or uuid in report_uuids:
            continue
        logger.info(f"Pruning {fn!s}")
        os.unlink(os.path.join(basepath, fn))


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli()
