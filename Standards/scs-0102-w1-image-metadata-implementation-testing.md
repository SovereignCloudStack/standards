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

- `scs_0102_prop_architecture`,
- `scs_0102_prop_hash_algo`,
- `scs_0102_prop_min_disk`,
- `scs_0102_prop_min_ram`,
- `scs_0102_prop_os_version`,
- `scs_0102_prop_os_distro`,
- `scs_0102_prop_hw_disk_bus`,
- `scs_0102_prop_hypervisor_type`,
- `scs_0102_prop_hw_rng_model`,
- `scs_0102_prop_image_build_date`,
- `scs_0102_prop_image_original_user`,
- `scs_0102_prop_image_source`,
- `scs_0102_prop_image_description`,
- `scs_0102_prop_replace_frequency`,
- `scs_0102_prop_provided_until`,
- `scs_0102_prop_uuid_validity`,
- `scs_0102_prop_hotfix_hours`.

The property `patchlevel` is not tested because it is entirely optional.

The following testcase ensures that each image is as recent as claimed by its `replace_frequency`:

- `scs_0102_image_recency`

The script [`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
can be used to check these testcases.

## Manual tests

None.
