import logging
import re

import yaml


logger = logging.getLogger(__name__)


_specs = yaml.safe_load(r"""
"ubuntu-capi-image-1":
  name_scheme: "ubuntu-capi-image v[0-9]\\.[0-9]+(\\.[0-9]+)?"
  source:
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2404-kube
  - https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube
"ubuntu-capi-image-2":
  # this name_scheme uses `-` to separate base name "ubuntu-capi-image" from version
  # latest openstack-image-manager can be told to use `-` by setting `separator: "-"` on the image
  name_scheme: "ubuntu-capi-image-v[0-9]\\.[0-9]+(\\.[0-9]+)?"
  source:
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


def _lookup_images(image_lookup, image_spec):
    name_scheme = image_spec.get('name_scheme')
    if name_scheme:
        rex = re.compile(name_scheme)
        return [img for name, img in image_lookup.items() if rex.match(name)]
    img = image_lookup.get(image_spec['name'])
    if img is None:
        return []
    return [img]


def compute_scs_0104_source(image_lookup, image_spec):
    """
    This test ensures that every image matching `image_spec` has the correct `image_source`.

    For an impression of what these specs look like, refer to `SCS_0104_IMAGE_SPECS`.
    """
    matches = _lookup_images(image_lookup, image_spec)
    errors = 0
    for image in matches:
        img_source = image.properties.get('image_source', '')
        sources = image_spec['source']
        if not isinstance(sources, (tuple, list)):
            sources = [sources]
        if not any(img_source.startswith(src) for src in sources):
            errors += 1
            logger.error(f"Image '{image.name}' source mismatch: '{img_source}' matches none of these prefixes: {', '.join(sources)}")
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
