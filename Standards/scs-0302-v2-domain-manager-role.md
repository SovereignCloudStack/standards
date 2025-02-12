---
title: Domain Manager adoption notes
type: Standard
track: IAM
status: Draft
replaces: scs-0302-v1-domain-manager-role.md
---

## Introduction

After the domain manager persona has been implemented certain issues in the
standard adoption and verification started being raised by CSPs:

- Not every CSP is using domains to separate customers.

- CSP may rely on the Identity federation in which case it is impossible or is
prohibited to manage identities on OpenStack side (OpenStack is a service
provider and not an identity provider).

- CSP may customize authorization policies in a different way so that domain
manager can not be implemented by simply reusing the upstream implementation.

As such simple enforcement of the Domain Manager persona can not be achieved.

This standard clarifies base standard and splits requirements into recommended
and mandatory to provide better granularity while still giving guidance with
the goal to provide a smooth user experience for the end users.

Requiring customer to use CSP specific APIs to manage identity data is
contradicting the idea of standardization  as such. It hinders customers from
having a smooth user experience across different cloud providers forcing them
to adapt their management strategies on such clouds. Moreover it represent a
lock-in what is contradicting with the idea of SovereignCloudStack.

### Mandatory capabilities

#### Assign roles to users/group on projects/domain

One of the main initial concerns of the Domain Manager was the ability of the
customer to manage user permissions in a self-service manner. OpenStack
Keystone provides an easy possibility to smoothly integrate role assignments
with arbitrary external systems in a transparent way (a role assignment backend
plugin can be provided to persist assignments in any external system). As such
this capability MUST be supported by the CSP using OpenStack APIs or role
assignments.

#### Project creation

Another important requirement was to provide self-service capability for
customers to create projects as desired without requesting CSP support. This
capability MUST be available using native cloud APIs.

#### Project editing

Customer must be able to activate or deactivate project access without
requesting CSP support. This capability provides possibility to temporarily
disable users to authorize into certain project by modifying `enabled` property
of the project. Further control of the project name, description, options and
tags MUST be provided to the customer using native Keystone API.

:::info

Project deletion using Keystone API is not mandatory since CSP may have certain
expectations on the resources cleanup. This requirement is described in detail
in a dedicated chapter.

:::

### Recommended capabilities

Relying on the Identity federation conceptually changes ways of identity
resource management. This makes it impossible to fulfill them as MUST
requirements. This chapter describes remaining capabilities of the initial
Domain Manager as SHOULD implement.

#### Domains usage

It is strongly suggested to rely on the Domain concept of Keystone to implement
multi-tenancy.

Usage of domains by itself allows to implement a form of self-service management
by the customer. Only identity resources are owned by domains (with projects
being also identity resources). Other services use projects for resources
isolation. They do not need to be domain aware.

Using domains allows implementing [domain
limits](https://docs.openstack.org/keystone/latest/admin/unified-limits.html#domain-limits)
which allow to set a global resources limit for the customer. Without domains
specific limits artificial control of the overall customer consumption must be
implemented.

#### User management

User management (creation, activation, deactivation, deletion) SHOULD be
possible using OpenStack APIs.

When an external IdP is being used (IdP federation) there is still an
expectation that local users may be required by customers. As such, creation of
users (pre-creating federated users or regular local users) within customer
domain SHOULD be possible. Keystone does not allow certain operations on
federated users (i.e. password change, MFA, name) as such allowing customers to
manage users using OpenStack APIs should not conflict with any additional
requirements.

Security requirements on the customer side or on the CSP side to only allow
federated users to consume platform services was used as the limitating factor
forcing degrading of the capability requirement.

#### Group management

Management of groups SHOULD be possible using OpenStack APIs.

In the case of federated Identities the possibility exists that groups on the IdP
side do not match groups on the cloud provider side. In addition to that there
might be a need to combine federated and local users. This would only be
possible when groups are managed by the OpenStack.

It is advised to keep user groups as mapped entities between external systems
of CSP and Keystone. Upon user login (or using SCIM) user group relation may be
synchronized between both platforms.

#### Project deletion

As described above project deletion may be implemented differently by CSPs.
There are few ways of achieving that:

- Forbid project deletion when resources (i.e. VMs) are still provisioned
inside of those projects. This scenario assumes that the customer is
responsible for cleaning projects before their deletion.

- Automatically purge all project resources by the CSP when project deletion
request is received. In this scenario CSP is implementing custom functionality
to delete all resources before deleting the project.

- Leave orphant resources. In this scenario project is being deleted by the API
with custom cleanup procedures being responsible for dropping orphant resources.

Leaving orphant resources MAY NOT be allowed.

Forbidding project deletion making customer responsible for the cleanup SHOULD
be preferred since it allows preventing the accidental deletion of the
resources. Supplementary methods for purging project resources MAY be offered by
the CSP.
