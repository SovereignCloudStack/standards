---
title: "SCS Volume Types: Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0114-v1-volume-type-standard.md
---

## Automated tests

We implemented the following testcases:

- `scs-0114-syntax-check` ensures that, for every volume type description,
  the list of aspects, if present, is formatted according to the standard.
- `scs-0114-encrypted-type` ensures that a volume type featuring encryption is present.
- `scs-0114-replicated-type` ensures that a volume type featuring replication is present.

The testcases can be run using the script
[`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py).
