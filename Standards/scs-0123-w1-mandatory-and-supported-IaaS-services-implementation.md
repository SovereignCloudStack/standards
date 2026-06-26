---
title: "Mandatory and Supported IaaS Services: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0123-v1-mandatory-and-supported-IaaS-services.md
  - scs-0123-v2-services.md
---

## Automated tests

We [implemented](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py)
the following testcases in accordance with the standard:

- `scs-0123-service-<type>` ensures that a service with the given type can be found in the service catalog
- `scs-0123-storage-apis` ensures that a service of one of the following types can be found: "volume", "volumev3", "block-storage"

v1 only (soon to be deprecated):

- `scs-0123-swift-s3` ensures that S3 is present on the same host as swift

Note: this testcase is a rather weak surrogate for testing the presence of S3 in general, which is resolved with v2,
where a dedicated entry in the service catalog is mandated.
