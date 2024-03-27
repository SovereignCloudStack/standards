---
title: "SCS Flavor Naming Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0100-v1-flavor-naming.md
  - scs-0100-v2-flavor-naming.md
  - scs-0100-v3-flavor-naming.md
---

## Introduction

The three major versions of the standard that exist so far are very similar, and deliberately so.
Therefore, the procedures needed to implement or test them are very similar as well. Yet, this document
will only cover v3, because v1 and v2 are already obsolete by the time of writing.

## Implementation Notes

Every flavor whose name starts with `SCS-` must conform with the naming scheme laid down in the standard.

### Operational Tooling

#### Syntax Check

The [test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming)
comes with a handy
[command-line utility](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/cli.py)
that can be used to validate flavor names, to
interactively construct a flavor name via a questionnaire, and to generate prose descriptions for given
flavor names. See the
[README](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/README.md)
for more details.

The functionality of this script is also (partially) exposed via the web page
[https://flavors.scs.community/](https://flavors.scs.community/).

With the OpenStack tooling (`python3-openstackclient`, `OS_CLOUD`) in place, you can call
`cli.py -v parse v3 $(openstack flavor list -f value -c Name)` to get a report
on the syntax compliance of the flavor names of the cloud environment.

#### Flavor Creation

The [OpenStack Flavor Manager](https://github.com/osism/openstack-flavor-manager) will create a whole set
of flavors in one go, given a YAML description of this set.

## Automated Tests

### Errors

The following items MUST be detected and reported as an error:

- any syntax error in a name starting with `SCS-`,
- any mismatch between any immediately discoverable property of a flavor (currently, CPU, RAM and disk size)
  and the meaning of its name (which is usually a lower bound), such as the CPU generation or hypervisor.

In addition, the following items MAY be reported as an error:

- any mismatch between any non-immediately discoverable property of flavor and the meaning of its name.

### Warnings

None so far.

### Implementation

The script [`flavor-names-openstack.py`](https://github.com/SovereignCloudStack/standards/tree/main/Tests/iaas/flavor-naming/flavor-names-openstack.py)
talks to the OpenStack API of the cloud specified by the `OS_CLOUD` environment and queries properties and
checks the names for standards compliance.

## Manual Tests

To be determined.
