#!/usr/bin/env python3
"""Standard flavors checker for OpenStack

Check given cloud for conformance with SCS standard regarding standard flavors,
to be found under /Standards/scs-0103-v1-standard-flavors.md

The respective list of flavors is defined in a corresponding yaml file; this script
expects the path of such a file as its only positional argument.

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    INFO      for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
from collections import Counter
import getopt
import logging
import os
import re
import sys
import tempfile
import time
import warnings

import openstack
import openstack.cloud
import yaml


logger = logging.getLogger(__name__)


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: flavors-openstack.py [options] YAML
This tool checks the flavors according to the SCS Standard 0103 "Standard Flavors".
Arguments:
 YAML   path to the file containing the flavor definitions corresponding to the version
        of the standard to be tested
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
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    # count the number of log records per level (used for summary and return code)
    counting_handler = CountingHandler(level=logging.INFO)
    logger.addHandler(counting_handler)

    try:
        opts, args = getopt.gnu_getopt(argv, "c:hd", ["os-cloud=", "help", "debug"])
    except getopt.GetoptError as exc:
        logger.critical(f"{exc}")
        print_usage()
        return 1

    if len(args) != 1:
        logger.critical("Missing YAML argument, or too many arguments")
        print_usage()
        return 1

    yaml_path = args[0]
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
        with open(yaml_path, "rb") as fileobj:
            flavor_spec_data = yaml.safe_load(fileobj)
    except Exception as e:
        logger.critical(f"Unable to load '{yaml_path}': {e!r}")
        logger.debug("Exception info", exc_info=True)
        return 1

    if 'meta' not in flavor_spec_data or 'name_key' not in flavor_spec_data['meta']:
        logger.critical("Flavor definition missing 'meta' field or field incomplete")
        return 1

    if 'flavor_groups' not in flavor_spec_data:
        logger.critical("Flavor definition missing 'flavor_groups' field")

    name_key = flavor_spec_data['meta']['name_key']
    # compute union of all flavor groups, copying group info (mainly "status") to each flavor
    # check if the spec is complete while we are at it
    flavor_specs = []
    for flavor_group in flavor_spec_data['flavor_groups']:
        group_info = dict(flavor_group)
        group_info.pop('list')
        missing = {'status'} - set(group_info)
        if missing:
            logging.critical(f"Flavor group missing attributes: {', '.join(missing)}")
            return 1
        for flavor_spec in flavor_group['list']:
            missing = {'name', 'cpus', 'ram'} - set(flavor_spec)
            if missing:
                logging.critical(f"Flavor spec missing attributes: {', '.join(missing)}")
                return 1
            flavor_specs.append({"_group": group_info, **flavor_spec})

    try:
        logger.debug(f"Fetching flavors from cloud '{cloud}'")
        with openstack.connect(cloud=cloud, timeout=32) as conn:
            present_flavors = conn.list_flavors(get_extra=True)
            by_name = {
                flavor.extra_specs[name_key]: flavor
                for flavor in present_flavors
                if name_key in flavor.extra_specs
            }

        logger.debug(f"Checking {len(flavor_specs)} flavor specs against {len(present_flavors)} flavors")
        for flavor_spec in flavor_specs:
            flavor = by_name.get(flavor_spec['name'])
            if not flavor:
                status = flavor_spec['_group']['status']
                level = {"mandatory": logging.ERROR}.get(status, logging.INFO)
                logger.log(level, f"Missing {status} flavor '{flavor_spec['name']}'")
                continue
            # check that flavor matches flavor_spec
            # name and corresponding extra_spec do match, because that's how we found the flavor in the first place...
            # cpu, ram, and disk should match, and they should match precisely for discoverability
            if flavor.vcpus != flavor_spec['cpus']:
                logger.error(f"Flavor '{flavor.name}' violating CPU constraint: {flavor.vcpus} != {flavor_spec['cpus']}")
            if flavor.ram != 1024 * flavor_spec['ram']:
                logger.error(f"Flavor '{flavor.name}' violating RAM constraint: {flavor.ram} != {1024 * flavor_spec['ram']}")
            if flavor.disk != flavor_spec.get('disk', 0):
                logger.error(f"Flavor '{flavor.name}' violating disk constraint: {flavor.disk} != {flavor_spec.get('disk', 0)}")
            # other fields besides name, cpu, ram, and disk should also match
            report = [
                f"{key}: {es_value!r} should be {value!r}"
                for key, value, es_value in [
                    (key, value, flavor.extra_specs.get(f"scs:{key}"))
                    for key, value in flavor_spec.items()
                    if key not in ('_group', 'name', 'cpus', 'ram', 'disk')
                ]
                if value != es_value
            ]
            if report:
                logger.error(f"Flavor '{flavor.name}' violating property constraints: {'; '.join(report)}")
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)

    c = counting_handler.bylevel
    logger.debug(f"Total critical / error / info: {c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.INFO]}")
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
