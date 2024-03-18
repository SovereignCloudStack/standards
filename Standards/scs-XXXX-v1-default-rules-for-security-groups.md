---
title: Default Rules for Security Groups
type: Standard
status: Draft
track: IaaS
---

## Introduction

Security Groups in IaaS (OpenStack) are sets of ip table rules, that are applied to ports which connect a VM to a network.
They are project-bound, which means that all Security Groups that are newly created are only available to the project in that they were created.
This is also the case for the default Security Group that is created for each project as soon as the project itself is created.

## Terminology

Security Group (abbr. SG)
  Set of ip table rules, used for tenant network security.

Security Group Rule (abbr. SG Rule)
  A single ip table rule, that is part of a SG.

Administrator (abbr. Admin)
  Operator = User of an OpenStack cloud with the admin role.

## Motivation

The rules of a security Group can be edited by any user with the member role within a project.
But when a Security Group is created it automatically incorporates a few SG rules that are specified by administrators since the 2023.2 release[^1][^2].
In combination with the OpenStack bevior that when a VM is created and no Security Group is specified, the default SG of the project is automatically applied to the ports of the VM,
a user cannot be sure which IP table rules are applied to such a VM.

Therefore this standard proposes default Security Group rules that MUST be set by administrators to avoid differences in default network security in different IaaS-Environments.

[^1]: [Tracking of development for editable default SG rules](https://bugs.launchpad.net/neutron/+bug/1983053)
[^2]: [Release Notes of Neutron 2023.2](https://docs.openstack.org/releasenotes/neutron/2023.2.html)

## Design Considerations

Until the 2023.1 release (antelope) the default Security Group rules are hardcoded in the OpenStack Code.
We should require to not change this behavior through code changes in deployments.

Beginning with the 2023.2 release (bobcat) the default Security Group rules can now be edited by administrators through an API.
All rules that should be present as default in Security Groups MUST be configured by admins through this API.

### Open questions

The requirement to not change the default code of earlier OpenStack releases is difficult to test.
It should be considered to only apply this standard onto versions of OpenStack that implement the new endpoint for the default Security Group rules, which would only include 2023.2 or higher releases.

It is possible to have different default Security Group rules for the default SG and custom SGs.
And it is arguable to have a more strict standard for default rules for the default Security Group than for the custom Security Groups.
Because the latter ones are not automatically applied to a VM but are always edited by the users to apply to their requirements.

The Whitelisting concept of Security Group rules makes it hard to allow traffic with an exception of certain ports.
It would be possible to just define many rules to achieve what a blacklist would achieve.
This has the severe downside that users could be confused by these rules and will not disable unnecessary default rules in their SGs.

## Standard

The default Security Group rules for ALL Security Groups MUST NOT allow incoming Traffic. Neither IPv4 nor IPv6.
This can be achieved through the absence of any ingress rules in the default Security Group rules.

The default Security Group rules for ALL Security Groups SHOULD allow egress Traffic for both IPv4 and IPv6.
This standard should not forbid to also disallow all outgoing traffic.
Allowing all outgoing traffic in the default rules in combination with blocking all incoming traffic would be strict enough from a security point of view.
And it would make it necessary for users to check and change the rules of their security group to a meaningful set.

### Example

In the following table, there is no ingress traffic allowed but all egress traffic:

```bash
$ openstack default security group rule list
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| ID                       | IP Protocol | Ethertype | IP Range  | Port Range | Direction | Remote Security Group | Remote Address Group | Used in default Security Group | Used in custom Security Group |
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| 47b929fd-9b39-4f22-abc5- | None        | IPv6      | ::/0      |            | egress    | None                  | None                 | True                           | True                          |
| 7d4f64d10909             |             |           |           |            |           |                       |                      |                                |                               |
| 92a79600-5358-4fef-a390- | None        | IPv4      | 0.0.0.0/0 |            | egress    | None                  | None                 | True                           | True                          |
| 822665f46070             |             |           |           |            |           |                       |                      |                                |                               |
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
```

These rules can also be configured to only apply to custom Security Groups through the API.

## Related Documents

The spec for the default Security Groups Rules can be found [here](https://specs.openstack.org/openstack/neutron-specs/specs/2023.2/configurable-default-sg-rules.html).

More about Security Groups as a resource in OpenStack can be found [here](https://docs.openstack.org/nova/latest/user/security-groups.html).

## Conformance Tests

The conformance tests should check for the absence of any ingress traffic rules in the `openstack security group rule list`.
As having egress rules is allowed by this standard, but not forced and can be set in various ways, there will not be any tests for such rules.
