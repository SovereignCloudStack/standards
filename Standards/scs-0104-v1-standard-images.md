---
title: SCS Standard Images
type: Standard
status: Stable
stabilized_at: 2024-02-21
track: IaaS
description: |
  The SCS-0104 standard establishes guidelines for virtual machine images in Sovereign Cloud Stack (SCS) environments,
  specifying mandatory, recommended, and optional images via a YAML file, ensuring interoperability and streamlined
  deployments. It mandates that image upload via Glance must be allowed, ensuring flexibility for users. The standard's
  machine-readable document facilitates automated processing for compliance and integration purposes, promoting
  consistency and reliability in cloud environments.
---

## Introduction

The [Sovereign Cloud Stack (SCS)](https://scs.community) provides standards for a range of cloud infrastructure types.
It strives for interoperable and sovereign cloud offerings which can be deployed and used by a wide range of organizations and individuals.

To this end, SCS unifies the naming and sourcing of virtual machine images, and for certain images their presence is mandated or recommended.

## Motivation

Following the example of the [SCS standards YAML](scs-0003-v1-sovereign-cloud-standards-yaml.md),
this standard establishes, by means of a YAML file, a mechanism with the following main objectives:

- to maintain a list of mandatory, recommended, and optional images, which also fixes the source location,
- to provide a machine-readable document for further processing (e.g. for a compliance tool suite or continuous integration).

## Uploading custom images

Image upload via Glance MUST be allowed based on a fair-use policy.

## Standard images YAML

The YAML file MUST contain the key `images`, whose value is a list of objects. Each object has one of two forms, as described below.

### Image specification, single image

| Key       | Type                 | Description                                          | Example                                              |
| --------- | -------------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| `name`    | String               | Name of the image                                    | `"Debian 12"`                                        |
| `status`  | String               | _optional_: either `mandatory` or `recommended`      | `"recommended"`                                      |
| `source`  | String               | Prefix of the source URL                             | `"https://cloud.debian.org/images/cloud/bookworm/"`  |
|           | OR: List of strings  | multiple possible prefixes                           | (see full example below)                             |

The meaning of this specification is as follows.

1. If the status is `mandatory`, then the image MUST be present.
2. If an image by the name given is present, then its `image_source` property
   (as described in the [Image Metadata standard](scs-0102-v1-image-metadata.md))
   MUST start with one of the prefixes given via `source`.

### Image specification, class of images

| Key           | Type                 | Description                                          | Example                                          |
| ------------- | -------------------- | ---------------------------------------------------- | ------------------------------------------------ |
| `name`        | String               | Name of the class of images                          | `"ubuntu-2204-kube"`                             |
| `name_scheme` | String (regex)       | Regular expression for the image name                | `"ubuntu-2204-kube-v[0-9].[0-9]+(.[0-9]+)?"`     |
| `status`      | String               | _optional_: either `mandatory` or `recommended`      | `"recommended"`                                  |
| `source`      | String               | Prefix of the source URL                             | `"https://swift.services.a.regiocloud.tech"`     |
|               | OR: List of strings  | multiple possible prefixes                           | (see full example below)                         |

The meaning of this specification is as follows:

1. If the status is `mandatory`, then at least one image MUST be present whose name
   matches the regular expression given via `name_scheme`.
2. For any image whose name matches the regular expression given via `name_scheme`,
   its `image_source` property MUST start with one of the prefixes given via `source`.

## Full example

```yaml
images:
- name: "Ubuntu 22.04"
  source:
  - https://cloud-images.ubuntu.com/releases/jammy/
  - https://cloud-images.ubuntu.com/jammy/
  status: mandatory
- name: "ubuntu-capi-image"
  name_scheme: "ubuntu-capi-image-v[0-9].[0-9]+(.[0-9]+)?"
  source: https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube
  status: recommended
- name: "Ubuntu 20.04"
  source:
  - https://cloud-images.ubuntu.com/releases/focal/
  - https://cloud-images.ubuntu.com/focal/
- name: "Debian 12"
  source:
  - https://cloud.debian.org/images/cloud/bookworm/
  - https://cdimage.debian.org/cdimage/cloud/bookworm/
- name: "Debian 11"
  source:
  - https://cloud.debian.org/images/cloud/bullseye/
  - https://cdimage.debian.org/cdimage/cloud/bullseye/
```

This example provides allowable source prefixes for two Debian versions, two Ubuntu
versions, and for any version of the Kubernetes cloud API provider. Only the latter is
recommended, while only Ubuntu 22.04 is mandatory.

## Lifecycle considerations

### YAML lifecycle

The YAML file is generally located in this repository under `/Tests/iaas`.

Any change that could render existing installations non-conformant (i.e., when new
specifications are added, when the name scheme of a specification is changed so as to
match more names than before, when the status of an existing specification changes to
mandatory, or when some source prefix is removed) requires a new YAML file to be created.
As a consequence, any currently valid certificates stay valid; the change can only take
effect in a new version of the certificate in question, if so desired.

### Image lifecycle

It is important to note that this standard does not prohibit any images, and neither
does it preclude the operator from providing any and all optional images.

It is possible that a specification is mandatory in one version and non-mandatory in the
next version. This standard makes no statement as to what is supposed to happen to the
corresponding images in a live cloud environment. It is recommended to keep the
once-mandatory images in the live environment. As for new environments, it is up to the
operator whether to provide any or all of these images, as stated above.

## Conformance Tests

The script `images-openstack.py` will read the lists of mandatory and recommended images
from a yaml file provided as command-line argument, connect to an OpenStack installation,
and check whether the images are present. Missing images will be reported on various
logging channels: error for mandatory, info for recommended images. Additionally, images
whose `image_source` does not conform with the specifications will be reported on the
error channel. The return code will be non-zero if the test could not be performed or
if any errors have been reported.

## Operational tooling

The [openstack-image-manager](https://github.com/osism/openstack-image-manager) is able to
create all standard, mandatory SCS images for you given image definitions from a YAML file.
