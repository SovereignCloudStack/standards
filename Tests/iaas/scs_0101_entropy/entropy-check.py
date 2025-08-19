#!/usr/bin/env python3
"""Entropy checker

Check given cloud for conformance with SCS standard regarding
entropy, to be found under /Standards/scs-0101-v1-entropy.md

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    WARNING   for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.
"""
import getopt
import logging
import os
import sys
import warnings

import openstack
import openstack.cloud


try:
    from . import entropy_check
except ImportError:
    import entropy_check


logger = logging.getLogger(__name__)


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: entropy-check.py [options]
This tool checks the requested images and flavors according to the SCS Standard 0101 "Entropy".
Options:
 [-c/--os-cloud OS_CLOUD] sets cloud environment (default from OS_CLOUD env)
 [-d/--debug] enables DEBUG logging channel
 [-i/--images IMAGE_LIST] sets images to be tested, separated by comma.
 [-V/--image-visibility VIS_LIST] filters images by visibility
                                  (default: 'public,community'; use '*' to disable)
""", end='', file=file)


def print_result(check_id, passed):
    print(check_id + ": " + ('FAIL', 'PASS')[bool(passed)])


def main(argv):
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    warnings.filterwarnings("ignore", "search_floating_ips")

    try:
        opts, args = getopt.gnu_getopt(argv, "c:i:hdV:", ["os-cloud=", "images=", "help", "debug", "image-visibility="])
    except getopt.GetoptError as exc:
        logger.critical(f"{exc}")
        print_usage()
        return 1

    cloud = os.environ.get("OS_CLOUD")
    image_visibility = set()
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            print_usage()
            return 0
        if opt[0] == "-i" or opt[0] == "--images":
            logger.info("ignoring obsolete option -i")
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

    try:
        logger.debug(f"Connecting to cloud '{cloud}'")
        with openstack.connect(cloud=cloud, timeout=32) as conn:
            all_images = conn.list_images()
            all_flavors = conn.list_flavors(get_extra=True)

            if '*' not in image_visibility:
                logger.debug(f"Images: filter for visibility {', '.join(sorted(image_visibility))}")
                all_images = [img for img in all_images if img.visibility in image_visibility]
            all_image_names = [f"{img.name} ({img.visibility})" for img in all_images]
            logger.debug(f"Images: {', '.join(all_image_names) or '(NONE)'}")

            if not all_images:
                logger.critical("Can't run this test without image")
                return 1

            logger.debug("Checking images and flavors for recommended attributes")
            print_result('entropy-check-image-properties', entropy_check.compute_scs_0101_image_property(all_images))
            print_result('entropy-check-flavor-properties', entropy_check.compute_scs_0101_flavor_property(all_flavors))

            logger.debug("Checking dynamic instance properties")
            canonical_image = entropy_check.compute_canonical_image(all_images)
            collected_vm_output = entropy_check.compute_collected_vm_output(conn, all_flavors, canonical_image)
            print_result('entropy-check-rngd', entropy_check.compute_scs_0101_rngd(collected_vm_output, canonical_image.name))
            scs_0101_entropy_avail_result = entropy_check.compute_scs_0101_entropy_avail(collected_vm_output, canonical_image.name)
            scs_0101_fips_test_result = entropy_check.compute_scs_0101_fips_test(collected_vm_output, canonical_image.name)
            entropy_check_result = entropy_check.compute_scs_0101_entropy_check(
                scs_0101_entropy_avail_result,
                scs_0101_fips_test_result,
            )
            print_result('entropy-check-entropy-avail', scs_0101_entropy_avail_result)
            print_result('entropy-check-fips-test', scs_0101_fips_test_result)
            print_result('entropy-check', entropy_check_result)
        return not entropy_check_result
    except BaseException as e:
        logger.critical(f"{e!r}")
        logger.debug("Exception info", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
