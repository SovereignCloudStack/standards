---
title: Security Groups Decision Record
type: Decision Record
status: Draft
track: IaaS
author: josephineSei
date: DD-03-2024
---

## Introduction

Security Groups in IaaS (OpenStack) are sets of ip table rules, that are applied to ports which connect a virtual machine to a network.
In contrast to other resources like flavors or volume types that are always publicly accessible, or images that can be both public and private, security groups are always bound to the project level.
That creates some difficulties for a possible standard of Security Groups, which are discussed in this document.

## Terminology

Security Group
  A set of iptables rules that is applied to ports connecting a virtual machine and a network.

Security Group Rule (abbr. Rule)
  This references a single rule within a security group.

RBAC
  Role Based Access Control used for policies and alike.

network rbac / neutron rbac
  These access controls will let administrators and users share neutron related resources with other projects.

admin
  The most powerful role in OpenStack. Only given to some Operators of the Cloud Infrastructure.

## Context

While creating a virtual machine and also later on, one or more security groups can be added to it.
When there is no security group specified the default security group will always be added.
Like every other security group, the default group is also project bound.
That means, it can be edited as required by project members.
By design of OpenStack and when not changed, default rules in the default security group block all incoming traffic except from the same Security Group and only allow outgoing traffic[^1].

[^1]: [Default Security Group Rules](https://github.com/openstack/neutron/blob/master/neutron/db/migration/alembic_migrations/versions/2023.2/expand/c33da356b165_security_group_default_rules.py)

### Reasons for and against a standard for security groups

Considering having most likely similiar security groups within different projects, it might make sense to standardize a few security groups for often used cases like ssh, http, https and maybe icmp.
What speaks for standardizing a certain set of security groups:

1. Having a set of correctly configured security groups could reduce misconfiguration from users
2. Re-using correctly configured security groups saves time for users
3. Auditing security groups would be way easier for operators when helping customers
4. The configuration for the Security Groups can be done by networking experts, which may result in a higher security level as when users without expertise configure them

What are the downsides of having a set of standardized security groups:

1. A bug or misconfiguration is a single point of failure for ALL customers
2. Users might apply the wrong security group to their port or VM because they lack the domain knowledge, unknowingly opening themselves to attacks
3. Users will not inspect such default security groups: this may result in applying a wrong group and opening traffic too much
4. the central authority managing the groups does not necessarily know the usecase of the user, the user/operator must know best what kind of security their workload needs. What is a necessary port for 99% of deployments might be a security disaster for my deployment
5. Providing default groups could have the effect of stopping customers to think about their specific security needs and instead just copying default groups and or rules

This leads to a conclusion, that a set of default security groups is only more valuable than harmful for users:

1. when the rules in those groups are configured correctly
2. and when the users still have to think about their network security on their own for each VM they start

### Technical limitations

As security groups are project bound and there is no native way to them to be shared, we are left with three options:

1. To use another endpoint `network rbac` to share security groups among different projects.
2. To adhere to the project scope of security groups and only give documentation about recommended security groups to users.
3. To only add a tutorial on how to create your own security group in general, how to detect what kind of network permissions your project needs for most frequent (linux) workloads and how to craft your own security groups in a secure way.

### Option 0: Pre-Requirement: default rules for the (default) security group

For every project that is created there will also be a project-specific default security group created.
The default rules for the default groups and all other newly created groups can be looked up like this:

```bash
stack@devstack:~/devstack$ openstack default security group rule list
+------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| ID                     | IP Protocol | Ethertype | IP Range  | Port Range | Direction | Remote Security Group | Remote Address Group | Used in default Security Group | Used in custom Security Group |
+------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
| 47b929fd-9b39-4f22-    | None        | IPv6      | ::/0      |            | egress    | None                  | None                 | True                           | True                          |
| abc5-7d4f64d10909      |             |           |           |            |           |                       |                      |                                |                               |
| 6ace51bb-5258-45ab-    | None        | IPv6      | ::/0      |            | ingress   | PARENT                | None                 | True                           | False                         |
| 9ba9-1efbebfb086b      |             |           |           |            |           |                       |                      |                                |                               |
| 92a79600-5358-4fef-    | None        | IPv4      | 0.0.0.0/0 |            | egress    | None                  | None                 | True                           | True                          |
| a390-822665f46070      |             |           |           |            |           |                       |                      |                                |                               |
| 997bb0c2-652e-4d1f-    | None        | IPv4      | 0.0.0.0/0 |            | ingress   | PARENT                | None                 | True                           | False                         |
| b910-e12c89f88b44      |             |           |           |            |           |                       |                      |                                |                               |
+------------------------+-------------+-----------+-----------+------------+-----------+-----------------------+----------------------+--------------------------------+-------------------------------+
```

Those rules can be edited, which may pose a security risk for customers consuming the default security group.
This should be adressed as a pre-requirement [here](https://github.com/SovereignCloudStack/standards/issues/521).

### Option 1: operator usage of network rbac

The `network rbac` endpoint[^2] manages the possibitity to share and access certain network-specific resources such as security groups.
For admins it is possible to use this endpoint to share a security group with ALL projects within the the cloud including ALL projects of ALL domains:

```bash
stack@devstack:~/devstack$ openstack network rbac create --target-all-projects --action access_as_shared --type security_group group-for-everyone
+-------------------+--------------------------------------+
| Field             | Value                                |
+-------------------+--------------------------------------+
| action            | access_as_shared                     |
| id                | 394d8e71-143f-4c5b-a72f-cd10af3222df |
| object_id         | b6a3834a-f89c-47a9-9ed6-ca89e93701c4 |
| object_type       | security_group                       |
| project_id        | 15f2ab0eaa5b4372b759bde609e86224     |
| target_project_id | *                                    |
+-------------------+--------------------------------------+
```

This would fulfill our goal to grant access to predefined security groups for all projects and all groups recieved as shared do not count into the projects quota for security groups.
But there are a few downsides to this:

1. This should be strictly bound to the admin: no other user should be able to share security groups so to not confuse user.
2. The managing of those `network rbac` objects can get out of hand pretty quickly, because there neither is an explicit name for such an object nor do the names of the shared objects appear:

```bash
stack@devstack:~/devstack$ openstack network rbac list --long
+-----------------------------+----------------+-----------------------------+--------------------+
| ID                          | Object Type    | Object ID                   | Action             |
+-----------------------------+----------------+-----------------------------+--------------------+
| 97507e4c-7413-4d61-ab21-    | security_group | 110b1bea-f0e0-4fb7-9fc7-    | access_as_shared   |
| 047fc23516dd                |                | cda1b6f927b0                |                    |
| bc22a865-46f9-4cd2-80af-    | security_group | 5f22e42e-95dc-4c0a-8651-    | access_as_shared   |
| 3c249ba0e010                |                | 57b1dfc8639f                |                    |
| 2467806f-5428-4506-8e23-    | network        | 02ef8579-9917-4a01-893d-    | access_as_shared   |
| f4690db04e01                |                | cb2f9f3d5f98                |                    |
| ed40996e-218d-4daa-b222-    | network        | 73edb86b-d7ab-4db3-82b7-    | access_as_external |
| f3c603a5b8a6                |                | 25fa8b012e40                |                    |
| 45e0a707-af82-42a6-b93f-    | subnetpool     | cd7addd1-05d9-48a8-bc38-    | access_as_shared   |
| efde18216f13                |                | 4a581354983f                |                    |
| e514c2c8-65ac-4062-8b03-    | subnetpool     | ad1cc1ed-3261-4df2-8c73-    | access_as_shared   |
| fe24f6fc4656                |                | c3dd72d59061                |                    |
+-----------------------------+----------------+-----------------------------+--------------------+
stack@devstack:~/devstack$ openstack network rbac show bc22a865-46f9-4cd2-80af-3c249ba0e010
+-------------------+--------------------------------------+
| Field             | Value                                |
+-------------------+--------------------------------------+
| action            | access_as_shared                     |
| id                | bc22a865-46f9-4cd2-80af-3c249ba0e010 |
| object_id         | 5f22e42e-95dc-4c0a-8651-57b1dfc8639f |
| object_type       | security_group                       |
| project_id        | 15f2ab0eaa5b4372b759bde609e86224     |
| target_project_id | *                                    |
+-------------------+--------------------------------------+
```

The biggest downside: As soon as a security group is shared, everyone from every project, can edit the rules of this group.

[^2]: [Neutron RBAC](https://docs.openstack.org/neutron/latest/admin/config-rbac.html)

### Option 2: stay project-scoped

Using and adhering the project scope of the security groups has the consequence, that:

1. either an admin has to set up security groups for each project
2. or the SCS project only provides a guide on how to setup and use some recommended security groups.

As users are allowed to, will and should edit their security groups, there is no way to ensure, that a certain set of security groups with certain rules is always present in a project.
So packing an extra burden on admins is unreasonable.
The option to give a guide and recommend a few security groups however is a quite good option.

### Option 3: security-focused guide

Instead of providing users with a set of default groups or the knowledge about how to create default groups, there could be a guide created that focuses on the crafting of a security group in a secure way.
That would include identifying what kind of network permission a single VM needs and how to proceed after gathering all requirements of the customers workload.

## Decisions

The default Security Group Rules should be standardized as a pre-requirement (Option 0).

Using the `network rbac` endpoint (Option 1) would not solve the idea of having pre-defined and administrator audited Security Groups, because it is possible for any user to edit the rules of shared Security Groups.
Instead the project-scope of the Security Groups should by focused and a guide prepared, that gives insight about creating and using Security Groups with a few examples but with a clear security focus (Mix of Option 2 and 3).

## Consequences

Any CSP will have to follow the standard for the default Security Group Rules.
There are no consequences regarding Security Groups as it and users stay in full control and responsible for their own Security Groups

## Related Documents

[A PR to standardize default Security Group Rules](https://github.com/SovereignCloudStack/standards/pull/525)
[A PR to a first draft for a guide for security groups](https://github.com/SovereignCloudStack/docs/pull/142)
