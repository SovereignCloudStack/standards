---
title: Naming convention in SCS
type: _Standard | Decision Record_
status: Draft
track: IAM
---

<!---
This is a template striving to provide a starting point for
creating a standard or decision record adhering to scs-0001.
Replace at least all text which is _italic_.
See https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md
--->

## Introduction

When CSPs try to enroll a new customer they encounter themselfs in
a situation where they have to choose namings for the openstack domain,
project and user.

There might also exists some group or roles from the customers point of
view, like `domain admin` or `project admin` not related at all with
openstack.

## Motivation

Create a naming convention to use during the provisioning of the users and
groups through an openstack domain.

## Design Considerations

OPTIONAL

### Options considered

#### PS approach to naming

For naming the customers the suggestion from PS is the following:

A prefix will be use to differenciate domain, project and user in
the openstack environment. The project name is also added as a sufix.

So the onboaring tool will create the following structure for a new
customer onboarded in the system.

```commandline
domain: d<customer_id> 
project: p<customer_id>-<project_name>
user: u<customer_id>-<user_name>
```

For the customer also a domain admin group and a project admin group are
created. This are not related in any way with openstack. This groups use
the prefix "gd" for domain group and "gp" for group project and are build
like the following:

```commandline
domain admin group: gd<customer_id>-member
project admin group: gp<customer_id>-<project_name>-member
```

For the creation of a domain a new domain admin group is created.

```commandline
openstack domain create d000001
openstack group create gd000001-member
```

When a project is created a new admin group for that project is created.

```commandline
openstack project create p000001-scs_dev_project
openstack group create p000001-scs_dev_project-member
```

After the creation of a project it is necessary to assign roles to the
new groups.

```commandline
openstack role add --group gd000001-member --project p000001-scs_dev_project $role
openstack role add --group gp000001-scs_dev_project-member --project p000001-scs_dev_project $role
```

For the creation of regular non admin users, the accounts will be added
to the "domain admin" group to give them access to all projects within
the domain.

```commandline
openstack user created u000001-user1
openstack group add user gd000001-member u000001-user1
```

In the case of machine accounts, they are only added to the specific
"project admin" groups.

```commandline
openstack user created u000001-svc_user_project
openstack group add user gp000001-scs_dev_project-member u000001-svc_user_project
```

#### _Option 2_

Option 2 description

## Open questions

RECOMMENDED

## Decision

Decision

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
