---
title: Governance of the SCS community
type: Procedural
status: Draft
replaces: scs-0005-v1-project-governance.md
track: Global
description: |
  This is version 2 of the SCS-0005 and outlines the structure and governance of
  the SCS community by the SCS Project Board and how this is elected.
---

## Introduction

The [Sovereign Cloud Stack (SCS)](https://scs.community) provides standards
for a range of cloud infrastructure types as well as a modular open-source
reference implementation.
The project is governed by the _SCS Project Board_.

## Role of the _SCS Project Board_

The role of the _SCS Project Board_ is the overall governance of the SCS Community and Project.
This happens together with the _Forum SCS-Standards_ of the Open Source Business Alliance. To further
underline this alignment, the _Forum SCS-Standards_ is part of the _SCS Project Board_.
The _SCS Project Board_ itself is elected by the _SCS Community_.

### Definitions

#### _SCS Project_

The _SCS Project_ is the Open-Source project that consists of the software, documentation, documents, blog posts as well as the people ("_SCS Community_") working on this.

#### _SCS Community_

The collective of people, companies, and organizations promoting the idea of the _SCS Project_ as well as the people working on the various aspects.

#### _SCS GitHub Organization_

The _SCS GitHub Organization_ is this: [https://github.com/sovereigncloudstack](https://github.com/sovereigncloudstack)

### Roles in the _SCS GitHub Organization_

#### Members

Joining the SCS GitHub Organization as a contributor results in being assigned the **member role** in the organization. Members are contributors or collaborators who:

- Actively contribute to projects within the organization.
- Have repository-specific access based on their contributions.
- Are eligible to vote in elections and nominate candidates for the _SCS Project Board_.
- Must adhere to the [Code of Conduct](https://github.com/SovereignCloudStack/.github/blob/main/CODE_OF_CONDUCT.md).

#### Owners

Members of the _SCS Project Board_ are also designated as **owners** of the SCS GitHub organization. Owners have administrative privileges, including:

- Managing organization-level settings.
- Onboarding new members.
- Enforcing compliance with governance and community standards.

This alignment ensures that governance roles in the SCS Project Board directly translate into operational responsibilities within the GitHub organization.

## Joining the SCS GitHub Organization

Since being part of the GitHub organization comes with a set of responsibilities, joining the SCS GitHub Organization can be done by:

- being invited by the _SCS Project Board_
- submitting a request to be onboarded as a member to the _SCS Project Board_
- have existing members of the GitHub organization nominate you

One of these items is sufficient.

Actively contributing to one or several of the projects under the governance of the SCS project board should typically result in a membership. Please be aware of our [Code of Conduct](https://github.com/SovereignCloudStack/.github/blob/main/CODE_OF_CONDUCT.md).

## Election of the _SCS Project Board_

### Term

The _SCS Project Board_ is elected for the term of one year. Elections are done
within the last six weeks of the calendar year.

### Seats on the board

The _SCS Project Board_ contains five seats. One of these seats is filled by
the delegate of the _Forum SCS-Standards_. The other four seats are voted upon.

#### Conflict of Interest and Organizational Diversity

To ensure balanced representation and avoid conflicts of interest, no more than one seat on the SCS Project
Board elected by the community may be held by individuals affiliated with the same organization, company,
or employer at any given time. This limitation applies only to the elected seats, not to the seat filled by
the delegate of the Forum SCS-Standards.

If two or more candidates from the same organization are among the top-ranked choices in an election:

- Only the highest-ranked candidate from that organization will be elected.
- The remaining seat(s) will be filled by the next highest-ranked candidate(s) from different organizations.

If an existing board member changes their organizational affiliation during their term, resulting in multiple board
members from the same organization, one of the affected members must resign their seat. The affected members may mutually
agree on who will resign. If no agreement can be reached within 30 days of the affiliation change, the SCS Project Board
will decide by majority vote which member shall retain their seat. A replacement will be determined according to the most
recent election results, selecting the next eligible candidate from a different organization.

#### Resignation

Resignation can happen for several reasons, such as:

- Elected member may sustainably no longer be willing or able to serve on the project board.
- Elected member needs to resign due to conflict of interest (see above for organizational diversity rules).

When a board member resigns, the next eligible candidate from the last election will automatically join the board,
if (s)he accepts it and does not conflict with the organizational diversity rules. In case no more candidates exist,
the board will continue to exist with one person less. As soon as the board loses another member that can not be backfilled,
an extraordinary election will be scheduled for the rest of the term. Resigned members are encouraged to suggest
new candidates. The search for candidates should at least allow for two weeks and the election announced at least
three weeks in advance of happening and run for a week.

### Nominations

Every person who is part of the Sovereign Cloud Stack GitHub organization can be
nominated for the board. Likewise, one can nominate oneself.
The nomination is done by adding the person with the required data to the file corresponding to the term in the "Community-Governance" folder in the [Standards](https://github.com/sovereignCloudStack/standards/) repository. Obviously, the person, that is to be nominated, should be asked before being added to the file.

### Eligible for voting

Every person who is a member of the GitHub organization "Sovereign Cloud Stack" is eligible for voting. In order to be able to vote an onboarding onto the Identity Management of the SCS community needs to happen.

### Electoral management

The voting process is governed by the _Forum SCS-Standards_.
Voting is done using the [Condorcet Internet Voting Service](https://civs1.civs.us/). This is the same system as is [being used by the OpenInfra foundation](https://wiki.openstack.org/wiki/Election_Officiating_Guidelines#Running_the_election_itself).

### Voting period

The voting will be open for a week.

### Announcement

The voting will be announced on the `scs-members` mailing list as well as on the
[General & Announcements](https://matrix.to/#/#scs-general:matrix.org) Matrix channel.
Enlisted voters will receive e-mails to the email address used in the SCS community's
Identity Management system.

### Mechanisms

Each eligible voter is asked to rank the candidates according to their priorities.
The four favorite choices among all voters will be elected into the _SCS Project Board_.
In case there are four or fewer nominees for the election, no formal vote will
be conducted, and all nominees will be elected into the _SCS Project Board_.

## Roles in the _SCS Project Board_

Among the elected Project Board a spokesperson is nominated. The spokesperson is
elected by a simple majority vote among the members of the project board. The
spokesperson is elected for the whole term.

## Version history

- Version 1 existed without major changes since 16.01.2025
- Version 2 extends the detail of the _SCS Project Board_ election by:
  - adding a section to avoid conflict of interest and ensure organizational
    diversity
  - adding a section to define the election mechanism if members of the board
    resign
  - specifying how to proceed when four or fewer candidates are nominated for
    the elections
