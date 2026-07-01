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

## Concept definitions

A standard can be viewed as a collection of propositions that "must" (or "should") be satisfied
by a test subject (cloud or cluster). The standard is satisfied if all "must" propositions are
satisfied.

A _testcase_ is a collection of propositions that coincide with respect to the following properties:

- whether they can be tested automatically with normal user permissions;
- how often they need to be tested (daily, weekly, monthly, annually);
- whether they are required ("must").

We unambiguously refer to a testcase using a composite identifier consisting of two parts:

- the _scope_: in the context of this standard, just an identifier of a namespace;
  for example: `scs-compatible-iaas` (or a UUID)
- the _testcase id_, for example `scs-0100-syntax-check` or `scs-0101-fips-test`.

The scope part is usually clear from the context and therefore omitted.

A _test_ is a testcase or a collection of tests. We refer to a test using the same kind of
composite identifier as for a testcase.

For instance, if we have testcases `scs-0100-syntax-check` and `scs-0100-semantics-check`,
we could define the test `scs-0100-v3` as the collection consisting of these two testcases.
Given further tests `scs-0101-v1`, `scs-0102-v1` etc., we could define the test `scs-0501-v4`
as the collection consisting of `scs-0100-v3`, `scs-0101-v1`, `scs-0102-v1` etc.

A test can be viewed as a collection of propositions; namely, all propositions of all testcases
that are part of the test.

The _result_ of a test is one of the following values:

- `FAIL`: it could be verified that at least one of its propositions is not satisfied;
- `MISS` (missing): for at least one of its propositions, it was not (recently) attempted to verify it;
- `DNF` (did not finish): for at least one of its propositions, it could not be verified whether it is satisfied;
- `PASS`: it could be verified that all its propositions are satisfied.

If multiple items apply, we always opt for the topmost one.

A _score card_ is a data structure that contains the following information:

- Subject: the name of the test subject,
- Scope: the scope of all the testcases referred to in this score card,
- Test results: a mapping that maps testcase ids to results.

A _test report_ is a data structure that contains the information of a score card, plus:

- Creator: who created the report (name of person or version of test suite),
- Check date: when the test was performed,
- Log: free-form text that details the test run.

A _check script_ is a computer program that tests one or more testcases and reports the result per testcase.

The precise form of the data structures (score card, report), as well as the input-output formats of the check scripts is up to the implementation, but it must be well documented.

A _test suite_ is a collection of interoperable check scripts, i.e., check scripts that use the same data structures and I/O formats.

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
