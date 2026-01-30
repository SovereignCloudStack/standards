---
title: "SCS Standard Flavors: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0103-v1-standard-flavors.md
---

## Operational tooling

The [openstack-flavor-manager](https://github.com/osism/openstack-flavor-manager) is able to
create all standard, mandatory as well as recommended SCS flavors for you. It now has a `--limit-memory`
(defaulting to 32 GiB) to skip the creation of recommended flavors above this memory limit.

You can generate input for it using the tool
[`flavor-manager-input.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs_0100_flavor_naming/flavor-manager-input.py).

## Automated tests

We [implemented](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
a set of testcases corresponding 1:1 to the standard flavors:

- `scs-0103-flavor-X` with varying `X`: ensures that flavor `SCS-X` is present and has the
  required `extra_specs`.

_NOTE_: We still need to add testcases to ensure that the `extra_specs` of non-standard
flavors are correct as well.
