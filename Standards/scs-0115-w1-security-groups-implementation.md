---
title: "Default Rules for Security Groups: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-0115-v1-default-rules-for-security-groups.md
---

## Automated tests

We implemented a single test case,

- `scs-0115-default-rules`,

which ensures

1. the absence of any ingress traffic rules except traffic from the same Security Group in the `openstack default security group rule list`,
2. the presence of any egress traffic rules.

The testcase can be run using the script
[`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py).
