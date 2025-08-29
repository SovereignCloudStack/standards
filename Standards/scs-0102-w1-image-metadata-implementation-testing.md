---
title: "SCS Image Metadata: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-0102-v1-image-metadata.md
---


## Implementation notes

The [OpenStack Image Manager from OSISM](https://github.com/osism/openstack-image-manager)
will create a set of images from a "spec file" provided by the user, which can also set the required properties
for these images.

## Automated tests

We implemented a host of testcases to reflect the requirements and recommendations of the standard. The following
testcases ensure that fields have proper values:

- `scs-0102-prop-architecture`,
- `scs-0102-prop-hash_algo`,
- `scs-0102-prop-min_disk`,
- `scs-0102-prop-min_ram`,
- `scs-0102-prop-os_version`,
- `scs-0102-prop-os_distro`,
- `scs-0102-prop-hw_disk_bus`,
- `scs-0102-prop-hypervisor_type`,
- `scs-0102-prop-hw_rng_model`,
- `scs-0102-prop-image_build_date`,
- `scs-0102-prop-image_original_user`,
- `scs-0102-prop-image_source`,
- `scs-0102-prop-image_description`,
- `scs-0102-prop-replace_frequency`,
- `scs-0102-prop-provided_until`,
- `scs-0102-prop-uuid_validity`,
- `scs-0102-prop-hotfix_hours`.

The property `patchlevel` is not tested because it is entirely optional.

The following testcase ensures that each image is as recent as claimed by its `replace_frequency`:

- `scs-0102-image-recency`

The script [`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
can be used to check these testcases.

## Manual tests

None.
