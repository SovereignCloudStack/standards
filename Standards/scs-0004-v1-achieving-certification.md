---
title: Regulations for achieving SCS-compatible certification
type: Procedural
status: Draft
track: Global
---

## Introduction

The Sovereign Cloud Stack (SCS) issues certificates with various scopes, among them _SCS-compatible IaaS_ (infrastructure as a service) and _SCS-compatible KaaS_ (Kubernetes as a service).

This document details how a cloud service provider (henceforth also called operator) can attain such a certificate for one of their clouds.

## Motivation

As operator, I want to obtain a certificate with the scope SCS-compatible IaaS or SCS-compatible KaaS.

## Regulations

1. Each certificate issued pertains to a given cloud, a given scope, and a given version of that scope with a fixed expiry date. The certificate is only valid for that cloud and for the time frame that ends on that expiry date.

2. The operator MUST include the official [SCS compliance test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests) (which does not require admin privileges) in their continuous test infrastructure (e.g., Zuul). The tests MUST be run at given intervals, depending on their resource-usage classification:

    - _light_: at least nightly,
    - _medium_: at least weekly,
    - _heavy_: at least monthly.

   For public clouds, it is recommended to offer the SCS project access to the infrastructure so the test suite runs can be triggered continuously by the SCS team.

   Alternatively, and for non-public clouds, the results (log files) MUST be submitted to SCS by a mechanism of SCS' choice and need to be reproduced again on request by SCS.

   <!-- Initially this will probably be eMail -->

3. If the desired certificate requires manual checks, then the operator MUST offer the SCS project suitable access. Manual checks MUST be repeated once every 3 months.

4. Details on the standards achieved, as well as the current state and the history of all test and check results will be displayed on a public webpage (henceforth, _certificate status page_) owned by SCS.

5. The SCS certification assessment body (initially the SCS project in the OSB Allliance e.V., possibly further entities empowered to do so by the SCS trademark owner, currently the OSB Alliance e.V.) WILL review the certification application and either grant the certification, reject it or ask for further measures or information.
   <!-- body might as well just be a machine, at least on the scs compatible level -->

6. Once the certificate is granted by the SCS certification assessment body, the operator SHOULD use the corresponding logo and publicly state the certified "SCS compatibility" on the respective layer for the time of the validity of the certification. In case of a public cloud, this public display is even REQUIRED. In any case, the logo MUST be accompanied by a hyperlink (a QR code for printed assets) to the respective certificate status page.

7. If the certificate is to be revoked for any reason, it will be included in a publicly available Certificate Revokation List (CRL). This fact will also be reflected in the certificate status page.

8. If any of the automated tests or manual checks fail after the certificate has been issued, the certificate is not immediately revoked. Rather, the automated tests MUST pass 99.x % of the runs, and the operator SHALL be notified at the second failed attempt in a row at the latest. In case a manual check fails, it has to be repeated at a date to be negotiated with SCS. It MAY NOT fail more than two times in a row.

## Design Considerations

## Open Questions

## Related Documents

As of now, this document pertains to the certificate scopes on the certification level _SCS-compatible_ only. It will be extended to cover the remaining levels as they become relevant, either directly or by way of referring to additional documents.

For details on our mechanisms for developing, denoting, and versioning the certificate scopes, we refer to the document [scs-0003-v1](scs-0003-v1-sovereign-cloud-standards-yaml.md).
