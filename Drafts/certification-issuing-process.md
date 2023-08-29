---
title: Regulations for achieving SCS certification
type: Procedural
status: Draft
track: Global
---

# Introduction

The Sovereign Cloud Stack (SCS) issues certificates of various types, among them _SCS-compatible IaaS_ (infrastructure as a service) and _SCS-compatible KaaS_ (Kubernetes as a service).

This document details how a cloud service provider (henceforth, CSP) can attain such a certificate for one of their clouds.

# Motivation

As Operator, I want to achieve the Certificate SCS compatible.

# Regulations

1. Each certificate issued pertains to a certain cloud, a certain type (here, SCS-compatible IaaS or SCS-compatible KaaS), and a certain version of that type with a fixed expiry date. The certificate is only valid for that cloud and for the time frame that ends on that expiry date.

2. For achieving the certificate „SCS compatible“ an operator MUST include the official SCS compliance test suite in his continuous test infrastructure -- for public clouds the recommended way to achieve this is to offer the SCS project access to the infrastructure so the test suite runs can be triggered continuously by the SCS team and ensure continuous compliance. For non-public clouds, the results (log files) can be submitted to SCS by a mechanism of SCS' choice and need to be reproduced again on request by SCS.

**FIXME:** Mention the possibility to create a Zuul project and add nodepools to Zuul? How would that even work?

<!-- Initially this will probably be eMail -->
<!-- What happens when the tests fail? Who will be notified, will the certificate be revoked after a given amount of time? -->

3. The SCS certification assessment body (or entities empowered to do so) WILL review the certification application and either grant the certification, reject it or ask for further measures or information.
<!-- body might as well just be a machine, at least on the scs compatible level -->

4. After having received a confirmation of a successful achievement of a certificate granted by the SCS certification assessment body, the operator MAY use the corresponding logo and publicly state the certified „SCS compatibility“ on the respective layer for the time of the validity of the certification. The logos will contain a link to SCS-owned pages that contain details on the achieved standards, either by embedding a hyperlink or a QR code for printed assets.

<!-- Make clear that we – the SCS project – are allowed to test a cloud enviroment on request or request docs that prove the fulfillment of certification requirements -->

# Design Considerations

# Open Questions

# Related Documents

<!-- scs-0003 -->
