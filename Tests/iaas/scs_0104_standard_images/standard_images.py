from collections import defaultdict
from datetime import date
import logging
import re

import yaml


logger = logging.getLogger(__name__)


_specs = yaml.safe_load(r"""
"ubuntu-capi-image-1":
  name_scheme: "ubuntu-capi-image v[0-9]\\.[0-9]+(\\.[0-9]+)?"
  source:
  - https://nbg1.your-objectstorage.com/osism/openstack-k8s-capi-images/
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2404-kube
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube
"ubuntu-capi-image-2":
  # this name_scheme uses `-` to separate base name "ubuntu-capi-image" from version
  # latest openstack-image-manager can be told to use `-` by setting `separator: "-"` on the image
  name_scheme: "ubuntu-capi-image-v[0-9]\\.[0-9]+(\\.[0-9]+)?"
  source:
  - https://nbg1.your-objectstorage.com/osism/openstack-k8s-capi-images/
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2404-kube
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube
"Ubuntu 24.04":
  source:
  - https://cloud-images.ubuntu.com/releases/noble/
  - https://cloud-images.ubuntu.com/noble/
"Ubuntu 22.04":
  source:
  - https://cloud-images.ubuntu.com/releases/jammy/
  - https://cloud-images.ubuntu.com/jammy/
"Ubuntu 20.04":
  source:
  - https://cloud-images.ubuntu.com/releases/focal/
  - https://cloud-images.ubuntu.com/focal/
"Debian 13":
  source:
  - https://cloud.debian.org/images/cloud/trixie/
  - https://cdimage.debian.org/cdimage/cloud/trixie/
"Debian 12":
  source:
  - https://cloud.debian.org/images/cloud/bookworm/
  - https://cdimage.debian.org/cdimage/cloud/bookworm/
"Debian 11":
  source:
  - https://cloud.debian.org/images/cloud/bullseye/
  - https://cdimage.debian.org/cdimage/cloud/bullseye/
"Debian 10":
  source:
  - https://cloud.debian.org/images/cloud/buster/
  - https://cdimage.debian.org/cdimage/cloud/buster/
""")
SCS_0104_IMAGE_SPECS = {key: {'name': key, **val} for key, val in _specs.items()}

IMAGE_SOURCES = {
    'debian': ['https://cloud.debian.org/images/cloud/', 'https://cdimage.debian.org/cdimage/cloud/'],
    'ubuntu': ['https://cloud-images.ubuntu.com/'],
}
CAPI_RE = re.compile(r"ubuntu-capi-image( |-)v[0-9]\\.[0-9]+(\\.[0-9]+)?")
CAPI_SOURCES = [
    'https://nbg1.your-objectstorage.com/osism/openstack-k8s-capi-images/',
    'https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/',
]
CAPI_PURPOSE = 'k8snode'
CAPI_DESC = 'https://github.com/osism/k8s-capi-images'


def _lookup_images(image_lookup, image_spec):
    name_scheme = image_spec.get('name_scheme')
    if name_scheme:
        rex = re.compile(name_scheme)
        return [img for name, img in image_lookup.items() if rex.match(name)]
    img = image_lookup.get(image_spec['name'])
    if img is None:
        return []
    return [img]


def compute_image_lookup_ex(images):
    """Compute image lookup via os_distro, for all images with os_purpose=generic"""
    lookup = defaultdict(list)
    for img in images:
        if not img.os_distro:
            continue
        if img.properties.get('os_purpose', '') != 'generic':
            continue
        lookup[img.os_distro].append(img)
    return lookup


def compute_scs_0104_source(image_lookup, image_spec):
    """
    This test ensures that every image matching `image_spec` has the correct `image_source`.

    For an impression of what these specs look like, refer to `SCS_0104_IMAGE_SPECS`.
    """
    matches = _lookup_images(image_lookup, image_spec)
    return _check_image_source(matches, image_spec['source'])


def _check_image_source(matches, sources):
    errors = 0
    for image in matches:
        img_source = image.properties.get('image_source', '')
        if not isinstance(sources, (tuple, list)):
            sources = [sources]
        if not any(img_source.startswith(src) for src in sources):
            errors += 1
            logger.error(f"Image '{image.name}' source mismatch: '{img_source}' matches none of these prefixes: {', '.join(sources)}")
    return not errors


def compute_scs_0104_source_ex(image_lookup_ex, os_distro):
    matches = image_lookup_ex.get(os_distro, ())
    logger.debug(f"matches for {os_distro!r}: {', '.join([match.name for match in matches]) or 'none'}")
    return _check_image_source(matches, IMAGE_SOURCES[os_distro])


def compute_scs_0104_source_capi(
    image_lookup, rex=CAPI_RE, sources=CAPI_SOURCES, purpose=CAPI_PURPOSE, desc=CAPI_DESC,
):
    matches = [img for name, img in image_lookup.items() if rex.match(name)]
    logger.debug(f"matches for CAPI: {', '.join([match.name for match in matches]) or '(none)'}")
    errors = 0
    if not _check_image_source(matches, sources):
        errors += 1
    for img in matches:
        actual = img.properties.get('os_purpose', '(not set)')
        if actual != purpose:
            errors += 1
            logger.error(f"Image {img.name!r} should have os_purpose {purpose!r}, has {actual!r}")
        actual = img.properties.get('image_description', '(not set)')
        if actual != desc:
            errors += 1
            logger.error(f"Image {img.name!r} should have image_description {desc!r}, has {actual!r}")
    return not errors


def compute_scs_0104_image(image_lookup, image_spec):
    """
    This test ensures that a certain image is present, as specified by `image_spec`.

    For an impression of what these specs look like, refer to `SCS_0104_IMAGE_SPECS`.
    """
    matches = _lookup_images(image_lookup, image_spec)
    if not matches:
        logger.error(f"Missing image '{image_spec['name']}'")
        return False
    return True


def compute_scs_0104_image_ubuntu_latest(image_lookup_ex, os_distro='ubuntu'):
    """
    This test ensures that current Ubuntu LTS is present.
    """
    today = date.today()
    acceptable_year = today.year - today.year % 1
    acceptable = [f'{acceptable_year % 100:2d}.04']
    if date.year == acceptable_year and today.month <= 4:
        acceptable.append(f'{acceptable_year % 100 - 2}.04')
    matches = [
        image
        for image in image_lookup_ex.get(os_distro, ())
        if image.os_version in acceptable
    ]
    logger.debug(f"matches for current {os_distro!r} LTS: {', '.join([match.name for match in matches]) or '(none)'}")
    if not matches:
        logger.error(f"Missing generic {os_distro} image with os_version in {acceptable!r}")
        return False
    return True
