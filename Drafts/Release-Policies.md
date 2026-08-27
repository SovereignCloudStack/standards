# SCS Releases

or: What does a release mean in the SCS world?

## Definition

An SCS Release is an annual attestation that a curated set of third-party
open-source modular software stacks have been validated as a reliable basis for
building and operating a "Certified SCS-compatible IaaS" environment. The SCS
project does not ship or maintain the attested software itself — instead, each
release represents a quality endorsement of a known-good combination of upstream
projects. Providers are free to use any software they choose; an SCS Release
does not limit or prescribe those choices, but serves as a reference signal for
what has been tested and validated by the SCS community. The following three
pillars define the criteria that MUST or SHOULD be met for software to be
included in an SCS Release:

### Pillar 1: Real-world Production Deployment (MUST)

To be attested in an SCS Release, a modular software stack MUST be in active
production use in at least one provider environment that holds a valid
"Certified SCS-compatible IaaS" certification at the time of the release. This
ensures that the attestation is grounded in real-world, production-grade
deployments rather than theoretical compatibility.

### Pillar 2: Compliance Documentation (SHOULD)

For each modular software stack included in an SCS Release, there SHOULD be
comprehensive documentation covering the implementation-specific configuration
necessary to achieve and maintain "Certified SCS-compatible IaaS" compliance.
This documentation SHOULD be sufficiently detailed to allow a skilled operator
to reproduce a compliant deployment based on the documented modular software
stack.

### Pillar 3: Automated Integration Testing (SHOULD)

Automated testing pipelines that validate the full modular software stack used
to deliver a "Certified SCS-compatible IaaS" environment SHOULD exist at the
integration layer. These pipelines SHOULD ideally incorporate the SCS testing
framework to verify conformance with SCS standards and to detect regressions
across the integrated modular software stack.

## Schedule

Our release schedule is time-based: We publish one release per year on June 1st.

Releases are announced on our web page and via press releases. There is an
announcement mailing list that all users of SCS should subscribe to, where
release information will be posted.

Each release is accompanied by release notes documenting the attested modular
software stacks, notable changes from the previous release, and known issues
with the attested versions.

## Maintenance

An SCS Release attestation is considered maintained until one month after the
following year's release is published. During this period, the SCS project
monitors the attested software versions for relevant CVEs, security advisories,
and critical known issues, and publishes compatibility notes or advisories where
necessary. The attestation itself is not revised — if issues are severe enough
to affect the validity of the endorsement, a formal advisory will be issued.

For high-profile issues, especially security issues, we will send out
notification emails to our announcement mailing list.

## Support

There is NO commercial L1/L2 support provided by the central SCS team.

We will look at reported issues and work on addressing them, but this requires
issues that have been pre-analyzed and qualified already. This does not include
working with operators to determine whether a problem is a hardware issue, a
misconfiguration, or an incompatibility between software components outside the
attested modular software stack. The SCS project also does not guarantee
response times or resolution times.

This leaves an opportunity for companies to create commercial support services.
If partners want to build such support services and offer L1/L2 support, there
is an option for the SCS project to build a certification to ensure high quality
services. There is also the option to offer commercial L3 support for the L1/L2
partners with defined response times. Some CSPs might build up sufficient
in-house skills to provide L1/L2 internally and only rely on a commercial L3
service from the SCS project.

## Attested Modular Software Stacks

Each SCS Release categorizes the modular software stacks and configurations it
covers by the level of validation confidence, based on how many of the three
pillars defined above are met. This categorization carries no expectation of
mandatory use.

1. Modular software stacks that meet all three pillars: **Fully Attested**

- In active production use at a certified provider (Pillar 1)
- Compliance documentation is available (Pillar 2)
- Automated integration testing pipelines exist for the full stack (Pillar 3)

2. Modular software stacks that meet Pillars 1 and 2, but where automated
    integration testing is not yet complete: **Partially Attested**

- In active production use at a certified provider (Pillar 1)
- Compliance documentation is available (Pillar 2)
- Automated integration testing is absent or incomplete (Pillar 3 not yet met)

3. Modular software stacks that meet Pillar 1 only: **Minimally Attested**

- In active production use at a certified provider (Pillar 1)
- Compliance documentation and automated integration testing are not yet
  available (Pillars 2 and 3 not met)
- We welcome feedback, qualified issue reports, and contributions for these
  modular software stacks

4. Configurations for which compliance documentation exists but that are not yet
   in active production use at a certified provider: **Documented (Unattested)**

- Ideally, some automation exists in our CI to validate that the documentation
  stays accurate

5. **Not Attested**

**Modular software stacks or configurations not listed are not officially
endorsed by an SCS Release.**

## Deprecation

Each SCS Release is a snapshot of what certified providers are actually running
in production at the time of the release. The composition of the attestation can
therefore change from year to year, and no continuity guarantees can be made for
any attested modular software stack.

Where the SCS project is aware that providers are deprecating certain software
modules and that these are therefore likely to be removed from the attested
modular software stack in the next SCS Release, we will notify the SCS community
as early as possible.

## Certification

The "Certified SCS-compatible IaaS" certification program is the authoritative
reference for what it means to operate an SCS-compatible cloud environment. An
SCS Release attests that certain software versions and configurations are a
validated basis for achieving this certification, but by no means sufficient on
their own. Providers seeking certification should refer to the current
certification program documentation and test suite for the definitive
requirements.
