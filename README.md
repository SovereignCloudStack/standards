# Sovereign Cloud Stack – Standards and Certification

Sovereign Cloud Stack combines the best of cloud computing in one unified standard. SCS is built, backed, and operated by an active open-source community worldwide. Together we put users in control of their data by enabling cloud operators through a decentralized and federated cloud stack – leveraging true digital sovereignty to foster trust in clouds.

## SCS compatible clouds

This is a list of clouds that we test on a nightly basis against our `scs-compatible` certification level.

| Name | Description | Operator | Compliance check |
| ---- | ----------- | -------- | ---------- |
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/contribute/cloud-resources/plusserver-gx-scs.md) | Dev environment provided for SCS & GAIA-X context | PlusServer GmbH | [![Compliance of gx-scs](https://github.com/SovereignCloudStack/standards/actions/workflows/check-gx-scs.yml/badge.svg)](https://github.com/SovereignCloudStack/standards/actions/workflows/check-gx-scs.yml) |

## SCS standards overview

Standards are organized as certification levels according to [SCS-0003-v1](Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md). We currently maintain one certification level `scs-compatible` that is described here: [Tests/scs-compatible.yaml](Tests/scs-compatible.yaml).

More certification levels will follow as the project progresses.

## Repo Structure

This repository is organized according to [SCS-0002-v1](Decisions/scs-0002-v1-standards-docs-org.md).

### Decisions

Decision Records, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](Standards/scs-0001-v1-sovereign-cloud-standards.md#types-of-documents)

### Drafts

Old Design-Docs folder with existing Architectural Decision Records (ADRs). This directory is currently in the process of being consolidated and cleaned up. See [cleanup step-1](Decisions/scs-0002-v1-standards-docs-org.md#suggested-cleanup-step-1) and [open questions](Decisions/scs-0002-v1-standards-docs-org.md#open-questions).

### Operational-Docs

FIXME, best practises

### Standards

Official SCS standards, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](Standards/scs-0001-v1-sovereign-cloud-standards.md).

### Tests

Testsuite and tools for SCS standards, see [Tests/README.md](Tests/README.md).

