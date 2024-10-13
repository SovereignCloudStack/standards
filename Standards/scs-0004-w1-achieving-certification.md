---
title: "Implementtaion hints for achieveing SCS-compatible certification"
type: Supplement
track: Global
status: Draft
supplements:
  - scs-0004-v1-achieving-certification.md
---


# Getting SCS-compatible certification

## Process overview

The *SCS-compatible* Certification for Operators is a technical certification:
The Operator needs to fulfill technical requirements, such as providing certain
APIs and guaranteeing certain platform behavior in order to be certifiable.

These requirements are meant to provide guarantees to their customers, allowing
them to rely on certain features to be available and on certain system behavior
that lets their applications run in a reliable way.

The SCS certification process typically consists of a few simple steps:

1. Running the SCS compliance test suite and adjusting the infrastructure until it passes.
2. Any additional declarations (for non-testable aspects) are written and passed to the SCS certification body.
3. The operator must be a member ("shaper" or "advisor" level) of the Forum SCS-Standards in the
   OSB Alliance (a non-profit) and pay the respective membership fees. Alternatively fees can
   be paid without becoming a member.
4. The cloud can be listed on the SCS pages as *SCS-compatible* with a compatibility status that is
   updated on a daily basis. SCS then tests the infrastructure on a daily basis.

The precise rules that govern how certificates are issued or withdrawn are defined in the
[SCS standard 0004](scs-0004-v1-achieving-certification).


## Self-testing and technical adjustments

In order for a cloud service offering to obtain a certificate, it has to
conform to all standards of the respective scope, which will be tested at
regular intervals, and the results of these tests will be made available
publicly.

The best approach to get your cloud into compliance is by installing the
test suite locally. Have a look at the
[blog article](https://scs.community/blog/2024/10/14/cert-adapt-example.html).

A description how *SCS-compatible IaaS* compliance can be achieved on environments that use different
OpenStack implementations is written up in a blog article
[Cost of making an OpenStack Cluster SCS compliant](https://scs.community/2024/05/13/cost-of-making-an-openstack-cluster-scs-compliant/).

## Declarations

For the SCS-compatible IaaS v5 standard, the providers must — if they implement availability zones
at all (which is optional) — guarantee certain levels of independence for these. This can not
be fully tested by an automated test. The process thus envisions that providers must create some
documentation on the physical infrastructure and how it maps to availability zones and declare that
this documentation reflects the truth. SCS will review the docs and judge whether they meet the
criteria. In case of doubt, audits can be performed.

## Forum SCS-Standards @ OSBA

The SCS brand belongs to the Open Source Business Alliance e.V. (OSBA), an non-profit organization and
association for the Open Source Industry in Germany. After the completion of the funded SCS project
in the OSBA on 2024-12-31, the OSBA sets up the Forum SCS-Standards
which performs the work to evolve the SCS standards, develops the tests and perform the certification
process and thus becomes the SCS certification body.

Members of the OSBA can become also member of the Forum SCS-Standards for an additional membership
fee, providing the financial resources for the Forum SCS-Standards to do its work. Membership in the
OSBA is open to any organization that supports the goals of the OSBA.
Alternatively, a certification fee can be paid without any membership.

## Getting listed and tested

When all tests are passing, all needed declarations are done, fees for the certification or the
membership in the Forum SCS-Standards at the OSBA have been paid, the infrastructure service
can become officially certified.

The SCS team will add the cloud to the [list of certified clouds](https://docs.scs.community/standards/certification/overview)
on the SCS docs page. This can be used to prove to customers that the cloud is SCS compliant.
Note that for public clouds, there will be a nightly job that tests the cloud for compliance, which will be
triggered by SCS infrastructure (zuul). For this, access to a tenant on the cloud needs
to be provided free of charge. (This only requires very low quota, one VM is created for a minute
in one of the tests.)

For clouds not being accessible from the outside, a VPN tunnel or a local monitoring
job (with result upload) can be used.

Please let us know if you want us to create an official SCS-certified badge that
can be used in your marketing material beyond pointing to our list.

### Optional Health Monitor

Note that for almost all certified clouds in the list of certified clouds, we also
have a health monitor running (currently still
[openstack-health-monitor](https://docs.scs.community/docs/operating-scs/guides/openstack-health-monitor/Debian12-Install)
but soon the new [health-monitor](https://scs.community/tech/2024/09/06/vp12-scs-health-monitor-tech-preview/)),
which exposes information on the performance and error rate of each cloud.
This provides some transparency on the state of the clouds by constantly running
scenario tests against them and is tremendously helpful for both the cloud operations
teams and their customers. Strictly speaking, it is *not* a requirement for the
*SCS-compatible* certification, just best practice. It will be part of an
*SCS-sovereign* certification though, where transparency on operational aspects
will be required.

## Staying compliant

Once your cloud is listed in the
[list of certified clouds](https://docs.scs.community/standards/certification/overview)
which is fed by the
[compliance manager](https://compliance.sovereignit.cloud/page/table), it
will enjoy the nightly tests. These might fail for a number of reasons:

* There is a new version of the SCS standards in effect and you need to adjust things.
* Your cloud was unreachable or otherwise had intermittent issues.
* You have done changes to your cloud that break *SCS-compatible* compliance.
* The test automation engine (zuul) is in trouble.
* The tests have a bug.

In either case, this need proper analysis to determine what should be done.
<!--In the list of certified clouds, the tests are performed by github actions.
These are executed from the
[github SCS standards repository](https://github.com/SovereignCloudStack/standards).
By looking at the logs from the github actions, you can typically see why the failure
happened. You could of course also do a local test again to see if the issue can
be reproduced.-->
In the compliance manager (executing tests via zuul), we will add links to the log
files directly on the table, so it will be even easier to find the relevant log files.
It is a good idea to reproduce the failures by running the test suite locally,
as it may be easier to focus on just the one failing aspect of your infrastructure.

Your cloud will show up as failing in the compliance manager after tests start
failing; this is not the same as a revoked certification, though. For clouds that have been
compliant before, it is highly recommended to work with the SCS certification body
upon such failures to determine a way back into compliance that avoids certification
revocation.
