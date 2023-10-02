# Test and development cloud resources

This document gives an overview of the test and development cloud resources currently provided by our partners.

## How to request cloud resources

To request access to an existing project, please contact the responsible community member. To apply for a new project, please create a pull request against this document (leave `Unique Identifier` blank) and assign it to the particular CSP team (e.g. @SovereignCloudStack/plusserver, @SovereignCloudStack/wavecon, ...)

## plusserver

### Usage

A brief guide on how to use the resources provided by plusserver GmbH can be found [here](plusserver-gx-scs.md)

### Users

As suggested in [#155](https://github.com/SovereignCloudStack/standards/issues/155) the username for non-"service users" will contain the users github handle and are prefixed with a plusserver default.
`prefix-<github handle>`

> **Note**
> ATM this is not directly connected to the SovereignCloudStack github org membership, accounts will be created manually for now.

Example:

| github handle | plusserver login    |
| :-----------: | :-----------------: |
| frosty-geek   | u500924-frosty-geek |
| fkr           | u500924-fkr         |
|               |                     |

> **Note**
> To easy collaboration & transparency within the SCS team all users will have their default_project_id set to `p500924-scs-community` by default and will have full access on all projects listed below.

### Service Users

Service users will have their default_project_id set to a specific project and will NOT be granted full access to other projects by default.

| Unique Identifier                | Service User Name          | Full Access on            | Community Contact | Description                                   | Needed until |
| :------------------------------: | -------------------------- | ------------------------- | ----------------- | --------------------------------------------- | :----------: |
| 9a1576af59644a2dbbace773ad17158d | u500924-svc-sig-monitoring | p500924-sig-monitoring1   | fkr               | Service User - SIG Monitoring                 | 31.12.2023   |
| 4925967416894fd78be6701689059653 | u500924-svc-cloudmon       | p500924-cloudmon-target   | costelter         | Service User - CloudMon Test Project          | 31.12.2023   |
| f89b3d64ddff4d9d8cadb5e06fa22299 | u500924-svc-healthmonitor  | p500924-scs-healthmonitor | garloff           | Service User - SCS Health Monitor             | ∞            |
| 49cc3d72fbdf41fe8dc407f57f026dbf | u500924-svc-standards      | p500924-scs-healthmonitor | garloff           | Service User - SCS Standards Compliance Check | ∞            |
|                                  |                            |                           |                   |                                               |              |

### Projects

| Unique Identifier                | Project Name                | Community Contact | Description                       | Needed until |
| :------------------------------: | --------------------------- | ----------------- | --------------------------------- | :----------: |
| 2237c767cf5f456da19359ed31c1c16b | p500924-scs-community       | fkr               | SCS Community Project             | ∞            |
| b43cfafbcf1f4eb08865b2886c29e09b | p500924-cluster-api-session | garloff           | cluster-api hands on session      | ∞            |
| 9b7a73e516be4cd1acbd63d543985c52 | p500924-gonicus-dev         | o-otte            | GONICUS GmbH                      | ∞            |
| 3829cc7c8f034fc985f5055a1df6f247 | p500924-scs-healthmonitor   | garloff           | SCS Health Monitor                | ∞            |
| b97d38bf128b4479981c4dbe2ef70cd5 | p500924-SIG-IAM             | fkr               | SIG IAM and VP08                  | ∞            |
| 9de7d8dc2d674e52be44904d6b338b0b | p500924-cloudmon            | costelter         | CloudMon Test Project             | 31.12.2023   |
| 2c9e0e4ef8d44c36807df50b06b3c81d | p500924-cloudmon-target     | costelter         | Target project for CloudMon tests | 31.12.2023   |
| 3501db829014406884990a1016f3e25d | p500924-sig-monitoring1     | fkr               | SIG Monitoring - cloudmon target  | 31.12.2023   |
| 602778bad3d3470cbe58c4f7611e8eb7 | p500924-dnation             | chess-knight      | dNation dev for VP06c             | ∞            |
| 91091d4039a6457db27d48d58bb1b4e4 | p500924-jschoone            | jschoone          | KaaS dev and evaluation           | ∞            |
| 93956190702b4a7d8a8886806d57713f | p500924-metering            | cah-link          | Dev Environment for VP13          | 31.12.2023   |
| abbe6561cf6248b6af395334aa09af85 | p500924-harbor              | chess-knight      | SCS Harbor for VP06c              | ∞            |
| 4ff97734574146ccb4c7e7568bc1e36f | p500924-XPanse              | swaroopar         | Eclipse XPanse Projekt POC        | 31.11.2023   |
| e7622c1048ac4520a2d050ae141e826b | p500924-tender-6a           | jschoone          | Dev Environment for VP06a         | ∞            |
| eeed7e0ad33f42f189fb4165116f5a1b | p500924-dnation-k8s         | matofeder         | dNation dev for VP06c             | ∞            |
| b342f37804f14459bdf703573169bf79 | p500924-minery              | 90n20             | Testbed env for Pentesting        | 30.11.2024   |
| 0fa3c3559f0d4f39ba7aa70c7f7188ca | p500924-tender-10-3         | tonifinger        | Dev Environment for VP10-3        | ∞            |
|                                  |                             |                   |                                   |              |

## Wavecon

### Service Users

|        Unique Identifier         | Service User Name | Full Access on | Community Contact | Description                                   | Needed until |
| :------------------------------: | ----------------- | -------------- | ----------------- | --------------------------------------------- | :----------: |
| df4af5376bbd4de587c4335622149be7 | scs-standards     | scs-standards  | itrich            | Service User - SCS Standards Compliance Check |      ∞       |

### Projects

|        Unique Identifier         | Project Name       | Community Contact | Description        | Needed until |
| :------------------------------: | ------------------ | ----------------- | ------------------ | :----------: |
| 718964b4b87446688ac04b151519fb51 | scs                | garloff           | SCS Health Monitor |      ∞       |
| c46ccc9e695c4b23bacee2ad11145d9a | scs-health-monitor | garloff           | SCS Health Monitor |      ∞       |
| 00de553df86949b49365baee6375fb5a | scs-standards      | itrich            | SCS Health Monitor |      ∞       |
