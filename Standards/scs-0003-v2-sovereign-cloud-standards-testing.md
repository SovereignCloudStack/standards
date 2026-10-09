---
title: Sovereign Cloud Standards Testing
type: Procedural
status: Draft
track: Global
replaces:
- scs-0003-v1-sovereign-cloud-standards-yaml.md
description: |
  SCS-0003 defines concepts central to testing SCS standards and regulates how results may
  be obtained and aggregated.
---

## Introduction

This standard defines concepts central to testing SCS standards and regulates how results may
be obtained and aggregated.

## Motivation

We want to attest certain propositions. In its most basic form, an attestation takes the form
subject-predicate-object, for instance,

> `regio-a` (subject) `passes` (predicate) `scs-0501-v5` (object)

where

- `regio-a` is an IaaS environment and
- `scs-0501-v5` refers to [scs-0501-v5](https://docs.scs.community/standards/scs-0501-v5-scs-compatible-iaas).

The objects of our attestations may be whole standards, but usually we will decompose the
standards into smaller units called _testcases_, so that we can test and retest certain parts
more often than others.

## Concept definitions

A standard can be viewed as a collection of propositions that "must" (or "should") be satisfied
by a test subject (cloud or cluster). The standard is satisfied if all "must" propositions are
satisfied.

Note that the same proposition can occur as a requirement (must) in one standard and as a
recommendation (should) in another (version or standard). Likewise, one standard may mandate
that the proposition be tested daily, whereas another (version or standard) might mandate
a different schedule.

A _testcase_ is a collection of propositions. We unambiguously refer to a testcase using a
globally unique identifier, for example `scs-0100-syntax-check` or `scs-0101-fips-test`.

Note that multiple testcases can be joined into a single _composite_ testcase that comprises
all propositions of all these testcases. For instance, we might join `scs-0100-syntax-check`
and `scs-0100-semantics-check` and call the resulting composite testcase `scs-0100-v3`.

The _result_ of a testcase is one of the following values:

- `FAIL`: it could be verified that at least one of its propositions is violated;
- `DNF` (did not finish): no violations could be proven, but for at least one of its propositions,
  it could not be determined with certainty whether it is satisfied or violated;
- `PASS`: it could be verified that all its propositions are satisfied.

A _partial attestation_ is a data structure that contains the following information:

- UUID,
- timestamp,
- subject: the name of the test subject,
- predicate: a result,
- object: a testcase identifier.

A _test report_ is a data structure that contains the following information:

- UUID,
- Creator: who created the report (name of person or version of the software),
- a list of partial attestations,
- Evidence: free-form text that details the test run.

A _check script_ is a computer program that tests one or more testcases and produces a test report.

An _attestation_ is a data structure that contains the following information:

- partial attestation,
- evidence: uuid of a test report.

A _score card_ for a given subject is a list of attestations for that subject;
for each object, only the most recent attestion is contained; otherwise,
the list is comprehensive (no known attestations are omitted).

## Regulation

Each standard must be decomposed into testcases. Each testcase should be "atomic" in the following two senses:

- it's clear what specific part of the standard is satisfied or not satisfied;
- the testcase can be reused for multiple versions of the standards.

The latter criterion is a matter of engineering judgment, because it cannot be known in advance how a standard might evolve.

Each testcase id must be prefixed by `scs-XXXX-` where `XXXX` is the document id of the standard; an exception is possible in the rare case when a testcase applies to multiple standards.

A check script that can test multiple testcases should provide the option to select which testcases to run.

A list of reports from a certain time frame can be merged into an aggregate score card, provided that the following conditions are satisfied:

- for each testcase, the result must be taken from the most recent report containing that testcase,
- if an additional report from the same time frame is known to exist, all its testcases must be contained in more recent reports from the list.
