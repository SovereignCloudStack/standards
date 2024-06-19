---
title: "SCS Standard Images: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0104-v1-standard-images.md
---

## Introduction

The standard defines a set of images with specified names and properties.

## Implementation notes

The [OpenStack Image Manager from osism](https://github.com/osism/openstack-image-manager)
will create a set of images from a file provided by the user.
The SCS project provides such a [file](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/SCS-Spec.Images.yaml) derived from the [`scs-0104-v1-images.yaml`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml), which is
defined by the standard to contain the mandatory and recommended images.
This also enables the easy adoption of the ["SCS Image Metadata Standard (scs-0102-v1-image-metadata)"](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0102-v1-image-metadata.md).

## Automated tests

### Images sample

Some checks need to be performed on a live instance. For these checks, the [`scs-0104-v1-images.yaml`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml)
file is used as a default to check the images provided on the IaaS instance
against the expected set of images.

### Errors and warnings

The test provides a return value of up to 127, depending on the number of errors that occurred
during testing. Additionally, logs are provided to provide further information:

- CRITICAL   for problems preventing the test to complete,
- ERROR      for violations of requirements,
- WARNING    for violations of recommendations,
- DEBUG      for background information and problems that don't hinder the test.

### Implementation

The script [`images-openstack.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/standard-images/images-openstack.py)
connects to OpenStack and performs the checks described in this section.

## Manual tests

None.
