#!/usr/bin/env python3
"""Volume types checker

Check given cloud for conformance with SCS standard regarding
volume types, to be found under /Standards/scs-0112-v1-volume-types.md

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    INFO      for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
from collections import Counter, defaultdict
import getopt
import logging
import os
import re
import sys

import openstack
import openstack.cloud


logger = logging.getLogger(__name__)
RECOGNIZED_FEATURES = ('encrypted', 'replicated')


def extract_feature_list(description, pattern=re.compile(r"\[scs:([^\[\]]*)\]")):
    """Extract feature-list-like prefix

    If given `description` starts with a feature-list-like prefix, return list of features,
    otherwise None. To be more precise, we look for a string of this form:

    `[scs:`feat1`, `...`, `...featN`]`

    where N >= 1 and featJ is a string that doesn't contain any comma or brackets. We return
    the list [feat1, ..., featN] of substrings.
    """
    if not description:
        # The description can be None or empty - we need to catch this here
        # otherwise we will get a critical Error in the pattern matching
        return
    match = pattern.match(description)
    if not match:
        return
    fs = match.group(1)
    if not fs:
        return []
    return fs.split(", ")


def test_feature_list(type_name: str, fl: list[str], recognized=RECOGNIZED_FEATURES):
    """Test given list of features and report errors to error channel"""
    if not fl:
        # either None (no feature list) or empty feature list: nothing to check
        return
    if fl != sorted(fl):
        logger.error(f"{type_name}: feature list not sorted")
    ctr = Counter(fl)
    duplicates = [key for key, c in ctr.items() if c > 1]
    if duplicates:
        logger.error(f"{type_name}: duplicate features: {', '.join(duplicates)}")
    unrecognized = [f for f in ctr if f not in recognized]
    if unrecognized:
        logger.error(f"{type_name}: unrecognized features: {', '.join(unrecognized)}")


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: entropy-check.py [options]
This tool checks volume types according to the SCS Standard 0112 "Volume Types".
Options:
 [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
 [-d/--debug] enables DEBUG logging channel
""", end='', file=file)


class CountingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        self.bylevel = Counter()

    def handle(self, record):
        self.bylevel[record.levelno] += 1


def main(argv):
    # configure logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    # count the number of log records per level (used for summary and return code)
    counting_handler = CountingHandler(level=logging.INFO)
    logger.addHandler(counting_handler)

    try:
        opts, args = getopt.gnu_getopt(argv, "c:i:hd", ["os-cloud=", "help", "debug"])
    except getopt.GetoptError as exc:
        logger.critical(f"{exc}")
        print_usage()
        return 1

    cloud = os.environ.get("OS_CLOUD")
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-d" or opt[0] == "--debug":
            logging.getLogger().setLevel(logging.DEBUG)

    if not cloud:
        logger.critical("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.")
        return 1

    try:
        logger.debug(f"Connecting to cloud '{cloud}'")
        with openstack.connect(cloud=cloud, timeout=32) as conn:
            volume_types = conn.list_volume_types()
        # collect volume types according to features
        by_feature = defaultdict(list)
        for typ in volume_types:
            fl = extract_feature_list(typ.description)
            if fl is None:
                continue
            logger.debug(f"{typ.name}: feature list {fl!r}")
            test_feature_list(typ.name, fl)
            for feat in fl:
                by_feature[feat].append(typ.name)
        logger.debug(f"volume types by feature: {dict(by_feature)}")
        for feat in ('encrypted', 'replicated'):
            if not by_feature[feat]:
                logger.warning(f"Recommendation violated: missing {feat} volume type")
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)

    c = counting_handler.bylevel
    logger.debug(
        "Total critical / error / warning: "
        f"{c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.WARNING]}"
    )
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
