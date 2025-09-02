---
title: "SCS Availability Zones: Implementation and Testing Notes"
type: Supplement
track: IaaS
supplements:
  - scs-0121-v1-Availability-Zones-Standard.md
---

## Automated Tests

The standard will not preclude small deployments and edge deployments, that both will not meet the requirement for being divided into multiple Availability Zones.
Thus multiple Availability Zones are not always present.
Sometimes there can just be a single Availability Zone.
Because of that, there will be no automated tests to search for AZs.

## Required Documentation

The requirements for each Availability Zone are written in the Standard.
For each deployment, that uses more than a single Availability Zone, the CSP has to provide documentation to proof the following points:

1. The presence of fire zones MUST be documented (e.g. through construction plans of the deployment).
2. The correct configuration of one AZ per fire zone MUST be documented.
3. The redundancy in Power Supply within each AZ MUST be documented.
4. The redundancy in external connection within each AZ MUST be documented.
5. The redundancy in core routers within each AZ MUST be documented.

After the initial setup, these requirements typically do not change at all (like the fire zones) or are very unlikely to change (like redundant internet connection).
Because of this, documentation needs to be provided only in the following cases:

1. When a new deployment with multiple AZs should be tested for compliance initially.
2. When there are physical changes in a deployment which already provided the documentation: the changes need to be documented and provided as soon as possible.

### Alternative Documentation

If a deployment already did undergo certification like ISO 27001 or ISO 9001, those certificates can be provided as part of the documentation to cover the redundancy parts.
It is still required to document the existence of fire zones and the correct configuration of one AZ per fire zone.

## Physical Audits

When reasons exist to mistrust the provided documentation, a physical audit by a natural person - called auditor - sent by e.g. the [OSBA](https://osb-alliance.de/) should be performed.
The CSP of the deployment in need of such an audit should grant access for the auditor to the physical infrastructure and should show them all necessary IaaS-Layer configurations that are needed to verify compliance to this standard.
