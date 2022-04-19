# SCS Releases

or: What does a release mean in the SCS world?

## Schedule

Our release schedule is time-based: We release every 6 months.\
Release dates are in Mar and Sep, which gives us \~5 months to integrate the latest OpenStack and Ubuntu releases. (We will only use Ubuntu LTS versions however.)\
First release will be R0, which will ship in April 2021 -- the delay is due to the delayed start of the funded project.

Releases are announced on our web page and via press releases. There is an announcement mailing list that all users of SCS should subscribe to, where release information will be posted.

Releases include release notes, which document some of the highlights (new features) and changes. Known issues ... are also documented here.

## Maintenance

We will provide maintenance (bugfix and security updates) for a release for 7 months or 1 month until the next release is published, whichever comes later. This gives providers 1 month time to migrate to the latest release after it has been published without leaving the maintained area. There may be space for commercial offerings to provide maintenance (and support) for older versions. [If those are offered from outside of the SCS team, the SCS project does insist on the option to create a certification program to ensure the quality of the provided services meet the SCS standards; though my thinking is that we should provide this from the SCS project if there is significant demand.]

Maintenance is provided as a regular stream of updates: Once the changes have passed our CI (which runs at least on a daily basis), they will be made available.

For high profile issues, especially security issues, we will send out notification emails to our announcement mailing list.

## Support

There is NO commercial L1/L2 support provided by the central SCS team.

While we will look at reported issues and will work on addressing them (and including the fixes in our update stream). This requires bug reports that have been pre-analyzed and qualified already; this does not include working with customers (CSPs) to determine whether or not there is a hardware issue or a misconfiguration. The SCS does also does not guarantee response times or fix times.

This leaves an opportunity for companies to create commercial support services. If partners want to build such support services and offer L1/L2 support, there is an option for the SCS project to build a certification to ensure high quality services. There is also the option to offer commercial L3 support for the L1/L2 partners with defined response times. Some CSPs might build up sufficient in-house skills to provide L1/L2 internally and only rely on a commercial L3 service from the SCS project.

## Features

There are a few kinds of features included in a release:

1\.Things that we consider standardized and stable: **Official standard Features**

* Every SCS cloud provider should use these
* We should have tests in place to ensure these things don't break

2\.Things that we consider stable, but optional: **Official optional features**

* Cloud providers may decide to implement these
* We should also have tests in place (though less urgently)

3\. Things that we do not consider stable yet, but still want to include it for demos, to show where we are going etc: **Technical Preview Features**

* Ideally, these stabilize after the release and can be selectively enabled by partners (after alignment with the SCS team)
* There is no guarantee for this to happen
* We are open to feedback and contributions for these -- we explicitly welcome suggestions, qualified bug reports etc.

4\.Things that are not included but that we **document** how users (or providers) set it up themselves

Ideally, we have some automation that does set this up in our CI and tests is, so the documentation stays true

5. Not included / not supported

**Services not listed are not officially supported.**

## Deprecation

Features or category 1 and 2 are guaranteed to be also included in future releases in a backward compatible way, so providers and users (DevOps teams) can rely on them not going away.\
We make no promises of forward compatibility (things developed for a new version would work on an older release); we will only invest some effort into providing it, where it is easy for us to do.

When features of these categories will change in non-backwards compatible ways or need to be removed, we will discuss it with our active partners and announce the decisions at least one release (6 months) in advance. If the SCS project finds out that there are unusual circumstances, in which this promise can not be kept, it will reach out to customers and partners as soon as possible. SCS does commit to provide assistance (in form of documentation, answering questions, ...) to customers that struggle with the situation.

Features in categories 3 and 4 have no guarantees to be included in the next release, to not change in incompatible ways or to being promoted to categories 2 or 1. However, in our monthly newsletters, we will talk about these from time to time, so our partners can easily stay up to date in their understanding where we are going.

## Backports

