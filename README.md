# SCS Documentation

Entry point for SCS Docs

# What is SCS? Why should I care?

Please see our [public web site](https://scs.community/) and specifically
the [About SCS](https://scs.community/About/) page.

# Get it and test it: Testbed

The easiest way to get in touch with SCS is to deploy an SCS cloud virtually.

This means that you set up an SCS test installation including all the infrastructure
pieces such as database, message queueing, ceph, monitoring and logging, IAM, the
[OpenStack](https://openstack.org/) core services, and (soon) the Container layer 
on top of an existing
IaaS platform. Currently, only OpenStack is supported as IaaS under the SCS cloud
(so you end up using OpenStack on top of OpenStack -- with nested virtualization
enabled, this performs decently). There is no fundamental limitation -- just
noone has done the porting of the terraform recipes yet to AWS, libvirt,
VMware, ...

SCS is based on [OSISM](https://osism.tech/). Read on the 
[OSISM testbed docs](https://docs.osism.de/testbed/) to learn how to get the
testbed running. Please read carefully through the
[deployment](https://docs.osism.de/testbed/deployment.html) section of the
manual.

The Requirements:Cloud access subsection also lists some clouds that we have
SCS running on and test regularly.

# Existing SCS Clouds

A few production clouds are already based on SCS: betacloud and PlusCloud Open.
More will come soon.

For PlusCloud Open, there is also a document how to
[get started guide for the PlusCloud Demonstrator env](PlusDemonstrator/GettingStarted.MD)

CityNetwork, Open Telekom Cloud, OVH clouds are also known to support the
testbed well. (There are a few caveats with the latter two, but those are
documented and no blockers.) Read above mentioned 
[Requirements:Cloud access](https://docs.osism.de/testbed/deployment.html#cloud-access)
subsections.

# Releases and Roadmap

## Release 0 (2021-07-15)

Barring unforeseen circumstances, we will release R0 of SCS on 2021-07-15.
It's main focus is to demonstrate the viability of our approach to a much broader
audience by providing a well-documented testbed. This will allow anyone interested
to study the system in real-life, test, contribute, compare, ... it.

While already in productive use (on bare metal) by two providers, the bare metal
setup currently has a few more manual steps than we would like. This will improve
with the next releases.

We have worked hard on supporting identity federation (OIDC and SAML) during the last
few months. We have also spent significant effort on getting the k8s stack with
k8s cluster API into a good shape. However, we have determined that we do not
yet consider those two key pieces as production-ready. The goal is to change that
for R1 (see below).

For now, you can use the software to see where SCS is going and test our technical
preview code. We really appreciate feedback we get on these pieces as well.
However keep in mind that we do not guarantee to ship technical previews from
Release n as production ready software in one of the next releases. We certainly
hope to do so.

## Release 1 (2021-09-2x)

The next release will come quickly. We intend to ship production ready k8s stack
(with k8s cluster API) and identity federation.

## Roadmap

We have a 6 month release cadence -- R2 will follow in March 2022.
Until then, we will provide bugfixes and security fixes for R1.

We do work towards a model where our partners can actually follow our main
development branches -- right now, our CI needs a bit more coverage though
to make this safe.

# Contribute and Connect

Please see the [SCS contributor guide](https://scs.community/docs/contributor/).

# Standards, Conformity and Certification

We intend to work on a conformity test suite.

Right now, we are basically relying on upstream tests -- RefStack (to perform
the OpenStack trademark certification tests formerly known as DefCore).

We have two specific standards aligned within the SCS community (and have also
sought feedback from the broader Gaia-X and OpenStack communities):

* [SCS Flavor naming and standard flavors standard](Operational-Docs/flavor-naming-draft.MD)

* [SCS Image naming and metadata standard](Design-Docs/Image-Properties-Spec.md)

Beyond this, we have a [draft document](Design-Docs/SCS-Spec.md) that captures our
view on how SCS compatible environments should look like. This one has not yet
seen sufficient review to be eligible for standardization. However, we appreciate
feedback (raise issues and PRs or start discussions).

# Issues and bugs

Please raise issues on github. If you can identify the affected component,
raise the issue against the relevant repository. Otherwise you can use
the issues repository. Obviously we appreciate PRs even more than issues;
please don't forget to sign off your contributions (see
[contributor guide](https://scs.community/docs/contributor/) ).

When reporting bugs, it is very useful to include some standard information
typically needed to analyze:
* What state of software (SCS) were you testing? What version numbers ... ?
* How does your environment look like (hardware, operating systems, etc.)?
* What did you do?
* What did you expect? What happened instead?
* Have you done this successfully before? What changed?


# Other resources

Please check our main [web page](https://scs.community/).
If you are an onboarded SCS community member, find here a link to our
[nextcloud](https://scs.sovereignit.de/) (login required).

We are in the process of setting up mailing lists and chats, please hold on ...

