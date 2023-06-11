# Sovereign Cloud Stack – Standards and Certification

SCS unifies the best of cloud computing in a certified standard. With a decentralized and federated cloud stack, SCS puts users in control of their data and fosters trust in clouds, backed by a global open-source community.

## SCS compatible clouds

This is a list of clouds that we test on a nightly basis against our `scs-compatible` certification level.

| Name | Description | Operator | v1 IaaS Compliance Check | v2 IaaS Compliance Check | HealthMon |
|---|---|---|:---:|:---:|:---:|
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/cloud-resources/plusserver-gx-scs.md) | Dev environment provided for SCS & GAIA-X context | plusserver GmbH | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-gx-scs-v1.yml?label=v1%20Compliance) | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-gx-scs-v2.yml?label=v2%20Compliance) | [HM](https://health.gx-scs.sovereignit.cloud:3000/) |
| [pluscloud open](https://www.plusserver.com/en/products/pluscloud-open) | Public cloud for customers | plusserver GmbH | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod1-v1.yml?label=v1%20Compliance) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod2-v1.yml?label=v1%20Compliance) | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod1-v2.yml?label=v2%20Compliance) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod2-v2.yml?label=v2%20Compliance) | [HM](https://health.prod1.plusserver.sovereignit.cloud:3000) |
| [Wavestack](https://www.noris.de/wavestack-cloud/) | Public cloud for customers | noris network AG/Wavecon GmbH | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-wavestack-v1.yml?label=v1%20Compliance) | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-wavestack-v2.yml?label=v2%20Compliance) | [HM](https://health.wavestack1.sovereignit.cloud:3000/) |
| [REGIO.cloud](https://regio.digital) | Public cloud for customers | OSISM GmbH | | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-regio-a-v2.yml?label=v2%20Compliance) | [Dashboard](https://apimon.services.regio.digital/public-dashboards/17cf094a47404398a5b8e35a4a3968d4?orgId=1&refresh=5m) |

## SCS standards overview

Standards are organized as certification levels according to [SCS-0003-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md). We currently maintain one certification level `scs-compatible` that is described here: [Tests/scs-compatible.yaml](Tests/scs-compatible.yaml).

More certification levels will follow as the project progresses.

## Repo Structure

This repository is organized according to [SCS-0002-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md).

### Standards

Official SCS standards and Decision Records, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md)).

### Tests

Testsuite and tools for SCS standards, see [Tests/README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/README.md).

### Drafts

Old Design-Docs folder with existing Architectural Decision Records (ADRs). This directory is currently in the process of being consolidated and cleaned up. See [cleanup step-1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#suggested-cleanup-step-1) and [open questions](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#open-questions).
