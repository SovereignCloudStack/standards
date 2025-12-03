---
title: SCS Standard Images
type: Standard
status: Draft
track: IaaS
description: |
  The SCS-0104 standard establishes guidelines for virtual machine images in Sovereign Cloud Stack (SCS)
  environments, specifying mandatory as well as recommended images, ensuring interoperability and streamlined
  deployments. It mandates that image upload via Glance must be allowed, ensuring flexibility for users.
replaces: scs-0104-v1-standard-images.md
---

## Introduction

The [Sovereign Cloud Stack (SCS)](https://scs.community) provides standards for a range of cloud infrastructure types.
It strives for interoperable and sovereign cloud offerings which can be deployed and used by a wide range of organizations and individuals.

To this end, SCS unifies the naming and sourcing of virtual machine images, and for certain images their presence is mandated or recommended.

## Uploading custom images

Image upload via Glance MUST be allowed based on a fair-use policy.

## Mandatory image sources

### Generic OS images

For an OS image with `os_purpose=generic`, the `image_source` SHOULD come from the original vendor.
Specifically, the following forms are even REQUIRED:

| `os_distro` | `os_version` | permissible `image_source` form(s) |
| --- | --- | ----|
| debian | [N]N | `https://cloud.debian.org/images/cloud/{codename}/...` |
|        |   | `https://cdimage.debian.org/cdimage/cloud/{codename}/...` |
| ubuntu | NN.NN | `https://cloud-images.ubuntu.com/releases/{codename}/...` |
|        |       | `https://cloud-images.ubuntu.com/{codename}/...` |

### Official SCS CAPI images

For each image whose name matches the regular expression

    ubuntu-capi-image( |-)v[0-9]\.[0-9]+(\.[0-9]+)?

the following property values MUST be set:

| property | value (pattern) |
| --- | --- |
| `image_source` | `https://nbg1.your-objectstorage.com/osism/openstack-k8s-capi-images/...` |
| | (tolerable for compatibility): `https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/...` |
| `os_purpose` | `k8snode` |
| `image_description` | `https://github.com/osism/k8s-capi-images` |

CSPs are free to register CAPI images with a different naming scheme from different source.

## Mandatory and recommended images

The tables in this section show what images are required or recomended.

Note that this standard does not prohibit any images, and neither
does it preclude the operator from providing any and all optional images,
so long as they do not violate above regulations on image sources.

### Generic OS images

Each row of the following table describes an image that MUST or SHOULD exist,
depending on the value in the column 'status'.

| status | os_distro | os_version | os_purpose |
| --- | --- | --- | --- |
| required | `ubuntu` | latest LTS, no later than April 30 | `generic` |
| recommended | `ubuntu` | previous LTS | `generic` |
| recommended | `debian` | latest stable, no later than one month after release | `generic` |
| recommended | `debian` | previous stable | `generic` |

A generic OS image MAY be named in the form "distro version",
without codename or build date; for instance,

- `Ubuntu 24.04`,
- `Debian 13`.

Note: when a new LTS/stable version is released and the respective image added to the environment,
the images of any previous versions may or may not be kept.

### Official SCS CAPI images

An image whose name matches the regular expression

    ubuntu-capi-image-v[0-9]\.[0-9]+(\.[0-9]+)?

SHOULD be present.
