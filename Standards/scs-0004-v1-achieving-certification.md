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

0. Certificates are issued by the SCS certification assessment body (initially the SCS project in the OSB Alliance e.V., to be succeeded by the Forum SCS-Standards in the very same OSB Alliance). An interested party has to apply for certification with this body, which in turn determines the rules that govern what parties are eligible for application (fees may apply).

1. Each certificate issued pertains to a given combination of subject (i.e., cloud environment), scope (such as _SCS-compatible IaaS_, and version of that scope. The certificate is only valid for that combination and for the time frame that ends when the scope expires, or for six months if the expiration date for the scope is not yet fixed.

2. The operator MUST ensure that the official [SCS compliance test suite](https://github.com/SovereignCloudStack/standards/tree/main/Tests) (which does not require admin privileges) is run at regular intervals and the resulting reports transmitted to the [SCS compliance monitor](https://github.com/SovereignCloudStack/standards/tree/main/compliance-monitor).

   For public clouds, the SCS certification assessment body can take on this task provided that suitable access to test subject is supplied.

   The test suite is partitioned according to resource usage; the required test intervals depend on this classification:

    - _light_: at least nightly,
    - _medium_: at least weekly,
    - _heavy_: at least monthly.

3. If the desired certificate requires manual checks, then the operator MUST offer the SCS project suitable documentation. Manual checks MUST be repeated once every quarter. In addition, the SCS certification assessment body reserves the right to occasionally verify documentation on premises.

4. Details on the standards achieved, as well as the current state and the history of all test and check results of the past 18 months will be displayed on a public webpage (henceforth, _certificate status page_) owned by SCS.

   The page will be kept online for the duration of the certificate's validity, plus at least 3 months; afterwards, it can be taken offline, either upon request or in the course of maintenance cleanup. However, the page's content won't be deleted until 12 months after the certificate's expiration, for the page will be reanimated and reused if, within this timeframe, a new certificate is issued for the same scope and the same cloud.

5. The SCS certification assessment body WILL review the certification application and either grant the certification, reject it or ask for further measures or information.

6. Once the certificate is granted by the SCS certification assessment body, the operator SHOULD use the corresponding logo and publicly state the certified "SCS compatibility" on the respective layer for the time of the validity of the certification. In case of a public cloud, this public display is even REQUIRED. In any case, the logo MUST be accompanied by a hyperlink (a QR code for printed assets) to the respective certificate status page.

7. If the certificate is to be revoked for any reason, it will be included in a publicly available Certificate Revocation List (CRL). This fact will also be reflected in the certificate status page.

8. If any of the automated tests or manual checks fail after the certificate has been issued, the certificate is not immediately revoked. Rather, the automated tests MUST pass 99.x % of the runs, and the operator SHALL be notified at the second failed attempt in a row at the latest. In case a manual check fails, it has to be repeated at a date to be negotiated with the SCS certification assessment body. It MAY NOT fail more than two times in a row.

## Design Considerations

## Open Questions

## Related Documents

As of now, this document pertains to the certificate scopes on the certification level _SCS-compatible_ only. It will be extended to cover the remaining levels as they become relevant, either directly or by way of referring to additional documents.

For details on our mechanisms for developing, denoting, and versioning the certificate scopes, we refer to the document [scs-0003-v1](scs-0003-v1-sovereign-cloud-standards-yaml.md).
