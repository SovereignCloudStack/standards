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

The Sovereign Cloud Stack project is compiled of several layers: Infrastructure and Container. Every layer may include different
mandatory or optional standards. Every layer is noted as a dedicated map in the certification YAML.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `iaas` | Map | List of versioned sets of SCS standards for the IaaS layer  | |
| `kaas` | Map | List of versioned sets of SCS standards for the KaaS layer  | |

Note that we don't currently have separate certification layers for Operations and IAM.
We expect that tests for these aspects will exist, but be incorporated into the IaaS
and KaaS layers.

## Set of standards

Every layer keeps record of the whole history of defined standards in a `version` map item.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.versions` | Array of maps | List of all past and upcoming set of standards | |
| `{layer}.versions.version` | String | Version of the particular list of standards  | _v3_ |
| `{layer}.versions.standards` | Array of maps | List of standards for this particular layer  | |

## Time evolution

Every version of the standard has a date at which it is effective (`stabilized_at`)
and may have an expiration date (`replaced_at`).

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.versions.stabilized_at` | Date | ISO formatted date indicating the date after which the set of standards was considered stable | _2022-11-09_ |
| `{layer}.versions.replaced_at` | Date | ISO formatted date indicating the date on which this version of the standard can no longer be used for certification | _2023-04-09_ |

Note that at any point in time, all versions that are older (`stabilized_at` is at or before this point)
can be certified against, unless the version is already obsoleted (the opint is after `replaced_at`).
This means that more than one version may be allowable at a certain point in time. Tooling should default
to use the newest allowable version (the one with the most recent `stabilized_at` date) then.

## Standards

Every list of standards consists of several standards that – altogether – define the particular layer standard in the given version.

| Key 	| Type 	| Description 	| Example   |
|-----	|------	|-------------	|---------- |
| `{layer}.versions.standards.name` | String | Full name of the particular standard | _Flavor naming_ |
| `{layer}.versions.standards.url` | String |  Valid URL to the latest raw version of the particular standard  | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Standards/SCS-0003-v1-flavor-naming.md_ |
| `{layer}.versions.standards.check_tool` | String | Valid local filename or URL to the latest check tool that verifies compliance with the particular standard | _https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Design-Docs/tools/flavor-name-check.py_ |
| `{layer}.versions.standards.check_tool_args` | String | *Optional* list of arguments to be passed to the `check_tool`. Preferably none needed. | `-v` |
| `{layer}.versions.standards.condition` | String | State of the particular standard, currently either `mandatory` or `optional` | _mandatory_ |

## Basic Example

```yaml
name: SCS Open
url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-open.yaml
depends_on:
  name: SCS Compatible
  url: https://raw.githubusercontent.com/SovereignCloudStack/Docs/main/Certification/scs-compatible.yaml
iaas:
  versions:
    - version: v5  # This version is in a draft state and work in progress
      stabilized_at: 2022-11-09
      replaced_at: 2023-04-09
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
      stabilized_at: 2022-04-01
      standards:
        - name: ....

    - version: v3  # This is the stable set of standards that us currently active
      stabilized_at: 2021-10-01
      replaced_at: 2022-11-08
      standards:
        - name: ....

    - version: v2  # This set of standards is obsolete and has been replaced by v3
      stabilizied_at: 2021-07-01
      replaced_at: 2021-11-01
      standards:
        - name: ....
 kaas:
   versions:
     - ...

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

# Tooling
The SCS repository Docs has a tool `scs-compliance-check.py` tool in the `Design-Docs/tools` directory
which parses the SCS Certficiation YAML and then runs the tests referenced there, returning the results
of the tests.

# Open Questions

# Acknowledgements

This document is heavily inspired by the [publiccode.yml standard](https://yml.publiccode.tools/), as published by the [Foundation for Public Code](https://publiccode.net/).
