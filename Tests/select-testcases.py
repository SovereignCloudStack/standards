#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
import sys
import getopt
import datetime
import logging
import yaml

from scs_cert_lib import load_spec, annotate_validity


logger = logging.getLogger(__name__)


def usage(file=sys.stdout):
    """Output usage information"""
    print("""Usage: select-testcases.py [options] SPEC_YAML

Arguments:
  SPEC_YAML: yaml file specifying the certificate scope

Options:
  -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
  -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
  -S/--sections SECTION_LIST: comma-separated list of sections to test (default: all sections)
  -t/--tests REGEX: regular expression to select individual testcases based on their ids
""", file=file)


class Config:
    def __init__(self):
        self.arg0 = None
        self.checkdate = datetime.date.today()
        self.version = None
        self.sections = None
        self.tests = None

    def apply_argv(self, argv):
        """Parse options. May exit the program."""
        try:
            opts, args = getopt.gnu_getopt(argv, "hd:V:S:t:", (
                "help", "date=", "version=", "sections=", "tests=",
            ))
        except getopt.GetoptError:
            usage(file=sys.stderr)
            raise
        for opt in opts:
            if opt[0] == "-h" or opt[0] == "--help":
                usage()
                sys.exit(0)
            elif opt[0] == "-d" or opt[0] == "--date":
                self.checkdate = datetime.date.fromisoformat(opt[1])
            elif opt[0] == "-V" or opt[0] == "--version":
                self.version = opt[1]
            elif opt[0] == "-S" or opt[0] == "--sections":
                self.sections = [x.strip() for x in opt[1].split(",")]
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


def main(argv):
    """Entry point for the checker"""
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    config = Config()
    config.apply_argv(argv)
    with open(config.arg0, "r", encoding="UTF-8") as specfile:
        spec = load_spec(yaml.load(specfile, Loader=yaml.SafeLoader))
    annotate_validity(spec['timeline'], spec['versions'], config.checkdate)
    if config.version is None:
        versions = select_valid(spec['versions'].values())
    else:
        versions = [spec['versions'].get(config.version)]
        if versions[0] is None:
            raise RuntimeError(f"Requested version '{config.version}' not found")
    if not versions:
        raise RuntimeError(f"No valid version found for {config.checkdate}")
    title = spec['name']
    if config.sections:
        title += f" [sections: {', '.join(config.sections)}]"
    if config.tests:
        title += f" [tests: '{config.tests.pattern}']"
    # collect all testcases we need
    testcase_lookup = spec['testcases']
    all_testcase_ids = set()
    for version in versions:
        for tc_id in version['testcase_ids']:
            if config.sections and testcase_lookup.get(tc_id, {}).get('section') not in config.sections:
                continue
            if config.tests and not config.tests.match(tc_id):
                continue
            all_testcase_ids.add(tc_id)
    logger.info(f"{title}: {len(all_testcase_ids)} testcases")
    if all_testcase_ids:
        print('\n'.join(sorted(all_testcase_ids)))


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as exc:
        logger.critical(f"{str(exc) or repr(exc)}")
        raise
