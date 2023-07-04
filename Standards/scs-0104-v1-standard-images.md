---
title: SCS Standard Images
type: Standard
status: Draft
track: IaaS
---

## Standard images

The following images are mandatory:

- `Ubuntu <LATESTLTS>`, `Ubuntu <PREVLTS>`, `Debian <STABLE>`
- Note that `<LATESTLTS>` refers to the latest LTS version, which at this point is `22.04`.
  The `<PREVLTS>` is the previous LTS version, at the time of this writing (7/2023) it's `20.04`.
  We don't carry the `.x` patch numbers in the standard image names. We switch to requiring the
  newest Ubuntu LTS version when the `.1` version comes out (around July/August). At this point
  the old `<PREVLTS>` version becomes optional ...
- For Debian, we use the latest STABLE version, which is `12` at the time of this writing.
  Similar to Ubuntu, we would do the switch and require the latest STABLE to be made available within
  ~3 months after release.

The following images are recommended:

- `Alma Linux 8`, `Alma Linux 9` (whichever versions are being supported upstream)
- `Debian <PREVSTABLE>` (the one pre-latest `<STABLE>`, `10` at the time of writing)
- `Fedora <LATEST>` (`36` currently, this will get replaced quickly as the next Fedora comes out)

We suggest the following supported images (with licensing/maintenance/support as intended from OS vendor)

- `SLES 15SP4`
- `RHEL 9`, `RHEL 8`
- `Windows Server 2022`, `Windows Server 2019`

We are also looking into standard suggestions for

- `openSUSE Leap 15.4`
- `Cirros 0.5.2`
- `Alpine`
- `Arch`

The suggestions mainly serve to align image naming between providers.

Note that additional images will be available on typical platforms, e.g. `ubuntu-capi-image-v1.24.4`
for platforms that are prepared to support SCS k8s cluster management.
