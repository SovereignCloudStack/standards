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

The [OpenStack Image Manager from OSISM](https://github.com/osism/openstack-image-manager)
will create a set of images from a "spec file" provided by the user, which can also set the required properties
for these images.

## Automated tests

### Images sample

Some checks need to be performed on a live instance. All publicly available images on this instance
will be checked for either only the mandatory properties or possibly also the recommended ones.
Additionally, a user can also decide to test their private images, although this isn't a necessity.

### Implementation

The script [`image-md-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/image-metadata/image-md-check.py)
connects to OpenStack and performs the checks described in this section.

## Manual tests

None.
