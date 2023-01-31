---
sidebar_position: 1
---

# SCS Documentation

[![Creative Commons Attribution-ShareAlike 4.0 International](https://licensebuttons.net/l/by-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-sa/4.0/)

## About

The Sovereign Cloud Stack combines the best of Cloud Computing in one unified standard.
SCS is built, backed, and operated by an active open-source community worldwide.
As only the sum of different repositories complete the SCS Stack, it is important to have an easy and accessible documentation in one place.

## What is SCS? Why should I care?

Please see our [public web site](https://scs.community/) and specifically
the [About SCS](https://scs.community/About/) page.
SCS describes a standard as well as a reference implementation of this standard.

## The reference implementation

### Get it and test it: Testbed

The easiest way to get in touch with SCS is to deploy a SCS cloud virtually.

This means that you set up a SCS test installation including all the infrastructure
pieces such as database, message queueing, ceph, monitoring and logging, IAM, the
[OpenStack](https://openstack.org/) core services, and (soon) the Container layer
on top of an existing
IaaS platform. Currently, only OpenStack is supported as IaaS under the SCS cloud
(so you end up using OpenStack on top of OpenStack -- with nested virtualization
enabled, this performs decently). There is no fundamental limitation -- just
noone has done the porting of the terraform recipes yet to AWS, libvirt,
VMware, ...

The SCS IaaS reference implementation is based on [OSISM](https://osism.tech/). Read on the
[OSISM testbed docs](https://docs.osism.de/testbed/) to learn how to get the
testbed running. Please read carefully through the
[deployment](https://docs.osism.de/testbed/deployment.html) section of the
manual.

The [Requirements:Cloud access subsection](https://docs.osism.de/testbed/deployment.html#cloud-access) also lists some clouds that we have
SCS running on and test regularly.

You can easily deploy the container layer on top of the testbed (or a production
SCS cloud of course) checking out the code from
[k8s-cluster-api-provider](https://github.com/SovereignCloudStack/k8s-cluster-api-provider/).

## Existing SCS Clouds

A few production clouds are already based on SCS: betacloud and PlusCloud Open.
More will come soon.

CityNetwork, Open Telekom Cloud, OVH clouds are also known to support the
testbed well. (There are a few caveats with the latter two, but those are
documented and no blockers.) Read above mentioned
[Requirements:Cloud access](https://docs.osism.de/testbed/deployment.html#cloud-access)
subsections.

## Development of SCS

The work done in SCS is supposed to be fed back upstream -- into the relevant
CNCF projects, into OpenStack, into kolla-ansible, into OSISM and others.
An OSISM deployment thus will bring you all the SCS greatness in the base
layer.
Whenever possible SCS works directly in the upstream projects. While the SCS
projects tracks the efforts across the released in [epics and userstories](https://github.com/orgs/SovereignCloudStack/projects),
the work on the code happens upstream - as such these repositories are usually
not found in the SCS namespace.

## Releases and Roadmap

### Release 0 (2021-07-15)

SCS R0 has been released on 2021-07-15 and bundles the work
accomplished by the community prior to the full start of the project.

See [Release Notes for R0](/docs/release-notes/Release0.md) for more information.

### Release 1 (2021-09-29)

R1 came quickly after R0 and was the first release to ship a production ready k8s stack
(with k8s cluster API), some identity federation integration and much improved
preconfiguration for monitoring and logging.

See [Release Notes for R1](/docs/release-notes/Release1.md) for more information.

### Release 2 (2022-03-23)

This release delivers vast improvements for bare metal automation
and the features in the container layers.

See [Release Notes for R2](/docs/release-notes/Release2.md) for more information.

### Release 3 (2022-09-21)

Release 3 features user federation, increase in deployment and upgrade
velocity by improving automated test coverage as well as bringing disk encryption
based on tang from the state of a technical preview to be fully supported.

See [Release Notes for R3](/docs/release-notes/Release3.md) for more information.

### Roadmap

We have a 6 month release cadence -- R4 will follow in March 2023.
Until then, we will provide bugfixes and security fixes for R3.

We do work towards a model where our partners can actually follow our main
development branches -- right now, our CI needs a bit more coverage though
to make this safe.

## Contribute and Connect

Please see the [SCS contributor guide](https://scs.community/docs/contributor/).

## Standards, Conformity and Certification

We intend to work on a conformity test suite.

Right now, we are basically relying on upstream tests --
[RefStack](https://refstack.openstack.org/) (to perform
the [OpenStack trademark certification](https://refstack.openstack.org/#/guidelines)
tests formerly known as DefCore) and the Kubernetes CNCF conformance tests run through
[sonobuoy](https://sonobuoy.io/).

We have two specific standards aligned within the SCS community (and have also
sought feedback from the broader Gaia-X and OpenStack communities):

- [SCS Flavor naming and standard flavors standard](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/flavor-naming.md)

- [SCS Image naming and metadata standard](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/Image-Properties-Spec.md)

Beyond this, we have a [draft document](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/SCS-Spec.md) that captures our
view on how SCS compatible environments should look like. This one has not yet
seen sufficient review to be eligible for standardization. However, we appreciate
feedback (raise issues and PRs or start discussions).

## Issues and bugs

Please raise issues on github. If you can identify the affected component,
raise the issue against the relevant repository in the SovereignCloudStack
or OSISM space. Otherwise you can use
the [issues repository](https://github.com/SovereignCloudStack/issues).
Obviously we appreciate PRs even more than issues;
please don't forget to sign off your contributions (see
[contributor guide](https://scs.community/docs/contributor/) ).

When reporting bugs, it is very useful to include some standard information
typically needed to analyze:

- What state of software (SCS) were you testing? What version numbers ... ?
- How does your environment look like (hardware, operating systems, etc.)?
- What did you do?
- What did you expect? What happened instead?
- Have you done this successfully before? What changed?
- Can this be reproduced? Occasionally? Reliably? How?
- Any analysis you have done? Experiments and their results? Log files?

## Other resources

Please check our main [web page](https://scs.community/).
If you are an onboarded SCS community member, find here a link to our
[nextcloud](https://scs.sovereignit.de/) (login required).

Our community interacts through our [github organization](https://github.com/sovereignCloudStack/),
on [mailing lists](https://scs.sovereignit.de/mailman3/postorius/lists/) as well as
chats [matrix.org:SCS](scs-general:matrix.org).
