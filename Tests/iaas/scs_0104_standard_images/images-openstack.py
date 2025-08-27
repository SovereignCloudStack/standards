#!/usr/bin/env python3
"""Standard images checker for OpenStack

Check given cloud for conformance with SCS standard regarding standard images,
to be found under /Standards/scs-0104-v1-standard-images.md

The respective list of images is defined in a corresponding yaml file; this script
expects the path of such a file as its only positional argument.

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    WARNING   for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
from collections import Counter
import getopt
import logging
import os
import re
import sys

import openstack
import openstack.cloud
import yaml


logger = logging.getLogger(__name__)


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: images-openstack.py [options] YAML
This tool checks the flavors according to the SCS Standard 0104 "Standard Images".
Arguments:
 YAML   path to the file containing the image definitions corresponding to the version
        of the standard to be tested
Options:
 [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
 [-d/--debug] enables DEBUG logging channel
 [-V/--image-visibility VIS_LIST] filters images by visibility
                                  (default: 'public,community'; use '*' to disable)
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
        opts, args = getopt.gnu_getopt(argv, "c:hdV:", ["os-cloud=", "help", "debug", "image-visibility="])
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
    image_visibility = set()
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-d" or opt[0] == "--debug":
            logging.getLogger().setLevel(logging.DEBUG)
        if opt[0] == "-V" or opt[0] == "--image-visibility":
            image_visibility.update([v.strip() for v in opt[1].split(',')])

    if not cloud:
        logger.critical("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.")
        return 1

    if not image_visibility:
        image_visibility.update(("public", "community"))

    # we only support local files; but we allow specifying the following URLs for the sake of
    # better documentation
    prefix = next(p for p in (
        'https://raw.githubusercontent.com/SovereignCloudStack/standards/main/Tests/',
        'https://github.com/SovereignCloudStack/standards/blob/main/Tests/',
        '',  # sentinel (do not remove!)
    ) if yaml_path.startswith(p))
    if prefix:
        yaml_path = yaml_path[len(prefix):]
    try:
        with open(yaml_path, "rb") as fileobj:
            image_data = yaml.safe_load(fileobj)
    except Exception as e:
        logger.critical(f"Unable to load '{yaml_path}': {e!r}")
        logger.debug("Exception info", exc_info=True)
        return 1

    if 'images' not in image_data:
        logger.critical("Image definition missing 'images' field")
        return 1

    image_specs = image_data['images']
    try:
        logger.debug(f"Fetching image list from cloud '{cloud}'")
        with openstack.connect(cloud=cloud, timeout=32) as conn:
            present_images = conn.list_images(show_all=True)
        if '*' not in image_visibility:
            logger.debug(f"Images: filter for visibility {', '.join(sorted(image_visibility))}")
            present_images = [img for img in present_images if img.visibility in image_visibility]
        all_image_names = [f"{img.name} ({img.visibility})" for img in present_images]
        logger.debug(f"Images: {', '.join(all_image_names) or '(NONE)'}")
        by_name = {
            image.name: image
            for image in present_images
        }

        logger.debug(f"Checking {len(image_specs)} image specs against {len(present_images)} images")
        for image_spec in image_specs:
            name_scheme = image_spec.get('name_scheme')
            if name_scheme:
                rex = re.compile(name_scheme)
                matches = [img for name, img in by_name.items() if rex.match(name)]
            else:
                matches = [img for img in (by_name.get(image_spec['name']), ) if img is not None]
            if not matches:
                status = image_spec.get('status', 'optional')
                level = {"mandatory": logging.ERROR, "recommended": logging.WARNING}.get(status, logging.DEBUG)
                logger.log(level, f"Missing {status} image '{image_spec['name']}'")
                continue
            for image in matches:
                img_source = image.properties['image_source']
                sources = image_spec['source']
                if not isinstance(sources, (tuple, list)):
                    sources = [sources]
                if not any(img_source.startswith(src) for src in sources):
                    logger.error(f"Image '{image.name}' source mismatch: {img_source} matches none of these prefixes: {', '.join(sources)}")
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)

    c = counting_handler.bylevel
    logger.debug(f"Total critical / error / warning: {c[logging.CRITICAL]} / {c[logging.ERROR]} / {c[logging.WARNING]}")
    if not c[logging.CRITICAL]:
        print("standard-images-check: " + ('PASS', 'FAIL')[min(1, c[logging.ERROR])])
    return min(127, c[logging.CRITICAL] + c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
