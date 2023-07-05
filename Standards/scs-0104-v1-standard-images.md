---
title: SCS Standard Images
type: Standard
status: Draft
track: IaaS
---

## Standard images

### Mandatory images

The following images are mandatory:

| image pattern         | notes                  | current image (as of July 2023)  |
| :-------------------- | :--------------------- | :------------------------------- |
| `Ubuntu <LATESTLTS>`  | latest LTS version     | `Ubuntu 22.04`                   |
| `Ubuntu <PREVLTS>`    | previous LTS version   | `Ubuntu 20.04`                   |
| `Debian <STABLE>`     | latest stable version  | `Debian 12`                      |

We don't carry the `.x` patch numbers in the standard image names. We switch to requiring the
newest Ubuntu LTS version when the `.1` version comes out (around July/August). At this point
the old `<PREVLTS>` version becomes optional.

For Debian, we require the latest STABLE to be made available within ~3 months after release.

### Recommended images

The following images are recommended:

| image pattern             | notes                   | current image as of July 2023  |
| :------------------------ | :---------------------- | :----------------------------- |
| `Debian <PREVSTABLE>`     | previous stable version | `Debian 11`                    |
| `Fedora <LATEST>`         | ./.                     | `Fedora 38`                    |

For Fedora, the image will get replaced quickly as the next Fedora comes out.

### Additional images

We suggest the following supported images (with licensing/maintenance/support as intended from OS vendor)

- `SLES 15SP4`
- `RHEL 9`, `RHEL 8`
- `Windows Server 2022`, `Windows Server 2019`

The suggestions mainly serve to align image naming between providers.

Note that additional images will be available on typical platforms, e.g. `ubuntu-capi-image-v1.24.4`
for platforms that are prepared to support SCS k8s cluster management.

## Image lifecycle

**TODO**: Recommendations on how to deal with images that used to be mandatory or recommended, but
aren't any longer (such as Debian 10)?

## Conformance Tests

The script `images-openstack.py` will read the lists of mandatory and recommended images
from a yaml file provided as command-line argument, connect to an OpenStack installation,
and check whether the images are present. Missing images will be reported on various
logging channels: error for mandatory, info for recommended images. The return code
will be non-zero if the test could not be performed or if any mandatory image is missing.
