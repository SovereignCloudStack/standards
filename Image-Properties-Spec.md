---
title: SCS Image Metadata Proposal
version: 2021-06-14-001
authors: Kurt Garloff, Christian Berendt
state: Draft
---

SCS Image Metadata Proposal (DRAFT) SCS

Please take note, that this is a DRAFT open for discussion (2021-06-14)

# Motivation

Many clouds offer standard Operating System images for their users' convenience.
To make them really useful, they should contain meta data (properties) to allow
users to understand what they can expect using these images.

The specification is targeting images that are managed by the service provider,
provided for public consumption. The spec or parts of it however might turn out
to be useful whenever someone manages images for somebody else's consumption.

We also suggest a standard set of images to be available.

# Overview

We categorize the image properties into a few buckets

* Technical requirements and features
* Image handling aspects
* Licensing/Maintenance/Support aspects

# Naming

We suggest plain OS images to be named "Distribution Version",
e.g. "openSUSE Leap 15.3" or "Ubuntu 20.04" or "CentOS 8.4", "Windows Server 2012R2".
We do not normally recommend to add more detailed patch levels into the name.

Special variants that include specific non-standard features should be named
"Distribution Version Feature1 Feature2".

There are several policies possible to provide updated images to include the latest
bug- and security fixes. This is outlined in update policy description below.

# Technical requirements and features

This is dependent on whether we deal with VM images or container images.

For VM images (OpenStack), we recommend to use the properties as described
in the [OpenStack Image documentation](https://docs.openstack.org/glance/latest//admin/useful-image-properties).

The following properties are considered mandatory:
* `architecture`, `hypervisor_type`
* `min_disk_size`, `min_ram`
* `os_version`, `os_distro`
* `hw_rng_model`, `hw_disk_bus` (`scsi` recommended, and then setting `hw_scsi_model` is also recommended)

The following properties are recommended (if the features are supported):
* `os_secure_boot`, `hw_firmware_type`
* `hw_watchdog_action`, `hw_mem_encryption`, `hw_pmu`, `hw_video_ram`, `hw_vif_multiqueue_enabled`

The `trait:XXX=required` property can be used to indicate that certain virtual hardware
features `XXX` are required.

# Image handling

## Image updating 

It is recommended that provider managed images are regularly updated.
This means that users referencing an image *by name* will always get the latest image for the
operating system indicated by that name (which includes a version number, but not the patch
level).

Technically, the thus updated image is a new image and will thus carry a new UUID.
It is recommended that the old image gets renamed (e.g. build date or patch level attached)
and hidden, but remains accessible via its (unchanged) UUID. 

The update handling by the provider is described via the properties `replace_frequency` and
`uuid_validity`, `provided_till`.

The `replace_frequency` and `provided_till` fields reference to the image name.

| replace_frequency | meaning              |
|-------------------|----------------------|
| yearly            | the image will get replaced *at least* once per year    |
| quarterly         | the image will get replaced *at least* once per quarter |
| monthly           | the image will get replaced *at least* once per month   |
| weekly            | the image will get replaced *at least* once per week    |
| daily             | the image will get replaced *at least* once per day     |
| critical_bug      | the image will get replaced for critical issues only    |
| never             | the image referenced by name will never change (until the date `provided_till`) |

Note the *at least* wording: Providers are expected to replace images upon critical security issues
out of order, except when indicating `never`.

The `provided_till` field is supposed to contain a date in `YYYY-MM-DD` format that
indicates until when an image under this name will be provided and (according to the
`replace_frequency`) updated at least. (Providers are free to provide updates for
longer or leave the non-updated image visible for longer.)
If this field is not set, no promises are made.

The `uuid_validity` field indicates how long the public image will be referencable
by it's UUID.

| uuid_validity  | meaning                |
|----------------|------------------------|
| none           | UUID will only be valid as long as the content does not change          |
| last-N         | The last N images for newer replacement will remain accessible via UUID |
| YYYY-MM-DD     | UUID will be valid until at least the date YYYY-MM-DD                   |
| notice         | UUID will remain valid until a deprecation notice will be published     |
| forever        | UUID will remain valid for as long as the cloud operates                |

Note that the old images must be hidden from the image catalogue or renamed (or both)
to avoid failing referencing by name. Note that `last-N` may be limited by the `provided_till`
date.

All dates are in UTC.

### Example:
Providing an image with name `OPSYS MAJ.MIN` with
`replace_frequency`=`monthly`, `provided_till`=`2022-09-30`, `uuid_validity`=`2022-12-31`
means that we will have a new image with this name at least once per month until the end
of September 2022. Old images will be hidden or renamed, but remain accessible via their
UUID until at least the end of 2022 (in Universal Time).

## Image Origin

* Mandatory: `image_source` needs to be a URL to point to a place from which the image can be downloaded.
  (Note: This may be set to the string "private" to indicate that the image can not be freely
   downloaded.)
* Mandatory: `image_description` needs to be a URL with release notes and other human readable data
  about the image.

* Recommended tag: `managed_by_VENDOR`

## Image build info

* Mandatory: `image_build_date` needs to be `YYYY-MM-DD` or `YYYY-MM-DD hh:mm:ss` (time in UTC).
  It is recommended that all publicly released patches before this date are included in the
  image build. If the cutoff date is earlier, this cutoff date need to be set instead, even
  if the build happens significantly after the cutoff date.
* Mandatory: `image_original_user` is the default login user for the operating system which can connect
  to the image via the injected SSH key or provided password. (This can be set to `none` if no default
  user name exists for the operating system.)
* Optional: `patchlevel` can be set to an operating specific patch level that describes the
  patch status -- typically we would expect the `image_build_date` to be sufficient.

* Optional: `image_sha256`: The sha256sum (as hex in ascii) for the image file. 
  (We recommend referencing the raw files, not .qcow2 or similar formats.)
* Optional: `image_sig`: The (ASCII armored) digital signature for the image file.

* Recommended tag: `os:OPERATINGSYSTEM`


## Licensing / Maintenance / Support 

TBW
