# Sovereign Cloud Stack – Standards and Certification

SCS unifies the best of cloud computing in a certified standard. With a decentralized and federated cloud stack, SCS puts users in control of their data and fosters trust in clouds, backed by a global open-source community.

## SCS compatible clouds

This is a list of clouds that we test on a nightly basis against our `scs-compatible` certification level.

| Name                                                                                                           | Description                                       | Operator                      |                                                                 IaaS Compliance Check                                                                 |                                                        HealthMon                                                         |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------: |
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/cloud-resources/plusserver-gx-scs.md) | Dev environment provided for SCS & GAIA-X context | plusserver GmbH               | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-gx-scs-v2.yml?label=compliant)    |                               [HM](https://health.gx-scs.sovereignit.cloud:3000/)                                        |
| [pluscloud open - prod1](https://www.plusserver.com/en/products/pluscloud-open)                                | Public cloud for customers                        | plusserver GmbH               | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod1-v2.yml?label=compliant) |                               [HM](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-pco)   |
| [pluscloud open - prod2](https://www.plusserver.com/en/products/pluscloud-open)                                | Public cloud for customers                        | plusserver GmbH               | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod2-v2.yml?label=compliant) |                               [HM](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod2) |
| [pluscloud open - prod3](https://www.plusserver.com/en/products/pluscloud-open)                                | Public cloud for customers                        | plusserver GmbH               | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod3-v2.yml?label=compliant) |                               [HM](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod3) |
| [pluscloud open - prod4](https://www.plusserver.com/en/products/pluscloud-open)                                | Public cloud for customers                        | plusserver GmbH               | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-pco-prod4-v2.yml?label=compliant) |                               [HM](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod4) |
| [Wavestack](https://www.noris.de/wavestack-cloud/)                                                             | Public cloud for customers                        | noris network AG/Wavecon GmbH | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-wavestack-v3.yml?label=compliant) |                               [HM](https://health.wavestack1.sovereignit.cloud:3000/)                                    |
| [REGIO.cloud](https://regio.digital)                                                                           | Public cloud for customers                        | OSISM GmbH                    | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-regio-a-v3.yml?label=compliant)   |   broken <!--[HM](https://apimon.services.regio.digital/public-dashboards/17cf094a47404398a5b8e35a4a3968d4?orgId=1&refresh=5m)-->      |
| [CNDS](https://cnds.io/)                                                                                       | Public cloud for customers                        | [artcodix UG](https://artcodix.com/) | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-artcodix-v3.yml?label=compliant)  |                                 [HM](https://ohm.muc.cloud.cnds.io/)                                              |
| [aov.cloud](https://aov.de/)                                                                                   | Community cloud for customers                     | aov IT.Services GmbH          |    (soon)                                                                                                                                             |                               [HM](https://health.aov.cloud/)                                                            |
| PoC WG-Cloud OSBA                                                                                              | Cloud PoC for FITKO                               | Cloud&amp;Heat Technologies GmbH | ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SovereignCloudStack/standards/check-poc-wgcloud-v4.yml?label=compliant)  | [HM](https://health.poc-wgcloud.osba.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?var-mycloud=poc-wgcloud&orgId=1) |

## SCS standards overview

Standards are organized as certification levels according to [SCS-0003-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md). We currently maintain one certification level `scs-compatible` that is described here: [Tests/scs-compatible-iaas.yaml](Tests/scs-compatible-iaas.yaml).

More certification levels will follow as the project progresses.

## Repo Structure

This repository is organized according to [SCS-0002-v1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md).

### Standards

Official SCS standards and Decision Records, see [Standards/scs-0001-v1-sovereign-cloud-standards.md](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md)).

### Tests

Testsuite and tools for SCS standards, see [Tests/README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/README.md).

### Drafts

Old Design-Docs folder with existing Architectural Decision Records (ADRs). This directory is currently in the process of being consolidated and cleaned up. See [cleanup step-1](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#suggested-cleanup-step-1) and [open questions](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0002-v1-standards-docs-org.md#open-questions).
