---
title: SCS-compatible IaaS
type: Standard
track: Scopes
status: Deprecated
stabilized_at: 2024-02-28
deprecated_at: 2025-07-01
replaces:
- scs-0501-v3-scs-compatible-iaas.md
description: |
  The certificate scope for level SCS-compatible and layer IaaS.
---

## Introduction

This is v4 of the certificate scope _SCS-compatible IaaS_.

## Subject Matter

Standards that were already included in v3.1:

- OpenStack-powered Compute v2022.11
- [scs-0100-v3: Flavor naming (v3.1)](https://docs.scs.community/standards/scs-0100-v3-flavor-naming)
- [scs-0102-v1: Image metadata](https://docs.scs.community/standards/scs-0102-v1-image-metadata)

Standards new with v4:

- [scs-0101-v1: Entropy](https://docs.scs.community/standards/scs-0102-v1-image-metadata)
- [scs-0103-v1: Standard flavors](https://docs.scs.community/standards/scs-0103-v1-standard-flavors)
- [scs-0104-v1: Standard images](https://docs.scs.community/standards/scs-0104-v1-standard-images) with [spec file](https://raw.githubusercontent.com/SovereignCloudStack/standards/main/Tests/iaas/scs-0104-v1-images.yaml)

## Testing Regime

The following regulations apply for those certifications where regular testing is required.

In general, automated tests (where applicable) shall be performed at least weekly.

- Tests for OpenStack-powered Compute may be performed less frequently, but no fewer than once a year.

## Previous Versions

- v4 extends v3 by including new standards as listed above.
