# Sovereign Cloud Stack – Standards and Certification

SCS unifies the best of cloud computing in a certified standard. With a decentralized and federated cloud stack, SCS puts users in control of their data and fosters trust in clouds, backed by a global open-source community.

## SCS compatible clouds

This is a list of clouds that we test on a nightly basis against our `scs-compatible` certification level.

| Name                                                                                                            | Description                                       | Operator                      | Compliance check                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/cloud-resources/plusserver-gx-scs.md)) | Dev environment provided for SCS & GAIA-X context | PlusServer GmbH               | [![Compliance of gx-scs](https://github.com/SovereignCloudStack/standards/actions/workflows/check-gx-scs.yml/badge.svg)](https://github.com/SovereignCloudStack/standards/actions/workflows/check-gx-scs.yml)                                                                                                                                                                                                                                 |
| [pluscloud open](https://www.plusserver.com/en/products/pluscloud-open)                                         | Public cloud for customers                        | PlusServer GmbH               | [![Compliance of pco-prod1](https://github.com/SovereignCloudStack/standards/actions/workflows/check-pco-prod1.yml/badge.svg)](https://github.com/SovereignCloudStack/standards/actions/workflows/check-pco-prod1.yml) [![Compliance of pco-prod2](https://github.com/SovereignCloudStack/standards/actions/workflows/check-pco-prod2.yml/badge.svg)](https://github.com/SovereignCloudStack/standards/actions/workflows/check-pco-prod2.yml) |
| [Wavestack](https://www.noris.de/wavestack-cloud/)                                                              | Public cloud for customers                        | noris network AG/Wavecon GmbH | [![Compliance of wavestack](https://github.com/SovereignCloudStack/standards/actions/workflows/check-wavestack.yml/badge.svg)](https://github.com/SovereignCloudStack/standards/actions/workflows/check-wavestack.yml)                                                                                                                                                                                                                        |

## SCS standards overview

Standards are organized as certification levels according to [SCS-0003-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md). We currently maintain one certification level `scs-compatible` that is described here: [Tests/scs-compatible.yaml](Tests/scs-compatible.yaml).

More certification levels will follow as the project progresses.

## Repo Structure

This repository is organized according to [SCS-0002-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md).

### Decisions

Decision Records, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md#types-of-documents)

### Drafts

Old Design-Docs folder with existing Architectural Decision Records (ADRs). This directory is currently in the process of being consolidated and cleaned up. See [cleanup step-1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#suggested-cleanup-step-1) and [open questions](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#open-questions).

### Standards

Official SCS standards, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md)).

### Tests

Testsuite and tools for SCS standards, see [Tests/README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/README.md).
