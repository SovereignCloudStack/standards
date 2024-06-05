---
title: Default Rules for Security Groups
type: Standard
status: Draft
track: IaaS
---

## Introduction

Security Groups in IaaS (OpenStack) are part of the network security mechanisms provided for the users.
They resemble sets of virtual firewall rules allowing specific network traffic at a port of a VM that connects it to a network.
They are project-bound, which means that all Security Groups that are newly created are only available to the project in which they were created.
This is also the case for the default Security Group that is created for each project as soon as the project itself is created.

## Terminology

Security Group (abbr. SG)
  Set of ip table rules, used for tenant network security.

Security Group Rule (abbr. SG Rule)
  A single ip table rule, that is part of a SG.

Administrator (abbr. Admin)
  Operator = User of an OpenStack cloud with the admin role.

## Motivation

The rules of a Security Group can be edited by default by any user with the member role within a project.
But when a Security Group is created it automatically incorporates a few SG rules that are configured as default rules.
Since the 2023.2 release, the default set of Security Group rules can be adjusted.
This functionality is only available to administrators[^1][^2].
In combination with the OpenStack behavior that when a VM is created with no Security Group specified, the default SG of the project is automatically applied to the ports of the VM,
a user cannot be sure which firewall rules are applied to such a VM.

Therefore this standard proposes default Security Group rules that MUST be set by administrators to avoid divergence in default network security between different IaaS environments.

[^1]: [Tracking of development for editable default SG rules](https://bugs.launchpad.net/neutron/+bug/1983053)
[^2]: [Release Notes of Neutron 2023.2](https://docs.openstack.org/releasenotes/neutron/2023.2.html)

## Design Considerations

Up to the 2023.1 release (antelope) the default Security Group rules are hardcoded in the OpenStack code.
We should not require to change this behavior through code changes in deployments.

Beginning with the 2023.2 release (bobcat) the default Security Group rules can now be edited by administrators through an API.
All rules that should be present as default in Security Groups have to be configured by admins through this API.

There are two ways to approach a standard for the default rules of Security Groups.

1: There could be a set of rules standardized that has to be configured by admins.

OpenStack's default rules for Security Groups already provide a good baseline for port security, because they allow all egress traffic and for the default Security Group only ingress traffic from the same group.

Allowing more rules would not benefit the security level, while reducing or limiting the existing rules would barely improve it.
Nevertheless a standard could hold up the current security level against possible future release with more open default rules.
Changing the default rules will not change the rules of any existing security groups.

2: With the already strict OpenStack default rules users are required in most use cases to create and manage their own Security Groups.

This has the benefit that users need to explicitly think about the port security of their VMs and may be less likely to apply Security Groups which rules open up more ports than needed.
There is also a guide from the SCS project on how to set up a security group that also focuses on having a good port security[^3].

With the default OpenStack behavior of having already strict rules, which in most cases require users to manage their own Security Groups, this standard should mandate a middle way:
It should allow adjusting the default rules, but only to a stricter version.

Allowing all outgoing traffic in the default rules in combination with blocking all incoming traffic would be strict enough from a security point of view.
And it would make it necessary for users to check and change the rules of their Security Group to a meaningful set.

[^3]: [Guide for Security Groups](https://docs.scs.community/docs/iaas/guides/user-guide/security-groups/)

### Further Annotations

This standard should only be applied onto versions of OpenStack that implement the new endpoint for the default Security Group rules, which would only include 2023.2 or higher releases.

It is possible to have different default Security Group rules for the default SG and custom SGs.
And it is arguable to have a more strict standard for default rules for the default Security Group than for the custom Security Groups.
Because the latter ones are not automatically applied to a VM but are always edited by the users to apply to their requirements.

The allowlisting concept of Security Group rules makes it hard to allow traffic with an exception of certain ports.
It would be possible to just define many rules to achieve what a blocklist would achieve.
But having many rules may confuse users and they may not disable unnecessary default rules in their SGs.

## Standard

The default Security Group rules for the default Security Groups SHOULD allow incoming traffic from the same Security Group.
The default Security Group rules for ALL Security Groups MUST NOT allow any other incoming traffic. Neither IPv4 nor IPv6.
This can be achieved through having ingress rules in the default Security Group rules that allow ingress traffic from the Remote Security Group "PARENT" but are only used in the default Security Group.

The default Security Group rules for ALL Security Groups SHOULD allow egress Traffic for both IPv4 and IPv6.

### Example

In the following table, there is only ingress traffic between the same default Security Groups allowed plus all egress traffic:

```bash
$ openstack default security group rule list
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| ID                       | IP Protocol | Ethertype | IP Range  | Port Range | Direction | Remote Security Group | Remote Address Group | Used in default Security Group | Used in custom Security Group |
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| 47b929fd-9b39-4f22-abc5- | None        | IPv6      | ::/0      |            | egress    | None                  | None                 | True                           | True                          |
| 7d4f64d10909             |             |           |           |            |           |                       |                      |                                |                               |
| 92a79600-5358-4fef-a390- | None        | IPv4      | 0.0.0.0/0 |            | egress    | None                  | None                 | True                           | True                          |
| 822665f46070             |             |           |           |            |           |                       |                      |                                |                               |
| 93e35d0c-2482-4ec1-9fbd- | None        | IPv4      | 0.0.0.0/0 |            | ingress   | PARENT                | None                 | True                           | False                         |
| fd8c9a21a04e             |             |           |           |            |           |                       |                      |                                |                               |
| ed5cd662-add2-4e42-b0a7- | None        | IPv6      | ::/0      |            | ingress   | PARENT                | None                 | True                           | False                         |
| 3b585d348820             |             |           |           |            |           |                       |                      |                                |                               |
+--------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
```

## Related Documents

The spec for introducing configurability for the default Security Groups Rules can be found [here](https://specs.openstack.org/openstack/neutron-specs/specs/2023.2/configurable-default-sg-rules.html).

More about Security Groups as a resource in OpenStack can be found [here](https://docs.openstack.org/nova/latest/user/security-groups.html).

## Conformance Tests

The conformance tests should check for the absence of any ingress traffic rules except traffic from the same Security Group in the `openstack default security group rule list`.
As having egress rules is allowed by this standard, but not forced and can be set in various ways, the tests should check for presence of any egress rules.
