---
title: SCS Image Metadata
type: Standard
stabilized_at: 2022-10-31
status: Stable
track: IaaS
replaces: Image-Metadata-Spec.md
description: |
  This is version 1.1 of the SCS-0102 Image Metadata Standard.
  It outlines how to categorize and manage metadata for cloud-based operating
  system images to ensure usability and clarity. The standard encompasses naming conventions, technical requirements,
  image handling protocols including updating and origin, and licensing/support details. These guidelines ensure
  that users can understand, access, and utilize OS images effectively, with clear information on features, updates,
  and licensing provided through well-defined metadata properties.
---

## Motivation

Many clouds offer standard Operating System images for their users' convenience.
To make them really useful, they should contain metadata (properties) to allow
users to understand what they can expect using these images.

The specification is targeting images that are managed by the service provider,
provided for public consumption. The spec or parts of it however might turn out
to be useful whenever someone manages images for somebody else's consumption.

## Overview

We categorize the image properties into a few buckets

- Technical requirements and features
- Image handling aspects
- Licensing/Maintenance/Support aspects

## Naming

We suggest plain OS images to be named "Distribution Version",
e.g. "openSUSE Leap 15.3" or "Ubuntu 20.04" or "CentOS 8", "Windows Server 2012R2".
We do not normally recommend to add more detailed patch levels into the name.

Special variants that include specific non-standard features should be named
"Distribution Version Feature1 Feature2".

There are several policies possible to provide updated images to include the latest
bug- and security fixes. This is outlined in update policy description below.

## Technical requirements and features

This is dependent on whether we deal with VM images or container images.

