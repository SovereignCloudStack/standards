---
title: Standards, Docs and Organisation
type: Procedural
version: 2023-08-03-001
authors: Max Wolfs
state: draft
track: Global
---

## Introduction

The Sovereign Cloud Stack (SCS) is a complex ecosystem, comprised of numerous Components and packages designed to accommodate a wide array of use cases. Given the unique functionalities of these components, the creation of a unified and comprehensible documentation presents a significant challenge. This procedural standard aims to define the structure and maintenance process for our documentation, thereby offering seamless and efficient access to users.

## Motivation

SCS promotes a collaborative environment by actively contributing to upstream projects. The involvement of individuals and companies within our community significantly enhances the SCS Bill of Materials (BOM), further amplifying its complexity. Consequently, our documentation must:

- Offer an overview and visual representation of the architectural model
- Foster coherence by maintaining a consistent theme throughout the documentation
- Facilitate a transparent and inclusive community environment
- Describe various deployment examples and use cases
- Reflect the SCS structure in the documentation's navigation

## Distributed Documentation

In line with the [OpenStack documentation approach](https://docs.openstack.org/doc-contrib-guide/), most SCS Components and components maintain independent documentation. To keep this documentation up-to-date and eliminate manual duplication, we utilize a custom workflow that synchronizes individual documents during the static documentation page's build process.

## Methodology and Taxonomy

Addressing the complexity of SCS requires an effective documentation structure. Accordingly, we have adopted the [Diataxis taxonomy](https://diataxis.fr/), categorizing the documentation into four distinct sections: Tutorials, Guides, References, and Explanations.

## Structure Template

The technical documentation and navigation should parallel the logical structure of the SCS Architecture. By doing so, users can better comprehend the information hierarchy and effectively visualize the SCS. The proposed structure is as follows:

```tree
├── Introduction
├── Getting Started
│    ├── Overview
│    ├── Virtualization
│    └── Containerization
├── IaaS Layer
│    ├── Overview
│    │        ├── Architecture
│    │        ├── Compute
│    │        ├── Storage
│    │        ├── Knowledge
│    │        └── Network
│    ├── Deployment Examples
│    │        ├── Example 1
│    │        │   ├── Hardware
│    │        │   └── Software
│    │        ├── ...
│    │        │   ├── Hardware
│    │        │   └── Software
│    │        └── Example x
│    │            ├── Hardware
│    │            └── Software
│    ├── Guides
│    │        ├── Guide 1
│    │        ├   ...
│    │        └── Guide x
│    └── Components
│        ├── Component 1
│        ├   ...
│        └── Component x
├── Container Layer
│    ├── Overview
│    │        ├── Architecture
│    │        └── ...
│    ├── Prerequisites
│    │        ├── Hardware
│    │        ├── Software
│    │        └── Knowledge
│    ├── Guides
│    │        ├── Guide 1
│    │        ├── ...
│    │        └── Guide x
│    └── Components
│        ├── k8s-cluster-api-provider
│        ├   ...
│        └── Component x
├── Operating SCS
│    ├── Overview
│    ├── Guides
│    │   ├── Guide 1
│    │   ├── ...
│    │   └── Guide x
│    ├── Monitoring
│    ├── Incident Management
│    ├── Audits
│    ├── Lifecycle Management: Patches/Updates & Upgrades
│    └── Logging
├── Identity and Access Management (IAM)
├── Releases
├── Standards
├── FAQ
└── Glossary
```

### Single Component/Component

The technical documentation and navigation should parallel the logical structure of the SCS Architecture. By doing so, users can better comprehend the information hierarchy and effectively visualize the SCS. The proposed structure is as follows:

```tree
│        ├── Component
│        │    ├── overview.md
│        │    └── requirements.md
│        │    ├── quickstart.md
│        │    ├── configuration.md
│        │    ├── contribute.md
```

Each document serves a specific purpose:

#### Overview

This document introduces the Component/component by addressing the basic "Why," "How," and "What" questions, and articulating the problems it solves in the broader SCS context answering the following questions:

- What is it and for what do I need this? What benefits does it have for users?
- What organization/company does this belong to? (Link to company/organization)
- Where am I – as module – within the bigger context of SCS?

#### Requirements

This section enumerates the necessary prerequisites to utilize the component, including software, hardware, and any required technical knowledge. What are the minimal requirements needed for a quickstart?

#### Quickstart

A concise guide providing users with a quick set up of the component, covering installation instructions, basic configuration, and initial steps. Caution: it is only for testing and not for production.

- What is the aim of this quickstart guide?
- Rule: one line per command for easy copy&paste and one line for description where possible
- Rule: only one working path for installation.

#### Configuration

This section elaborates on the configurable aspects of the component, such as options, parameters, or settings that users can modify to suit their needs.

#### Contribute

This document provides instructions on how interested parties can contribute to the component's development. It includes information on issue submission, proposed changes, and participation in discussions.

### Technical Implementation

SCS employs Docusaurus, a contemporary static website generator, to implement the Docs Standard. Docusaurus serves as an ideal platform for creating, managing, and deploying extensive documentation.

#### Documentation Framework

Docusaurus' robust toolkit assists in crafting and maintaining quality documentation. It offers comprehensive features such as Markdown support, customizable themes, and versioning, making it an excellent choice for our needs. This platform allows us to create user-friendly and visually engaging documentation.

#### Special Implementation Details

SCS's unique architecture necessitates a unique approach to documentation. To ensure seamless integration of reference documentation for Components and components developed for SCS, we have created a custom workflow. This workflow automatically syncs upstream repositories, pulling the most recent documentation at regular intervals.

We have accomplished this by utilizing a Node.js post-install script found [here](https://github.com/SovereignCloudStack/docs-page/blob/main/getDocs.js).

This script prompts the system to pull the latest docs every eight hours and build the static page. The workflow's specifications can be viewed here.

The [SCS documentation](https://docs.scs.community/) is built by the tooling from the [docs-page](https://github.com/SovereignCloudStack/docs-page/) repository, pulling content from [docs repository](https://github.com/SovereignCloudStack/docs/) as well as many other components as defined in the docs.package.json [here](https://github.com/SovereignCloudStack/docs-page/blob/main/docs.package.json).

### Writing Style and Format – Style Guide

#### Formatting and Linting

All documentation text files must be provided as markdown files with an .md extension. This prerequisite ensures uniformity across our documents, making them more accessible and comprehensible.

#### Diagrams, Charts, and Images

When necessary, diagrams, charts, and images can be used to simplify complex information. They should be properly captioned and referenced in the text.

#### Linting

To maintain a clean and consistent content repository, we enforce linting on:

- All staged files before committing
- All Pull Requests

##### Pre Commit

We run markdownlint against staged Git files using the Husky Git hook. This process is facilitated by [lint-staged](https://github.com/okonet/lint-staged) and [husky](https://github.com/typicode/husky).

The markdown files are linted according to the rules specified by [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) and formatted with [prettier](https://github.com/prettier/prettier).

The linting rules are specified in the configuration file .markdownlint-cli2.jsonc. Additionally, [markdownlint-rule-search-replace](https://github.com/OnkarRuikar/markdownlint)

##### GitHub Workflows

There are two actions running on every Pull Request on the main branch:

1. link-validator.yml validates every link in the markdown files.
2. pr-markdownlint.yml checks all markdown files according to the rules defined within .markdownlint-cli2.jsonc.

The Style Guide can be found [here](https://docs.scs.community/community/community/contribute/styleguide/).

### Open Questions

--

### Reference

--
