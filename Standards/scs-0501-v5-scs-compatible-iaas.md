---
title: SCS-compatible IaaS
type: Standard
track: Scopes
status: Stable
stabilized_at: 2024-12-19
replaces:
- scs-0501-v4-scs-compatible-iaas.md
description: |
  The certificate scope for level SCS-compatible and layer IaaS.
---

## Introduction

This is v5.1 of the certificate scope _SCS-compatible IaaS_.

Change log:

- v5.1 adds [scs-0123-v1: Mandatory and Supported IaaS Services](https://docs.scs.community/standards/scs-0123-v1-mandatory-and-supported-IaaS-services), which was intended to be included (as witnessed by the meeting minutes), but was inadvertently omitted.

## Subject Matter

Standards that were already included in v4:

- [scs-0128-v1: SCS end-to-end testing (formerly OpenStack-powered Compute)](https://docs.scs.community/standards/scs-0128-v1-e2e-testing)
- [scs-0100-v3: Flavor naming (v3.1)](https://docs.scs.community/standards/scs-0100-v3-flavor-naming)
- [scs-0101-v1: Entropy](https://docs.scs.community/standards/scs-0102-v1-image-metadata)
- [scs-0102-v1: Image metadata](https://docs.scs.community/standards/scs-0102-v1-image-metadata)
- [scs-0103-v1: Standard flavors](https://docs.scs.community/standards/scs-0103-v1-standard-flavors)

Standards changed with v5:

- [scs-0104-v1: Standard images](https://docs.scs.community/standards/scs-0104-v1-standard-images) with [new spec file](https://raw.githubusercontent.com/SovereignCloudStack/standards/main/Tests/iaas/scs-0104-v1-images-v5.yaml) instead of [former spec file](https://raw.githubusercontent.com/SovereignCloudStack/standards/main/Tests/iaas/scs-0104-v1-images.yaml)

Standards new with v5:

- [scs-0114-v1: Volume Types](https://docs.scs.community/standards/scs-0114-v1-volume-type-standard)
- [scs-0115-v1: Default rules for security groups](https://docs.scs.community/standards/scs-0115-v1-default-rules-for-security-groups)
- [scs-0116-v1: Key manager](https://docs.scs.community/standards/scs-0116-v1-key-manager-standard)
- [scs-0117-v1: Volume backup](https://docs.scs.community/standards/scs-0117-v1-volume-backup-service)
- [scs-0121-v1: Availability Zones](https://docs.scs.community/standards/scs-0121-v1-Availability-Zones-Standard)
- [scs-0123-v1: Mandatory and Supported IaaS Services](https://docs.scs.community/standards/scs-0123-v1-mandatory-and-supported-IaaS-services)
- [scs-0302-v1: Domain Manager Role](https://docs.scs.community/standards/scs-0302-v1-domain-manager-role)

## Testing Regime

The following regulations apply for those certifications where regular testing is required.

In general, automated tests (where applicable) shall be performed at least weekly.

- Tests for scs-0128-v1 may be performed less frequently, but no fewer than once a year.

## Previous Versions

- v5 extends v4 by including new standards as listed above,
  and it changes the spec for scs-0104-v1, updating standard images.
