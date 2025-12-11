---
title: Certification of integrators
type: Procedural
status: Draft
#stabilized_at: YYYY-MM-DD # TODO when Stable
replaces:
  - scs-0007-v1-certification-integrators.md
track: Global
description: |
  SCS-0007 defines the process and rules on how to become certified as SCS Integrator.
---

## Introduction

The purpose of this document is to describe a concept for how an implementation partner (also referred to as an applicant) can obtain certification as SCS Integrator. In essence, this certificate is intended to express that an applicant has sufficient technical knowledge and experience to provide technical support to other organizations using SCS.
By design, this certification demands to reach a certain score based on a predefined scoring system. As it may take some time for an aspiring applicant to become an SCS Integrator, a lesser variant of the certificate, called SCS Bronze Integrator, is also defined which can be achieved with a lower score.

## Motivation

As an implementation partner, I want to become certified as SCS Integrator in order to prove sufficient technical knowledge and experience to provide technical support for SCS.

## Regulations

The certificates are awarded for a period of one year based on the predefined scoring system below.
The certification is done either by the Forum SCS-Standards or an attestation body nominated by the forum.

### Certificate levels

Version 2 of this standard introduces a multilevel certification with Silver and Bronze levels. The levels are awarded according to a target score to be reached based on a predefined scoring system (see below).

- Certified SCS IaaS Silver Integrator: SCS IaaS (Infrastructure as a Service) implementation partner
- Certified SCS KaaS Silver Integrator: SCS KaaS (Kubernetes as a Service) implementation partner
- Certified SCS IaaS Bronze Integrator: aspiring SCS IaaS (Infrastructure as a Service) implementation partner
- Certified SCS KaaS Bronze Integrator: aspiring SCS KaaS (Kubernetes as a Service) implementation partner

As to remain backward compatibility with version 1 of this standard, the suffix for the "Silver" level MAY be omitted. The certificate level _Certified SCS IaaS Silver Integrator_ and _Certified SCS KaaS Silver Integrator_ therefore corresponds to the previously existing certificates _Certified SCS IaaS Integrator_ and _Certified SCS KaaS Integrator_ from version 1 of this standard. Certificates that have already been issued remain valid and will get the new name when issued once again.

### General expectations

The general expectation for certification is to provide proof of experience in setting up, operating and supporting SCS-compliant environments.

SCS is an open source community project with the goal of enabling digital sovereignty. As such, the commitment and support of this mission SHOULD be recognized and promoted beyond technical competence.

The applicant SHOULD work towards ensuring that digital sovereignty is implemented in accordance with the SCS definition (Standards and [Mission Statement](https://docs.scs.community/community/mission-statement)). This is expressed in a way that, in addition to the technology used to build environments (not necessarily only SCS environments), knowledge and experience in SCS standards compliance (SCS-compatible IaaS and KaaS) is also available and that environments built by the applicant have already been configured in accordance with the standards and are listed on the SCS compliance list.

The applicant SHOULD work towards ensuring that the cloud environments it sets up and/or manages are also officially visible as SCS clouds, thereby strengthening the SCS brand.

### Scoring system

The applicant MUST achieve a total of at least FOUR points to become SCS Silver Integrator or at least TWO points to qualify as SCS Bronze Integrator according to the following scoring system:

- two points for each SCS-compliant environment of a third party successfully brought into production by the applicant in the last 12 months, one point for 6 months;
- two points for each SCS-compliant environment of a third party actively being managed by the applicant for the last 12 months, one point for 6 months;
- two points for each SCS-compliant public-cloud environment with at least two regions or at least three availability zones being operated by the applicant for the last 12 months, one point for 6 months.

Here, an SCS-compliant environment is one that qualifies for [_Certified SCS-compatible IaaS_](https://docs.scs.community/standards/scs-compatible-iaas) or [_Certified SCS-compatible KaaS_](https://docs.scs.community/standards/scs-compatible-kaas), depending on the desired certification.

### Attestation

The audit for the certification of an applicant is carried out by the Forum SCS-Standards or an attestation body. It will assess and, if necessary, obtain evidence from the applicant to be able to estimate which score will be achieved in total and how.

## Version history

- Version 1 introduced the certification as SCS Integrator with the option to request for a voting on exceptions.
- Version 2 introduces a multilevel certification with a predefined scoring system in order to avoid the previously ambiguous voting on exceptions.
