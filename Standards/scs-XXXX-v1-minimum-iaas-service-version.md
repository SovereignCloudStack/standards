---
title: Standard for the minimum IaaS services versions
type: Standard
status: Draft
track: IaaS
---

## Introduction

The services, which build the IaaS Layer are, will and should be updated on a regular basis.
Older releases or versions of the software of these services may not receive updates anymore.
Those versions should not be used in deployments, so this standard will define how to determine, which versions may be used and which should not be used.

## Terminology

| Term                | Explanation                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| CSP                 | Cloud Service Provider, provider managing the OpenStack infrastructure.                                                                  |
| SLURP               | Skip Level Upgrade Release Process - A Process that allows upgrades between two releases, while skipping the one in between them.        |
| Compute             | A generic name for the IaaS service, that manages virtual machines (e.g. Nova in OpenStack).                                             |
| Network             | A generic name for the IaaS service, that manages network resources (e.g. Neutron in OpenStack).                                         |
| Storage             | A generic name for the IaaS service, that manages the storage backends and virtual devices (e.g. Cinder in OpenStack).                   |

## Motivation

In software projects like e.g. OpenStack the software will be modified and receive bug fixes continously and will have releases of new versions on a regular basis.
Older releases will at some point not recieve updates anymore, because it would need to much developing persons to maintain more and more releases.
Thus older software, which may be used on the IaaS Layer, will eventually not receive security updates anymore.
This threatens the baseline security of deployments, which should be avoided under all circumstances.

## Design Considerations

OPTIONAL

### Options considered

#### Only Allow th current versions of Software

Considering that OpenStack as one provider of IaaS Layer Software has two releases per year, with one SLURP release per year, this option would require CSPs to update their deployment once or twice a year.
Updating a whole deployment is a lot of work and requires also good life-cycle management.
Following the SLURP releases would reduce this work to once per year.

While following new releases closely already provides a deployment with recent bug fixes and new features, it also makes developing standards easier.
Differences between releases will accumulate eventually and may render older releases at some point uncompliant to the scs-standards.

On the other hand on the IaaS Level there aren't many breaking changes introduced by releases and also most standards will also work with older releases.
Security Updates and Bug fixes are also provided by OpenStack for a few older releases with the state `maintained`.
Additionally the [reference implementation](https://github.com/SovereignCloudStack/release-notes/blob/main/Release7.md) is integrating OpenStack releases after half a year - so about the time when a new release is cut by OpenStack.
Considering a CSP that wants to use only SLURP releases and waiting for the referene implementation will already be over a year or 2 releases behind, which cannot be considered as using the current version of IaaS Layer Software.
Thus this option can be dicarded.

#### Allow only maintained versions of Software

While follwoing closely to the newest releases could be advised, there are several downsides to requiring this workflow, even if it would be only for SLURP releases.
Following the reference implementation for example would also lead into being a little bit behind the newest release.
But this is not as bad as it may seem to be, because security related fixes and bug fixes are backported to older but still `maintained` releases.
Which releases still are maintained is stated [here](https://releases.openstack.org).

Allowing maintained versions would give CSPs a little bit more time to update and test their environments, while still receiving relevant security updates and bug fixes.
Also CSPs that want to become scs-compliant may not have the burden to upgrade their deployments, but can test before an upgrade, where they need to put in additional work to become scs-compliant.
While this option should be at least recommended, it makes it hard for alternative IaaS Layer software, as those might have different release schedules.

#### Advise CSPs to maintain older or other versions of software

CSPs may use releases of IaaS software, that are either not maintained anymore by an open source community or may be even closed source implementations of the mandatory IaaS APIs.
In the latter case the newest APIs may even be used, but the version number may differ from the OpenStack versions - expecially the microversions.
Detecting this is not easy, but would require to test specific API request, which were part of the last few releases.
An this will not show, whether security critical bugs are present or have been patched.

Allowing older versions or closed source software would only be acceptable, when CSPs assure (e.g. in documentation), that they themself will patch the software within their deployments.
Security bug fixes must be implemented and proof of the fix then provided.
Only under that circumstances deployments with older or alternative IaaS Layer software, may be handled as compliant.

This option seems to be a little bit too loose to actually advise using it, but when recommending the second option, this one could be used as a fall back.
And CSPs using OpenStack could even be encouraged to upgrade their deplyoments.

## Standard for a minimum IaaS Layer Software version

If OpenStack is used as implementation for IaaS Layer software the minimum version used SHOULD have the status `maintained`[^1].
Otherwise the CSP MUST implement security bug fixes themself within a reasonable timeframe and provide proof of that to the OSBA, so that the compliance will not be revoked.

[^1]: [OpenStack versions and their current status](https://releases.openstack.org)

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

The conformance test need to check, whether an OpenStack microversion is used, that is part of a `maintained` release.
If that is not the case, it can be assumed that either an older OpenStack version or another software is used on the IaaS Layer.
In that case the test should give a Warning, because the CSP then has to provide proof, that all security relevant bugs are fixed.
So the test may check for a provided documented, which has a recent update date.
