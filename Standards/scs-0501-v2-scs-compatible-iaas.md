---
title: SCS-compatible IaaS
type: Standard
track: Scopes
status: Deprecated
stabilized_at: 2023-03-23
deprecated_at: 2023-11-30
replaces:
- scs-0501-v2-scs-compatible-iaas.md
description: |
  The certificate scope for level SCS-compatible and layer IaaS.
---

## Introduction

This is v2 of the certificate scope _SCS-compatible IaaS_.

## Subject Matter

Standards that were already included in v1:

- [scs-0102-v1: Image metadata](https://docs.scs.community/standards/scs-0102-v1-image-metadata)

Standards changed in v2:

- OpenStack-powered Compute v2022.11 (instead of v2020.11)
- [scs-0100-v2: Flavor naming](https://docs.scs.community/standards/scs-0100-v2-flavor-naming) (instead of [v1](https://docs.scs.community/standards/scs-0100-v1-flavor-naming))

## Testing Regime

The following regulations apply for those certifications where regular testing is required.

In general, automated tests (where applicable) shall be performed at least weekly.

- Tests for OpenStack-powered Compute may be performed less frequently, but no fewer than once a year.

## Version history

- v2 amends v1 in the way outlined under 'subject matter'.
