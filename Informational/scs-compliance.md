# SCS compliance

In order to be SCS-compliant, the standards defined by the [SCS project](https://github.com/SovereignCloudStack/) need
to be adapted and complied to. For this reason, SCS provides standard documents and tests in its
[Standards repository](https://github.com/SovereignCloudStack/standards).
If a provider can run the tests supplied in that repository against his infrastructure without a test failure, that
part of his infrastructure can be considered SCS-compliant. It is important to note, that only tests of "stabilized"
standards need to passed, so some standards and also their tests might either be deprecated or still in a draft phase.

Standards and their tests are separated into a few general categories:

## IaaS

Standards for IaaS can be found under the handle scs-01XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for IaaS can be found in the `Tests/iaas` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.

More specific information about making Openstack SCS-compliant in this context can be found under in [this document](openstack/scs-compliance.md). An additional TLDR document is available [here](openstack/scs-compliance-tldr.md).

## KaaS

Standards for KaaS can be found under the handle scs-02XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for KaaS can be found in the `Tests/kaas` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.

More specific information about making Kubernetes SCS-compliant in this context can be found under in [this document](k8s/scs-compliance.md).

## IAM

Standards for IAM can be found under the handle scs-03XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for IAM can be found in the `Tests/iam` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.