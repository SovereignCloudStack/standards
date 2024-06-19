---
title: "SCS Image Metadata: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0102-v1-image-metadata.md
---

## Introduction

The standard defines a set of metadata properties for public images, that need to be set in order
to have an SCS-compliant IaaS setup.

## Implementation notes

The [OpenStack Image Manager from osism](https://github.com/osism/openstack-image-manager)
will create a set of images from a file provided by the user, which can also set the required properties
for these images. Additional images with their respective properties besides the images mandatory
through the ["SCS Standard Images Standard (scs-0104-v1-standard-images)"](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0104-v1-standard-images.md) can also be defined
this way.

The SCS project provides a [file](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/SCS-Spec.Images.yaml) derived from the [`scs-0104-v1-images.yaml`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml) with the necessary
properties.
This process also enables the easy adoption of the
["SCS Standard Images Standard (scs-0104-v1-standard-images)"](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0104-v1-standard-images.md).

## Automated tests

### Images sample

Some checks need to be performed on a live instance. All publicly available images on this instance
will be checked for either only the mandatory properties or possibly also the recommended ones.
Additionally, a user can also decide to test their private images, although this isn't a necessity.

### Errors and warnings

The test provides increases its return value for every error found during execution.
Additionally, logs are provided to output further information:

- Error   for invalid property values or missing properties
- Warning for missing images or not recommended values
- Info    for violations of recommendations

### Implementation

The script [`image-md-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/image-metadata/image-md-check.py)
connects to OpenStack and performs the checks described in this section.

## Manual tests

None.
