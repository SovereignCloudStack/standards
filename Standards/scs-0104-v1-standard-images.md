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

| image pattern             | notes                   | current image(s) as of July 2023  |
| :------------------------ | :---------------------- | :-------------------------------- |
| `Debian <PREVSTABLE>`     | previous stable version | `Debian 11`                       |
| `Fedora <LATEST>`         | ./.                     | `Fedora 38`                       |
| `Alma Linux <SUPPORTED>`  | any supported versions  | `Alma Linux 8`, `Alma Linux 9`    |

For Fedora, the image will get replaced quickly as the next Fedora comes out.

### Additional remarks

We suggest the following supported images (with licensing/maintenance/support as intended from OS vendor)

- `SLES 15SP4`
- `RHEL 9`, `RHEL 8`
- `Windows Server 2022`, `Windows Server 2019`

The suggestions mainly serve to align image naming between providers.

Note that additional images will be available on typical platforms, e.g. `ubuntu-capi-image-v1.24.4`
for platforms that are prepared to support SCS k8s cluster management.
