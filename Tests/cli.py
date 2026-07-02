#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
import datetime
import logging

import click
import yaml

from scs_cert_lib import load_spec, annotate_validity


logger = logging.getLogger(__name__)


def select_valid(versions: list) -> list:
    return [version for version in versions if version['_explicit_validity']]


@click.group()
def cli():
    return


@cli.command()
@click.option('--version', '-V', 'version', type=str, default=None)
@click.option('--tests', '-t', 'tests', type=str, default=None)
@click.option('--section', '-S', 'sections', type=str, multiple=True)
@click.argument('specpath', type=click.Path(exists=True))
def select(specpath, version, sections, tests):
    with open(specpath, "r", encoding="UTF-8") as specfile:
        spec = load_spec(yaml.load(specfile, Loader=yaml.SafeLoader))
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


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli()
