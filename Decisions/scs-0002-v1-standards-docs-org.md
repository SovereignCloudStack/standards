---
type: Procedural
status: Draft
track: Global
---

# Introduction

The old Docs repository had a subdirectory `Design-Docs/` which holds Docs on
Design Considerations, older Architecture Decision Records (ADRs) and even
Standards. It also has a `Design-Docs/tools/` subdirectory with conformance
checks and our overall conformance check driver (from PR#182).

# Motivation

This directory structure is confusing in a number of ways:
* The conformance checks are hard to find.
* The mixture of document types requires searching at two or three places.

We want to improve this (while avoiding unnecessary churn).

# Suggested cleanup (step 1)

* Move `Design-Docs/tools/` contents to `Tests/`
  - Also create subdirectories then for layers and test, while the overall
    conformance check tool, certification specs and README remain in `Tests/`.
* Rename `Design-Docs/` to `Drafts/`.
  - Use individual PRs to rewrite existing ADRs and Standards there to conform
    to our standards and move them over to `Decisions/` or `Standards/`.

# Open Questions

We don't know yet whether there is always a clear distinction between Standards
and Decisions (ADRs) -- if this turns out too hard to decide, we may unify those
two directories. (The decision will still be needed and be reflected in the header,
but finding the docs will be easier.)

Some documents with findings will remain in the `Drafts` directory.
We may want to categorize these and have a folder e.g. for research results.
