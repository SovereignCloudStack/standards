# What is required to make Yaook SCS-compliant?

This document is a TLDR for the [SCS compliance document](scs-compliance.md).

## OpenStack

The following things are required for SCS compliance of OpenStack:

### General

### Entropy

Entropy according to the ["SCS Entropy" Standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0101-v1-entropy.md
may be provided a few different ways, in order to ensure availability for cryptographic operations.

#### Flavors

The following attributes are recommended for OpenStack flavors.

| Attribute           | Status      | Unit / Value |
|---------------------|-------------|--------------|
| hw_rng:allowed      | Recommended | True         |
| hw_rng:rate_bytes   | Optional    | Bytes        |
| hw_rng:rate_period  | Optional    | Seconds      |
| hw_rng_model:virtio | Recommended |              |

#### Hardware

Compute nodes must use CPUs that offer instructions for accessing
entropy (such as `RDSEED` or `RDRAND` on x86_64 or `RNDR` on arm64), and
these instructions may not be filtered by the hypervisor.
They may also provide HRNG via `rngd`.

This can be verified inside virtual instances with:
1. `/proc/sys/kernel/random/entropy_avail` provides at least value `256` (pinned since Linux kernel 5.18)
2. FIPS 140-2 failures must not exceed 3 out of 1000 blocks tested, as determined by `cat /dev/random | rngtest -c 1000` .


### Flavors

All flavors MUST be named with the following schema, if they start with `SCS-`:

| Prefix | CPUs & Suffix     | RAM[GiB]           | optional: Disk[GB]&type       | opt: extensions |
|--------|-------------------|--------------------|-------------------------------|-----------------|
| `SCS-` | N`L/V/T/C`\[`i`\] | `-`N\[`u`\]\[`o`\] | \[`-`\[M`x`\]N\[`n/h/s/p`\]\] | \[`_`EXT\]      |

More details about this can be found in the ["SCS Flavor Naming Standard"](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0100-v3-flavor-naming.md) or the [long version](scs-compliance.md)
of this document. Special attention is required for the optional extension part, which doesn't need
to be used.

In order to further indicate an `SCS` flavor, `extra_specs` MUST be set for the flavors, as described in the
["SCS Standard Flavors and Properties" Standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0103-v1-standard-flavors.md).

| Name           | Value                                                                        |
|----------------|------------------------------------------------------------------------------|
| scs:name-v1    | recommended name, but with each dash AFTER the first one replaced by a colon |
| scs:name-v2    | recommended name                                                             |
| scs:cpu-type   | `shared-core` or `crowded-core`                                              |
| scs:disk0-type | not set or some disk type (e.g. `ssd`                                        |

Additionally, there are a number of mandatory and recommended (optional) flavors that need to be available
according to ["SCS standard flavors and properties" standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0103-v1-standard-flavors.md).

#### Mandatory

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type         |
|------------------|-------|--------------|-----------|----------------|-------------------|
| SCS-1V-4         | 1     | shared-core  | 4         |                |                   |
| SCS-2V-8         | 2     | shared-core  | 8         |                |                   |
| SCS-4V-16        | 4     | shared-core  | 16        |                |                   |
| SCS-4V-16-100s   | 4     | shared-core  | 16        | 100            | Local SSD or NVME |
| SCS-8V-32        | 8     | shared-core  | 32        |                |                   |
| SCS-1V-2         | 1     | shared-core  | 2         |                |                   |
| SCS-2V-4         | 2     | shared-core  | 4         |                |                   |
| SCS-2V-4-20s     | 2     | shared-core  | 4         | 20             | Local SSD or NVME |
| SCS-4V-8         | 4     | shared-core  | 8         |                |                   |
| SCS-8V-16        | 8     | shared-core  | 16        |                |                   |
| SCS-16V-32       | 16    | shared-core  | 32        |                |                   |
| SCS-1V-8         | 1     | shared-core  | 8         |                |                   |
| SCS-2V-16        | 2     | shared-core  | 16        |                |                   |
| SCS-4V-32        | 4     | shared-core  | 32        |                |                   |
| SCS-1L-1         | 1     | crowded-core | 1         |                |                   |

Additionally, the following flavors are required by the ["SSD Flavors" standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0110-v1-ssd-flavors.md);
these are already listed in the table above and only here for reference.

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type         |
|------------------|-------|--------------|-----------|----------------|-------------------|
| SCS-2V-4-20s     | 2     | shared-core  | 4         | 20             | Local SSD or NVME |
| SCS-4V-16-100s   | 4     | shared-core  | 16        | 100            | Local SSD or NVME |

#### Recommended

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type |
|------------------|-------|--------------|-----------|----------------|-----------|
| SCS-1V-4-10      | 1     | shared-core  | 4         | 10             | (any)     |
| SCS-2V-8-20      | 2     | shared-core  | 8         | 20             | (any)     |
| SCS-4V-16-50     | 4     | shared-core  | 16        | 50             | (any)     |
| SCS-8V-32-100    | 8     | shared-core  | 32        | 100            | (any)     |
| SCS-1V-2-5       | 1     | shared-core  | 2         | 5              | (any)     |
| SCS-2V-4-10      | 2     | shared-core  | 4         | 10             | (any)     |
| SCS-4V-8-20      | 4     | shared-core  | 8         | 20             | (any)     |
| SCS-8V-16-50     | 8     | shared-core  | 16        | 50             | (any)     |
| SCS-16V-32-100   | 16    | shared-core  | 32        | 100            | (any)     |
| SCS-1V-8-20      | 1     | shared-core  | 8         | 20             | (any)     |
| SCS-2V-16-50     | 2     | shared-core  | 16        | 50             | (any)     |
| SCS-4V-32-100    | 4     | shared-core  | 32        | 100            | (any)     |
| SCS-1L-1-5       | 1     | crowded-core | 1         | 5              | (any)     |

### Images

All images SHOULD be named with plain OS image names similar to "Distribution Version"; special variants
can add non-standard features to this schema with e.g. "Distribution Version Feature1 Feature2".

It is also important and partially mandatory to set image properties, which are listed in the following table.
More information about these image properties can be found in the [OpenStack Glance Documentation](https://docs.openstack.org/glance/latest/admin/useful-image-properties.html).

| Property name             | status      | Description                                           | Values / Unit                                                 |
|---------------------------|-------------|-------------------------------------------------------|---------------------------------------------------------------|
| architecture              | Mandatory   |                                                       |                                                               |
| hypervisor_type           | Mandatory   |                                                       |                                                               |
| min_disk_size             | Mandatory   | Minimum disk size                                     | GiB                                                           |
| min_ram                   | Mandatory   | Minimum RAM size                                      | MiB                                                           |
| os_version                | Mandatory   | OS version                                            |                                                               |
| os_distro                 | Mandatory   | Distro name                                           |                                                               |
| hw_rng_model              | Mandatory   | Add rng device to image instance                      | virtio, ..                                                    |
| hw_disk_bus               | Mandatory   |                                                       | scsi, hw_scsi_model, ...                                      |
| os_secure_boot            | Recommended | Is Secure Boot active?                                |                                                               |
| hw_firmware_type          | Recommended |                                                       | bios, uefi                                                    |
| hw_watchdog_action        | Recommended | Hardware watchdog action on server hang               | disabled, reset, poweroff, pause, none                        |
| hw_mem_encryption         | Recommended | Encryption of guest memory on HW level                | bool                                                          |
| hw_pmu                    | Recommended | Emulation of vPMU (performance monitoring unit)       | bool                                                          |
| hw_video_ram              | Recommended | maximum RAM for video image                           | int (MB)                                                      |
| hw_vif_multiqueue_enabled | Recommended | Equals queues with guest vCPUs                        | bool                                                          |
| replace_frequency         | Mandatory   | How often image must at least be replaced             | yearly, quaterly, monthly, weekly, daily, critical bug, never |
| provided_until            | Mandatory   | How long image with this name will be provided        | YYYY-MM-DD                                                    |
| hotfix_hours              | Optional    | Time until critical security issues are dealt with    | Hours                                                         |
| uuid_validity             | Mandatory   | Time this image will be referencable with this UUID   | none, last-N, YYYY-MM-DD, notice, forever                     |
| image_source              | Mandatory   | URL to download the image                             | URL                                                           |
| image_description         | Mandatory   | URL with release notes or human-readable data         | URL or text                                                   |
| image_build_date          | Mandatory   |                                                       | YYYY-MM-DD [hh:mm[:ss]]                                       |
| image_original_user       | Mandatory   | Default login user for the OS                         |                                                               |
| patchlevel                | Optional    |                                                       |                                                               |
| os_hash_algo              | Recommended | SHA256 or SHA512                                      |                                                               |
| os_hash_value             | Recommended | Value of the SHAXXX for the image                     |                                                               |
| license_included          | Optional    | Is license include in the flavor fee?                 | boolean                                                       |
| license_required          | Optional    | Does customer need to bring his own license?          | boolean                                                       |
| subscription_included     | Optional    | Does the image contain a maintenance subscription?    | boolean                                                       |
| subscription_required     | Optional    | Does the customer require a maintenance subscription? | boolean                                                       |
| maintained_until          | Optional    | Date of maintenance                                   | YYYY-MM-DD                                                    |
| l1_support_contact        | Optional    | Customer support contact                              | URI                                                           |

There are also a number of mandatory images that need to be available according to ["SCS Standard Images" standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0104-v1-standard-images.md), 
which need to be provided/retrieved from specified sources to be compliant.
The list of this can be found in the ["scs-0104-v1-images.yaml" file](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml)

| Name              | Name scheme                               | status      | Source 1                                                                                                                           | Source 2                                           |
|-------------------|-------------------------------------------|-------------|------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| Ubuntu 22.04      | -                                         | Mandatory   | https://cloud-images.ubuntu.com/releases/jammy/                                                                                    | https://cloud-images.ubuntu.com/jammy/             |
| ubuntu-capi-image | ubuntu-capi-image-v[0-9].[0-9]+(.[0-9]+)? | Recommended | https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube |                                                    |
| Ubuntu 20.04      | -                                         | -           | https://cloud-images.ubuntu.com/releases/focal/                                                                                    | https://cloud-images.ubuntu.com/focal/             |
| Debian 12         | -                                         | -           | https://cloud.debian.org/images/cloud/bookworm/                                                                                    | https://cdimage.debian.org/cdimage/cloud/bookworm/ |
| Debian 11         | -                                         | -           | https://cloud.debian.org/images/cloud/bullseye/                                                                                    | https://cdimage.debian.org/cdimage/cloud/bullseye/ |
| Debian 10         | -                                         | -           | https://cloud.debian.org/images/cloud/buster/                                                                                      | https://cdimage.debian.org/cdimage/cloud/buster/   |

