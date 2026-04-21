---
title: "CNCF Kubernetes conformance: Implementation and Testing Notes"
type: Supplement
track: KaaS
supplements:
  - scs-0201-v1-cncf-conformance.md
---

## Implementation notes

The actual execution of the conformance tests is performed by the [SCS compliance check suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests) using [Sonobuoy](https://sonobuoy.io).

## Automated tests

The script [`run_sonobuoy.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/sonobuoy_handler/run_sonobuoy.py) connects to an existing K8s cluster and handles both the execution of Sonobuoy and the generation of the results for a test report.

## Manual tests

None.
