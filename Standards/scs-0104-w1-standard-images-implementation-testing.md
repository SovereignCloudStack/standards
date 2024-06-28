---
title: "SCS Standard Images: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0104-v1-standard-images.md
---

## Implementation notes

The [OpenStack Image Manager from OSISM](https://github.com/osism/openstack-image-manager)
will create a set of images from a "spec file" provided by the user.
The SCS project provides such a [spec file](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/SCS-Spec.Images.yaml) derived from [`scs-0104-v1-images.yaml`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml), which is
defined by the standard to contain the mandatory and recommended images.

## Automated tests

### Images sample

Some checks need to be performed on a live instance. For these checks, the [`scs-0104-v1-images.yaml`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml)
file is used as a default to check the images provided on the IaaS instance
against the expected set of images.

### Implementation

The script [`images-openstack.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/standard-images/images-openstack.py)
connects to OpenStack and performs the checks described in this section.

## Manual tests

None.
