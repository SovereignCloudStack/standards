---
title: Volume Backup Functionality
type: Standard
status: Proposal
track: IaaS
---

## Introduction

OpenStack offers a variety of resources where users are able to transfer and store data in the infrastructure.
A prime example of these resources are volumes which are attached to virtual machines as virtual block storage devices.
As such they carry potentially large amounts of user data which is constantly changing at runtime.
It is important for users to have the ability to create backups of this data in a reliable and effifcient manner.

## Motivation

The [volume backup functionality of OpenStack](https://docs.openstack.org/cinder/latest/admin/volume-backups.html) is a feature that is not available in all OpenStack clouds per default.
The feature requires a backend to be prepared and configured correctly before it can be used.
In Cinder this is a separate configuration to the general storage backend of the volume service and is not mandatory.
Thus, an arbitrary OpenStack cloud may or may not offer this feature.

This standard aims to make this functionality the default in SCS clouds so that customers can expect the feature to be usable.

## Design Considerations

The standard should make sure that the feature is available and usable but should not limit the exact implementation (e.g. choice of backend driver) any further than necessary.

### Options considered

#### Only recommend volume backup feature, use images as alternative

As an alternative to the volume backup feature of the Block Storage API, Glance images can also be created based on volumes and act as a backup under certain circumstances.
As an option, this standard could keep the actual integration of the volume backup feature optional and guide users how to use images as backup targets instead in case the feature is unavailable.

However, it is not guaranteed that the Glance backend storage is separate from the volume storage.
For instance, both could be using the same Ceph cluster.
In such case, the images would not count as genuine backups.

Although users are able to download images and transfer them to a different storage location, this approach might also prove unfeasible depending on the image size and the existence (or lack) of appropriate target storage on the user side.

Furthermore, incremental backups are not possible when creating Glance images from volumes either.
This results in time-consuming backup operations of fully copying a volume everytime a backup is created.

#### Mandate the availability of the volume backup feature

This option is pretty straightforward.
It would make the volume backup feature mandatory for SCS clouds.
This way users can expect the feature to be available and usable.

With this, users can leverage functionalities like incremental backups and benefit from optimized performance of the backup process due to the tight integration with the volume service.

## Decision

This standard decides to go with the second option and makes the volume backup feature mandatory in the following way:

In an SCS cloud, the volume backup functionality MUST be configured properly and its API as defined per `/v3/{project_id}/backups` MUST be offered to customers.
If using Cinder, a suitable [backup driver](https://docs.openstack.org/cinder/latest/configuration/block-storage/backup-drivers.html) MUST be set up.

The volume backup target storage SHOULD be a separate storage system from the one used for volumes themselves.

## Related Documents

- [OpenStack Block Storage v3 Backup API reference](https://docs.openstack.org/api-ref/block-storage/v3/index.html#backups-backups)

## Conformance Tests

Conformance tests include using the `/v3/{project_id}/backups` Block Storage API endpoint to create a volume and a backup of it as a non-admin user and subsequently restore the backup on a new volume while verifying the success of each operation.

There is a test suite in [`volume-backup-tester.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/volume-backup/volume-backup-tester.py).
The test suite connects to the OpenStack API and executes basic operations using the volume backup API to verify that the functionality requested by the standard is available.
Please consult the associated [README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/volume-backup/README.md) for detailed setup and testing instructions.
