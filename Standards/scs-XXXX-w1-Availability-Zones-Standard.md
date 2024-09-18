---
title: "SCS Availability Zone Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-XXXX-vN-Availability-Zones-Standard.md
---

## Automated Tests

The SCS will also allow small deployments and edge deployments, that both will not meet the requirement for bein divided into multiple Availability Zones.
Thus Availability Zones are not always present and there will be no automated tests to search for AZs.

## Manual Tests / Audits

The requirements for each Availability Zone are written in the Standard.
For each deployment, that uses Availability Zones there has to be done an Audit to check the following parameters:

1. The presence of fire zones MUST be checked.
1.1. The correct configuration of one AZ per fire zone MUST be checked.
2. For each fire zone (== AZ) the following parts MUST be checked:
2.1. There MUST be redundancy in Power Supply
2.2. There MUST be redundancy in external connection
2.3. There MUST be redundancy in core routers

All of these things will either not change at all like the fire zones or it is very unlikely for them to change like redundant internet connection.
Because of this a manual audit will be enough to check for compliance.