A strong focus of SCS is on assuring the upstream projects are healthy and strive. For this to be possible a strong effort is made to assure features and fixes are implemented upstream.
Sometimes the upstream release cycle will have an impact on when a feature or fix is available for SCS consumers. Backporting could then be considered an option.
The following aspects should be considered in these case:

* The feature / fix must be merged upstream onto main
* Only if upstream will not accept a backport, a local backport is adviseable
* Is the feature a blocking requirement?
* Is a local backport simple enough - if not this is a *strong* argument against a local backport


## Implementation services

We strive to make it easy to set up an SCS environment. This means that we provide documentation, defaults and automation to allow standard SCS setups to created by appropriately skilled engineers. However, we will no have the bandwidth to cover unusual integrations (user management, network setups, billing systems, ...) -- these could be provided by commercial companies that offer consulting and implementation services around SCS. Again, we reserve the right to create certification programs to ensure high quality services here. We explicitly encourage partners to contribute knowledge in this space to our knowledge base.

## Operations services

Operating the SCS stack at high quality is typically harder than getting it to work.

SCS explicitly has the goal to achieve "Open Operations". We extend the idea of "Open Source", where companies (and individuals) collaborate on building software together in the open to the operational topics. This means we build the collaboration spaces to document best practices in operations, including automation mechanisms and tools, best practices on ops processes, etc. We explicitly encourage our partners to support each other. For larger scale collaboration in this space, we will need to incentivize the correct behavior by monitoring contributions and support and avoid the moral hazard from free riders. We could imagine to support JVs by partners or to create a commercial operational services offering. We reserve the right to create a certification program for partners that offer services to ensure good quality.

## Certification

At the time of this writing (Mar 2021), we have few documented standards. We all expect that SCS implementations will meet the requirements of the OpenStack powered Compute 2020.11 trademark certification and SCS does include tests for it.

Due to the lack of formalized tests, we can not yet certify stack yet, that do not use most of the SCS codebase in the implementation. The plan is to change this significantly until we release R1.

So for R0, the SCS trademark "SCS powered" we will only be allowed to partners which use most of SCS and which provide transparency into all of the downstream changes they apply. SCS reserves the right to veto such changes if and only if these would pose a significant risk to backwards stability or to compatibility with other SCS implementations.\
SCS partners that want to offer SCS compatible stacks and want to use the SCS trademark to advertise this to their clients need to run the CI tests regularly, have monitoring in place and need to provide normal tenant user-level access to their environment to the SCS project for free (with reasonable quota with at least 10 VMs, 10 vCPU, 80 GIB block storage, 2 routers, 10 nets/subnets, 10 security groups, 40 security group rules). SCS reserves the right to use its access for monitoring the performance/availabiilty/... of the partners' environment and publish that data. Where this is not feasible in private cloud settings (e.g. due to compliance reasons), the SCS project will work with the partner to review their installation and monitoring and grant the SCS powered certification. SCS might ask for compensation in this case.

Thinking about SCS trademarks:

* "SCS powered public platform" (this includes compatibility and monitoring) -- we plan to not charge for this (?)
* "SCS powered private platform" -- this should have the same technical requirements minus possibly some federation features what many not make sense in this setting. We might also not be able to monitor ... the platform and thus can not provide visibility into it
* "SCS ... with XXX" -- this allows to advertise **optional standardized features** of SCS. Applications may depend on these (and thus only work on the subset of SCS providers that chose to implement these features). There will be conformance tests for such features. All XXX terms are defined by SCS -- it is not allowed for partners to invent terms here.
* "SCS ... gold/platinum" -- this will indicate higher levels of compliance. We would disallow non-open-source pieces in the stack and mandate public availability of all downstream changes, enforce certain security and data-protection standards (e.g. only ops personell from a certain region or encryption), transparency for RCAs, SLAs, proven skills for the Ops personell, architectural review by SCS , .... This will need to be defined in the future. We would expect to charge for this.[\*]

[\*] We might accept donations in terms of free access to infrastructure as compensation. Similarly, we might invent a system where contributions to our knowledge or code base might be counted and rewarded points that lower compensation for certification.
