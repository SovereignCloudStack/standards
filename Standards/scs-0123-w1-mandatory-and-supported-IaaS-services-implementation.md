---
title: "Mandatory and Supported IaaS Services: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0123-v1-mandatory-and-supported-IaaS-services.md
---

## Automated tests

We [implemented](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
the following testcases in accordance with the standard:

- `scs-0123-service-X` (with varying `X`) ensures that a service of type X can be found in the service catalog,
- `scs-0123-storage-apis` ensures that a service of one of the following types can be found: "volume", "volumev3", "block-storage",
- `scs-0123-swift-s3` ensures that S3 can be used to access object storage using EC2 credentials from the identity API.
