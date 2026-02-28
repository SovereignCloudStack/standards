---
title: "Implementation hints for achieving SCS Integrator certification"
type: Supplement
track: Global
supplements:
  - scs-0007-v2-certification-integrators.md
---

## Introduction

The standard scs-0007 documents what requirements integration partners must fulfill to be eligible
for being certified as SCS Integrators.
This document describes the process and associated checks used to validate an applicant's suitability based on plausibility checks and the evidence submitted.

## Certification process procedure

To apply for a certification as an SCS Integrator, an application request must be sent to the attestation body. In the application request, the applicant specifies the certification level for which it is applying. The relevant SCS-compliant environments must also be specified as references therein, which should be used to calculate the necessary score according to the scoring system.

If the listed references are joint environments (e.g. two or more implementation partners have jointly set up an SCS environment or manage them together), it must be sufficiently demonstrated what the applicant's own share in the setup and operation of the environment is.

As specified in standard scs-0007, the listed references must also be compatible with standard scs-0004, which means they must qualify as [_Certified SCS-compatible IaaS_](https://docs.scs.community/standards/scs-compatible-iaas) or [_Certified SCS-compatible KaaS_](https://docs.scs.community/standards/scs-compatible-kaas). However, they do not necessarily have to be certified according to SCS-0004. It is sufficient to demonstrate that the respective environment meets the corresponding scope in its current version. Proof is provided by running the official [SCS compliance test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests), whereby all tests must pass. The test suite can be run either by the applicant or the attestation body. Ideally, the test results should be submitted directly together with the application request.

In the next step, the attestation body conducts an examination based on the application request and the accompanying evidence provided. The attestation body gets in contact with the applicant in order to resolve any remaining discrepancies and open issues together.

If there are no outstanding issues and all requirements have been sufficiently met with the relevant evidence, the respective certificate according to the score achieved will be issued.
