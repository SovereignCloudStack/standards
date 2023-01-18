---
type: Procedural
status: Draft
track: Global
---

# Introduction

The [Sovereign Cloud Stack (SCS)](https://scs.community) provides standards for a range of cloud infrastructure types.
It strives for interoperable and sovereign cloud offerings which can be deployed and used by a wide range of organizations and individuals.

With a growing number of documents and certification levels for Sovereign Cloud Stack, it is becoming increasingly difficult to keep track
of all stable as well as all upcoming standards. This document describes the standard we use to technically describe certification levels and
the mandatory standards therein.

# Motivation

This standard has three main objectives:
- to provide an overview of the mandatory standards for the different SCS certification levels
- to make the lifecycle of certification levels traceable
- to provide a machine-readable document for further processing (e.g. for a compliance tool suite or continuous integration).

## Overview of mandatory SCS standards

Digging through a repository of draft, stable, replaced and rejected standards becomes increasingly challenging with a growing number
documents and decision records. A central document that lists all mandatory standards to acquire a certain certification level can
resolve this issue. It provides clarity for providers as well as users and helps to understand the value
proposition of SCS.

## Lifecycle of certification levels

Standards and therefore certifications will evolve over time. To provide transparency and traceability for the lifecycle of SCS certification
levels, the whole history of our certifications should be recorded. Pre-notification of changes to our certification levels allows
users to adapt their environments or deployment automation to the new standards in advance.

## Machine-readability for further processing

By providing a machine-readable document, we can generate web-friendly overviews of our certification levels as well as create a tool suite
that checks environments against all described standards.

# SCS Certification YAML

Every certification level is recorded in a dedicated YAML file, e.g. `scs-open.yaml`.

The certification YAML *MUST* contain the following keys:

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `name` | String | Full name of this certification level	| _SCS Open_ |
| `url` | String | Valid URL to the latest raw version of this document | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-open.yaml_ |

The certification YAML *MAY* contain the following keys:

## Dependency

Standards that are required by lower certification levels shouldn't be included in higher tier certification levels again. We thus need to note
on which certification this level is depending on.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `depends_on` | Map | Preliminary certification level on which this certification level depends | |
| `depends_on.name` | String | Full name of the depending certification level | _SCS Compatible_ |
| `depends_on.url` | String | Valid URL to the latest raw version of the depending certification level | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-compatible.yaml_ |

## Layers

The Sovereign Cloud Stack project is compiled of several layers: Infrastructure, Container, IAM and Operations. Every layer may include different
mandatory or optional standards. Every layer is noted as a dedicated map in the certification YAML.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `iaas` | Map | List of versioned sets of SCS standards for the IaaS layer  | |
| `kaas` | Map | List of versioned sets of SCS standards for the KaaS layer  | |
| `iam` | Map | List of versioned sets of SCS standards for the IAM layer  | |
| `ops` | Map | List of versioned sets of SCS standards for the Ops layer  | |

Every layer map keeps track of the particular SCS standards for this layer and their history over time.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.stable` | String | Version of stabilized set of standards for this layer | _v3_ |
| `{layer}.stabilized_at` | Date | ISO formatted date indicating the date after which the set of standards was considered stable | _2022-11-09_ |
| `{layer}.upcoming` | String | Version of upcoming set of standards for this layer | _v4_ |
| `{layer}.replaced_at` | Date | ISO formatted date indicating the date on which the upcoming set of standards will replace the current stable | _2023-04-09_ |
| `{layer}.versions` | Array of maps | List of all past and upcoming set of standards | |

## Set of standards

Every layer keeps record of the whole history of defined standards in a `version` map item.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.versions.version` | String | Version of the particular list of standards  | _v3_ |
| `{layer}.versions.standards` | Array of maps | List of standards for this particular layer  | |

## Standards

Every list of standards consists of several standards that – altogether – define the particular layer standard in the given version.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.versions.standards.name` | String | Full name of the particular standard | _Flavor naming_ |
| `{layer}.versions.standards.url` | String |  Valid URL to the latest raw version of the particular standard  | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Standards/SCS-0003-v1-flavor-naming.md_ |
| `{layer}.versions.standards.check_tool` | String | Valid URL to the latest check tool that verifies compliance with the particular standard | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Design-Docs/tools/flavor-name-check.py_ |
| `{layer}.versions.standards.condition` | String | State of the particular standard, currently either `mandatory` or `optional` | _mandatory_ |

## Basic Example

```yaml
name: SCS Open
url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-open.yaml
depends_on:
  name: SCS Compatible
  url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-compatible.yaml
iaas:
  stable: v3
  stabilized_at: 2022-11-09
  upcoming: v4
  replaced_at: 2023-04-09
  versions:
    - version: v5  # This version is in a draft state and work in progress
      standards:
        - name: Flavor naming
          url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Standards/SCS-0003-v1-flavor-naming.md
          check_tool: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Design-Docs/tools/flavor-name-check.py
          condition: mandatory
        - name: Image metadata
          url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Standards/SCS-0004-v1-image-metadata.md
          check_tool: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Design-Docs/tools/image-md-check.py
          condition: optional
    - version: v4  # This is the upcoming standard with a given target date. No further changes should be done to this set of standards
      standards:
        - name: ....

    - version: v3  # This is the stable set of standards that us currently active
      standards:
        - name: ....

    - version: v2  # This set of standards is obsolete and has been replaced by v3
      replaced_by: v3
      standards:
        - name: ....
 kaas:
   stable: v2
   stabilized_at: ....

```

# Design Considerations

## File format

In order to have a document that can be processed by a wide range of tools, we need to opt for a simple but yet well supported format.
YAML offers readability for humans as well as good support by many frameworks. Since YAML is heavily used in the cloud and container
domain, the choice is obvious.

## Dependency graph for certifications

This standard only allows exactly one depending certification, otherwise we would need to use a list of mappings. Since this is
in accordance to the current plan of the SIG Standardization & Certification, we can safely ignore multiple dependency of
certification for now.

# Open Questions

# Acknowledgements

This document is heavily inspired by the [publiccode.yml standard](https://yml.publiccode.tools/), as published by the [Foundation for Public Code](https://publiccode.net/).
