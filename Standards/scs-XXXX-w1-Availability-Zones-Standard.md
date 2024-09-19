---
title: "SCS Availability Zone Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-XXXX-vN-Availability-Zones-Standard.md
---

## Automated Tests

The standard will not exclude small deployments and edge deployments, that both will not meet the requirement for being divided into multiple Availability Zones.
Thus multiple Availability Zones are not always present.
Somtimes there can just be a single Availability Zones.
Because of that, there will be no automated tests to search for AZs.

## Manual Tests / Audits / Required Documentation

The requirements for each Availability Zone are written in the Standard.
For each deployment, that uses Availability Zones there has to be done an Audit to check the following parameters:

1. The presence of fire zones MUST be checked.
2. The correct configuration of one AZ per fire zone MUST be checked.
3. For each fire zone (== AZ) the following parts MUST be checked:
4. There MUST be redundancy in Power Supply
5. There MUST be redundancy in external connection
6. There MUST be redundancy in core routers

All of these things will either not change at all like the fire zones or it is very unlikely for them to change like redundant internet connection.
Because of this a manual audit will be enough to check for compliance.

## Physical Audits

In cases where it is reasonable to mistrust the provided documentation, a physical audit by a natural person - called auditor - send by the OSBA (?) should be performed.
The CSP of the deployment, which needs such an audit, should grant access to the auditor to the physical infrastructure and should show them all necessary IaaS-Layer configurations, that are needed to verify compliance to this standard.

