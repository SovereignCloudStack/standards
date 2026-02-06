---
title: "Volume Backup Functionality: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0117-v1-volume-backup-service.md
---

## Automated tests

We [implemented](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
a single testcase,

- `scs-0117-test-backup`,

which verifies that a non-admin user can backup and restore volumes.

To this end, the testcase uses the `/v3/{project_id}/backups` Block Storage API endpoint to create a volume and a backup of it and subsequently restores the backup on a new volume while verifying the success of each operation.

## Manual tests

Note that the automated tests don't verify the optional part of the standard: providing a separate storage backend for Cinder volume backups.
This cannot be checked from outside of the infrastructure as it is an architectural property of the infrastructure itself and transparent to customers.
