---
title: Standard for the security of IaaS service software
type: Standard
status: Draft
track: IaaS
---

## Introduction

Software security relies on bug patches and security updates being available for specific versions of the software.
The services, which build the IaaS Layer should be updated on a regular basis based on updates provided by their respective authors or distributors.
But older releases or versions of the software of these services may not receive updates anymore.
Unpatched versions should not be used in deployments as they are a security risk, so this standard will define how CSPs should deal with software versions and security updates.

## Terminology

| Term                | Explanation                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| CSP                 | Cloud Service Provider, provider managing the OpenStack infrastructure.                                                                  |
| SLURP               | Skip Level Upgrade Release Process - A Process that allows upgrades between two releases, while skipping the one in between them.        |
| OSSN                | [OpenStack Security Note](https://wiki.openstack.org/wiki/Security_Notes) - security issues from 3rd parties or due to misconfigurations. |
| OSSA                | [OpenStack Security Advisories](https://security.openstack.org/ossalist.html) - security issues and advices for OpenStack.               |

## Motivation

In software projects like e.g. OpenStack the software will be modified and receive bug fixes continuously and will receive releases of new versions on a regular basis.
Older releases will at some point not receive updates anymore, because maintaining more and more releases simultaneously requires too much manpower.
Thus older software will also eventually not receive security updates anymore.
Using software which does not receive updates anymore threatens the baseline security of deployments and should be avoided under all circumstances.

## Design Considerations

It would be possible to define a minimum version of IaaS Layer software to avoid security risks.
In the following paragraphs several options of defining a minimum version or dealing with security patches otherwise are discussed.

### Options considered

#### Only Allow the current versions of Software

Considering that OpenStack as one provider of IaaS Layer Software has two releases per year, with one SLURP release per year, this option would require CSPs to update their deployment once or twice a year.
Updating a whole deployment is a lot of work and requires also good life-cycle management.
Following only the SLURP releases would reduce this work to once per year.

While following new releases closely already provides a deployment with recent bug fixes and new features, it also makes developing standards easier.
Differences between releases will accumulate eventually and may render older releases non-compliant to the SCS standards at some point.

On the other hand on the IaaS Level there aren't many breaking changes introduced by releases and also most standards will also work with older releases.
Security Updates and Bug fixes are also provided by OpenStack for a few older releases with the state `maintained`.
Additionally the [SCS reference implementation](https://github.com/SovereignCloudStack/release-notes/blob/main/Release7.md) is integrating OpenStack releases after half a year - so about the time when a new release is cut by OpenStack.
Considering a CSP that wants to use only SLURP releases and waiting for the reference implementation will already be over a year or 2 releases behind, which cannot be considered as using the current version of IaaS Layer Software.
Thus this option can be discarded.

#### Allow only maintained versions of Software

While following closely to the newest releases could be advised, there are several downsides to requiring this workflow, even if it would be only for SLURP releases.
Following the SCS reference implementation for example would also lead into being a little bit behind the newest release.
But this is not as bad as it may seem to be, because security related fixes and bug fixes are backported to older but still `maintained` releases.
All releases that are still maintained can be looked up at the releases page from OpenStack[^1].

Allowing maintained versions would give CSPs a little bit more time to update and test their environments, while still receiving relevant security updates and bug fixes.
Also CSPs that want to become SCS-compliant may not have the burden to upgrade their deployments, but can test before an upgrade, where they need to put in additional work to become SCS-compliant.

One problem is, that there might be new features implemented in the newest versions of the software, which are desired by other standards to be SCS-compliant.
In that case allowing all maintained versions would lead to a two-year timespan customers would need to wait for before such a feature becomes available in all SCS-compliant deployments.
In case of security relevant features this is not advisable.

#### Standards implicitly define the minimum versions of Software

Instead of requiring a defined minimum software version, it could be derived from the standards.
Because: Whenever there is a new wanted behavior a standard should be created and a resonable timeframe given to CSPs to adopt a software version that can fulfill the new standard.
Through the combination of all standards that are in place, the minimum version for the IaaS service software is implicitly given.

This would avoid to have conflicting versions of software in terms of feature parity, while also allowing older software.
Using this approach requires an additional advise to CSPs to update or implement patches for security issues.

#### Advise CSPs to integrate software updates

As long as maintained versions of software are used, updates with security patches are available and only need to be integrated.
This can and should be done in a reasonable short timeframe.

But CSPs may even use releases of IaaS software, that are either not maintained anymore by an open source community or may be even closed source implementations of the mandatory IaaS APIs.
Allowing older versions or closed source software would only be acceptable, when CSPs assure (e.g. in documentation), that they themself will patch the software within their deployments.
Security bug fixes must be implemented and proof of the fix then provided.
Only under these circumstances deployments with older or alternative IaaS Layer software may be handled as compliant.

This option could be taken for granted, but to actually advise using it may encourage CSPs to take a closer look on their life-cycle management and security risk handling.
And CSPs using OpenStack could even be encouraged to upgrade their deployments.

## Standard for a minimum IaaS Layer Software version

If a maintained[^1] version of OpenStack is used as implementation for IaaS Layer software, security patches noted in OSSNs and OSSAs MUST be integrated within a reasonable timeframe.
Otherwise the CSP MUST implement security bug fixes themself within a reasonable timeframe.

In both cases proof of the update MUST be send to the OSBA, so that the compliance will not be revoked.

An open SBOM list MAY be used to propagate the current version of the software and may be used as proof of updates.

[^1]: [OpenStack versions and their current status](https://releases.openstack.org)

## Conformance Tests

In case of provided SBOMs the version numbers of the software could be checked.
But this is not a requirement, so there cannot be such a test.
Tests on the integration of security patches itself are difficult.
And even if tests for certain security issues are possible, then those might be received as an attack.
This is the reason there will be no conformance test.

Rather the standard requiring that CSPs provide proof of the fixed vulnerabilites themself.