For VM images (OpenStack), we recommend to use the properties as described
in the [OpenStack Image documentation](https://docs.openstack.org/glance/latest//admin/useful-image-properties).

The following properties are considered mandatory:

- `architecture`
- `min_disk` (in GiB), `min_ram` (in MiB)
- `os_version`, `os_distro`
- `hw_disk_bus` (`scsi` recommended, and then setting `hw_scsi_model` is also recommended)

**Note**: Disk sizes tend to be measured in GB = 10^9 and not GiB = 2^30 in the disk industry, but OpenStack uses GiB.

The value given vor `min_ram` MUST be sufficient for the VM to boot and survive (for at least 10 s).

The following property is recommended:

- `hypervisor_type`

The values for `architecture` and `os_distro` and `hypervisor_type` (the latter only if specified) values
must follow the [OpenStack specifications](https://docs.openstack.org/glance/2025.1/admin/useful-image-properties.html).
The `os_version` string should be numeric if the distribution uses numbers, the pair `os_distro` `os_version` should
for example be `ubuntu` `24.04` for Ubuntu Noble Numbat 24.04[.x] LTS.

To allow the distinction between general purpose images (which should come from upstream with at most some
targeted adjustments as required by the cloud such as e.g. drviers) and images that are purpose-built, we
recommend an additional field:

- `os_purpose`

The following values are allowed

| `os_purpose` value | Intention                                                 |
|--------------------|-----------------------------------------------------------|
| `generic`          | A general purpose image, (mostly) vanilla from upstream   |
| `minimal`          | A much more barebones general purpose image               |
| `capinode`         | Node image built for cluster-API                          |
| `gpu`              | Image with GPU drivers e.g. for HPC or AI                 |
| `network`          | Image for a network appliance (router, loadbalancer, ...) |
| `appliance`        | Other appliances (single-purpose solutions)               |
| `custom`           | None of the above                                         |

Note that no other values are currently allowed and `custom` (or `appliance`) should be used in case
of doubt. Talk to the SCS standardization bodies if you'd like to see this list extended which is
likely the case if you fall back to `custom`.

The usage of standardized `os_distro`, `os_version` and `os_purpose` help cloud users to create
automation that works across clouds without requiring image names to be standardized. Only
one visible public image with `os_purpose` = `generic` and the same settings for `os_distro`
and `os_version` should be active on any given cloud.
The link to the OpenStack specs and the recommended `os_purpose` was added in 7/2025 to this
standard; a new version of the standard that requires `os_purpose` will be created later.

The following further properties are recommended (if the features are supported):

- `hw_rng_model`
- `os_secure_boot`, `hw_firmware_type`
- `hw_watchdog_action`, `hw_mem_encryption`, `hw_pmu`, `hw_video_ram`, `hw_vif_multiqueue_enabled`

The `trait:XXX=required` property can be used to indicate that certain virtual hardware
features `XXX` are required which may be advertised in matching
[flavor extra specs](https://docs.openstack.org/nova/latest/user/flavors.html#extra-specs).

## Image handling

### Image updating

It is recommended that provider managed images are regularly updated.
This means that users referencing an image _by name_ will always get the latest image for the
operating system indicated by that name (which includes a version number, but not the patch
level).

Technically, the thus updated image is a new image and will thus carry a new UUID.
It is recommended that the old image gets renamed (e.g. build date or patch level attached)
and hidden (`os_hidden=True`), but remains accessible via its (unchanged) UUID for some
time.

The update handling by the provider is described via the properties `replace_frequency`,
`uuid_validity`, `provided_until`, and `hotfix_hours`.

The `replace_frequency`, `provided_until`, and `hotfix_hours` fields reference to the image
as referenced by its name.

| `replace_frequency` | meaning                                                                          |
| ------------------- | -------------------------------------------------------------------------------- |
| `yearly`            | the image will get replaced _at least_ once per year                             |
| `quarterly`         | the image will get replaced _at least_ once per quarter                          |
| `monthly`           | the image will get replaced _at least_ once per month                            |
| `weekly`            | the image will get replaced _at least_ once per week                             |
| `daily`             | the image will get replaced _at least_ once per day                              |
| `critical_bug`      | the image will get replaced for critical issues only                             |
| `never`             | the image referenced by name will never change (until the date `provided_until`) |

Note the _at least_ wording: Providers can replace images more often.
The frequency is starting from the first release; so an image published on 2021-04-14 with an
update frequency of `monthly`, should be replaced no later than 2021-05-14. Due to weekends
etc., up to 3 days later is not considered a violation of this policy. So a valid sequence
from an image with `monthly` update frequency might be 2021-04-14, 2021-05-14, 2021-06-15,
2021-07-14, 2021-07-27 (hotfix), 2021-08-13 ...

Promises to update the registered public images typically depend on upstream image providers
(Linux distributors, OS vendors) keeping their promises to build and provide updated images.
Failures from upstream are not a reason to claim the cloud provider to be in violation of his
promises. However, if the provider observes massive upstream failures (which can e.g. cause
increased security risks), we advise the provider to inform the users.

We recommend updating images at least monthly.

The `hotfix_hours` field indicates how providers deal with critical security issues
that affect the images; it is an optional field that contains a numerical value, indicating
how quickly (in hours) a new image is provided _after the latter of the points in time that
the issue becomes public and a tested fix is available as maintenance update from the upstream
distribution_. A value of 0 indicates a best-effort approach without firm SLAs; the field not
being present indicates no commitment. A value of 48 would indicate that the provider
commits to a new image within 48hrs. A critical issue is defined as a security vulnerability
with a CVSS score of 9.0 or higher that affects software that is included in the image.

The `provided_until` field is supposed to contain a date in `YYYY-MM-DD` format that
indicates until when an image under this name will be provided and (according to the
`replace_frequency`) updated at least. (Providers are free to provide updates for
longer or leave the non-updated image visible for longer.)
If this field is set to `none`, no promises are made, if it is set to `notice`, updates
will be provided until a deprecation notice is published. (The values are the same as
for below `uuid_validity`, except that `forever` and `last-N` don't make any sense.)

The `uuid_validity` field indicates how long the public image will be referencable
by its UUID.

| `uuid_validity` | meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| `none`          | UUID will only be valid as long as the content does not change          |
| `last-N`        | The last N images for newer replacement will remain accessible via UUID |
| `YYYY-MM-DD`    | UUID will be valid until at least the date YYYY-MM-DD                   |
| `notice`        | UUID will remain valid until a deprecation notice will be published     |
| `forever`       | UUID will remain valid for as long as the cloud operates                |

Note that the old images must be hidden from the image catalogue or renamed (or both)
to avoid failing referencing by name. Note that `last-N` may be limited by the `provided_until`
date. We recommend providers that keep old images according to the advertized `uuid_validity`
to hide older images (setting the `os_hidden` property to `True`). If the outdated images must
remain visible, the recommendation is to rename the images by attaching a datestamp in the
format " `YYYYMMDD`" to the name where the date must reflect the `build_date` of the image.

The three properties `uuid_validity`, `provided_until` and `replace_frequency` are mandatory;
the field `hotfix_hours` is optional.

All dates are in UTC.

#### Example

Providing an image with name `OPSYS MAJ.MIN` with
`replace_frequency=monthly`, `provided_until=2022-09-30`, `uuid_validity=2022-12-31`,
`hotfix_hours=0`
means that we will have a new image with this name at least once per month (starting from
the initial release) until the end of September 2022. Old images will be hidden and/or
renamed, but remain accessible via their UUID until at least the end of 2022 (in Universal Time).
The provider makes an effort to replace images upon critical security issues out of order.

### Image Origin

- Mandatory: `image_source` needs to be a URL to point to a place from which the image can be downloaded.
  (Note: This may be set to the string "private" to indicate that the image can not be freely
  downloaded.)
- Mandatory: `image_description` needs to be a URL (or text) with release notes and other human-readable
  data about the image.

- Recommended _tag_: `managed_by_VENDOR`

Note that for most images that come straight from an upstream source, `image_description` should point
to an upstream web page where these images are described. If download links are available as well
on that page, `image_source` can point to the same page, otherwise a more direct link to the image
should be used, e.g. directly linking the `.qcow2` or `.img` file.
If providers have their own image building machinery or do some post-processing on top of
upstream images, they should point to the place where they document and offer these images.

### Image build info

- Mandatory: `image_build_date` needs to be `YYYY-MM-DD` or `YYYY-MM-DD hh:mm[:ss]` (time in UTC,
  24hrs clock).
  All publicly released and generally recommended patches before this date must be included in the
  image build. If the cutoff date is earlier, this cutoff date needs to be set instead, even
  if the actual build happens significantly after the cutoff date. If not all patches can be
  included for a good reason, then the `patchlevel` field (see below) must be used to describe
  the patch status.
- Mandatory: `image_original_user` is the default login user for the operating system which can connect
  to the image via the injected SSH key or provided password. (This can be set to `none` if no default
  username exists for the operating system.)
- Optional: `patchlevel` can be set to an operating specific patch level that describes the
  patch status — typically we would expect the `image_build_date` to be sufficient.

- Recommended: `os_hash_algo` and `os_hash_value`: The sha256 or sha512 hash
  for the image file. (This references the image file in the format it is stored in, we
  recommend raw over qcow2 for systems that use ceph.) Note that these values are
  typically generated automatically upon image registration.

- Recommended _tag_: `os:OPERATINGSYSTEM`

### Licensing / Maintenance subscription / Support

Some images require a license; in many cases the cloud providers include the license cost
by a per-use (e.g. hourly) fee. However, it is also possible sometimes that customers
use their own license agreements with the OS vendor with a bring-your-own-license (BYOL)
program. These properties may be attached to the image. Note that free Linux images
might not use any of these properties, except maybe `maintained_until`. Note that
Windows images would typically require `license_included`, `subscription_included`.
A boolean property that is not present is considered to be `false`.

- Optional: `license_included` (boolean) indicates whether the flavor fee
  includes the licenses required to use this image. This field is mandatory for
  images that contain software that requires commercial licenses.
- Optional: `license_required` (boolean) indicates whether a customer must bring
  its own license to be license compliant. This can not be true at the same time as the
  previous setting. This field is mandatory IF customers need to bring their own
  license to use the image.
- Optional: `subscription_included` (boolean) indicates that the image contains already
  a maintenance subscription which typically gives access to bug fixes, security
  fixes and (minor) function updates. If a subscription is included, the CSP should
  have prepared the image to also receive the provided maintenance updates from the
  vendor (optionally via a mirror).
- Optional: `subscription_required` (boolean) indicates that the customer requires
  a maintenance subscription from the OS vendor in order to receive fixes
  (which is often also a prerequisite to be eligible for support).
- Optional: `maintained_until: YYYY-MM-DD` promises maintenance from the OS vendor
  until at least this date (in UTC).
- Optional: `l1_support_contact` contains a URI that provides customer support
  contact for issues with this image. Note that this field must only be set if the
  service provider does provide support for this image included in the image/flavor
  pricing (but it might be provided by a contracted 3rd party, e.g. the OS vendor).

### Version history

* Version 1.0 has existed without notable changes since June 2021.
* Version 1.1 was created in preparation for a new major version 2.0 and has the following additional recommendations:
    - Reference OpenStack image spec for standard values of `os_distro`, `architecture` and `hypervisor_type`.
    - Recommendation on `os_version` to be a version number (if such a value exists).
    - Recommended field `os_purpose`.
