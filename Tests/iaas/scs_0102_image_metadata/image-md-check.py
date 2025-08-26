#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# SCS/Docs/tools/image-md-check.py

"""
Retrieve metadata from (public) images and check for compliance
with SCS specifications.

(c) Kurt Garloff <kurt@garloff.de>, 09/2022
SPDX-License-Identifier: CC-BY-SA-4.0
"""

from collections import Counter
import getopt
import logging
import os
import sys

import openstack


from image_metadata import \
    compute_scs_0102_prop_architecture, compute_scs_0102_prop_hash_algo, compute_scs_0102_prop_min_disk, \
    compute_scs_0102_prop_min_ram, compute_scs_0102_prop_os_version, compute_scs_0102_prop_os_distro, \
    compute_scs_0102_prop_hw_disk_bus, compute_scs_0102_prop_hypervisor_type, compute_scs_0102_prop_hw_rng_model, \
    compute_scs_0102_prop_image_build_date, compute_scs_0102_prop_image_original_user, \
    compute_scs_0102_prop_image_source, compute_scs_0102_prop_image_description, \
    compute_scs_0102_prop_replace_frequency, compute_scs_0102_prop_provided_until, \
    compute_scs_0102_prop_uuid_validity, compute_scs_0102_prop_hotfix_hours, \
    compute_scs_0102_image_recency


logger = logging.getLogger(__name__)


def usage(ret):
    "Usage information"
    print("Usage: image-md-check.py [options] [images]")
    print("image-md-check.py will create a report on public images by retrieving")
    print(" the image metadata (properties) and comparing this against the image")
    print(" metadata spec from SCS.")
    print("Options: --os-cloud CLOUDNAME: Use this cloud config, default is $OS_CLOUD")
    print(" -p/--private : Also consider private images")
    print(" -v/--verbose : Be more verbose")
    print(" -h/--help    : Print this usage information")
    print(" [-V/--image-visibility VIS_LIST] : filters images by visibility")
    print("                (default: 'public,community'; use '*' to disable)")
    print("If you pass images, only these will be validated, otherwise all images")
    print("(filtered according to -p, -V) from the catalog will be processed.")
    sys.exit(ret)


def main(argv):
    "Main entry point"
    # configure logging, disable verbose library logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    openstack.enable_logging(debug=False)
    image_visibility = set()
    private = False
    cloud = os.environ.get("OS_CLOUD")
    err = 0
    try:
        opts, args = getopt.gnu_getopt(argv[1:], "phvc:sV:",
                                       ("private", "help", "os-cloud=", "verbose", "skip-completeness", "image-visibility="))
    except getopt.GetoptError:  # as exc:
        print("CRITICAL: Command-line syntax error", file=sys.stderr)
        usage(1)
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            usage(0)
        elif opt[0] == "-p" or opt[0] == "--private":
            private = True  # only keep this for backwards compatibility (we have -V now)
        elif opt[0] == "-v" or opt[0] == "--verbose":
            logging.getLogger().setLevel(logging.DEBUG)
        elif opt[0] == "-s" or opt[0] == "--skip-completeness":
            logger.info("ignoring obsolete command-line option -s")
        elif opt[0] == "-c" or opt[0] == "--os-cloud":
            cloud = opt[1]
        if opt[0] == "-V" or opt[0] == "--image-visibility":
            image_visibility.update([v.strip() for v in opt[1].split(',')])
    image_names = args
    if not cloud:
        print("CRITICAL: Need to specify --os-cloud or set OS_CLOUD environment.", file=sys.stderr)
        usage(1)
    if not image_visibility:
        image_visibility.update(("public", "community"))
    if private:
        image_visibility.add("private")
    try:
        conn = openstack.connect(cloud=cloud, timeout=24)
        all_images = list(conn.image.images())
        if '*' not in image_visibility:
            logger.debug(f"Images: filter for visibility {', '.join(sorted(image_visibility))}")
            all_images = [img for img in all_images if img.visibility in image_visibility]
        all_image_names = [f"{img.name} ({img.visibility})" for img in all_images]
        logger.debug(f"Images: {', '.join(all_image_names) or '(NONE)'}")
        by_name = {img.name: img for img in all_images}
        if len(by_name) != len(all_images):
            counter = Counter([img.name for img in all_images])
            duplicates = [name for name, count in counter.items() if count > 1]
            print(f'WARNING: duplicate names detected: {", ".join(duplicates)}', file=sys.stderr)
        if image_names:
            images = [by_name[nm] for nm in image_names]
        else:
            images = all_images
        result = all((
            compute_scs_0102_prop_architecture(images),
            compute_scs_0102_prop_min_disk(images),
            compute_scs_0102_prop_min_ram(images),
            compute_scs_0102_prop_os_version(images),
            compute_scs_0102_prop_os_distro(images),
            compute_scs_0102_prop_hw_disk_bus(images),
            compute_scs_0102_prop_image_build_date(images),
            compute_scs_0102_prop_image_original_user(images),
            compute_scs_0102_prop_image_source(images),
            compute_scs_0102_prop_image_description(images),
            compute_scs_0102_prop_replace_frequency(images),
            compute_scs_0102_prop_provided_until(images),
            compute_scs_0102_prop_uuid_validity(images),
            compute_scs_0102_prop_hotfix_hours(images),
            compute_scs_0102_image_recency(images),
        ))
        print("image-metadata-check: " + ('FAIL', 'PASS')[min(1, result)])
        # recommended stuff
        _ = all((
            compute_scs_0102_prop_hash_algo(images),
            compute_scs_0102_prop_hypervisor_type(images),
            compute_scs_0102_prop_hw_rng_model(images),
        ))
    except BaseException as exc:
        print(f"CRITICAL: {exc!r}", file=sys.stderr)
        return 1 + err
    return err


if __name__ == "__main__":
    sys.exit(main(sys.argv))
