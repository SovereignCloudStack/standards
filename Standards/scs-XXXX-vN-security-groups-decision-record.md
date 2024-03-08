---
title: Security Groups Decision Record
type: Decision Record
status: Draft
track: IaaS
author: josephineSei
date: DD-03-2024
---

## Introduction

Security Groups in IaaS (OpenStack) are sets of ip table rules, that are applied to ports which connect a VM to a network.
In contrast to other resources like flavors or volume types that are always publicly accessable, or images that can be both public and private, security groups are always bound to the project level.
That creates some diffucilties for a possible standard of Security Groups, which are discussed in this document.

## Terminology

Security Group
  A set of iptables rules that is applied to ports connecting a VM and a network.

Security Group Rule (abbr. Rule)
  This references a single rule within a security group.

RBAC
  Role Based Access Control used for policies and alike.

network rbac / neutron rbac
  These access controls will let administrators and users share neutron related resources with other projects.

admin
  The most powerful role in OpenStack. Only given to some Operators of the Cloud Infratructure.

## Context

While creating a VM and also later on, one or more security groups can be added to it.
When there is no security group specified the default security group will always be added.
Like every other security group, the default group is also project bound.
That means, it can be edited as required by project members.

When thinking about standardizing security groups, the goal is to automatically have more than one default security group.
But to also have predefined groups with predefined roles for certain and often used cases as e.g. ssh, http and https (maybe also icmp).
Those groups should best be available to all projects and predefined by administrators.

As security groups are project bound and there is no native way to them to be shared, we are left with two options:

1. To use another endpoint `network rbac` to share security groups among different projects.
2. To adhere to the project scope of security groups and only give documentation about recommended security groups to users.

### Option 1: operator usage of network rbac

The `network rbac` endpoint[^1] manages the possibitity to share and access certain network sepcific resources as security groups.
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

[^1]: [Neutron RBAC](https://docs.openstack.org/neutron/latest/admin/config-rbac.html)

### Option 2: stay project-scoped

Using and adhering the project scope of the security groups has the consequence, that:

1. either an admin has to set up security groups for each project
2. or the SCS project only provides a guide on how to setup and use some recommended security groups.

As users are allowed to, will and should edit their security groups, there is no way to ensure, that a certain set of security groups with certain rules is always present in a project.
So packing an extra burden on admins is unreasonable.
The option to give a guide and recommend a few security groups however is a quite good option.

## Decision

To be decided.

## Consequences

What becomes easier or more difficult to do because of this change?

## Related Documents

[A PR to a first draft for a guide for security groups](https://github.com/SovereignCloudStack/docs/pull/142)
