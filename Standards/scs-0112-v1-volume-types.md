---
title: SCS Volume Types
type: Standard
status: Draft
track: IaaS
---


## Introduction

A volume is a virtual drive that is to be used by an instance (i. e., a virtual machine). With OpenStack,
each volume is created per a type that determines basic features of the volume as provided by the backend,
such as encryption, replication, or quality of service. As of the writing of this document, none of these
features can be discovered by non-privileged users via the OpenStack API.

## Motivation

As an SCS user, I want to be able to create volumes with certain common features, such as encryption or
replication, and to do so in a standardized manner as well as programmatically.
This standard outlines a way of formally advertising these common features for a volume type to
non-privileged users, so that the most suitable volume type can be discovered and selected easily--both by
the human user and by a program.

## Possible features

The following features are recognized.

| name  | meaning  |
| :--    | :--  |
| `encrypted`  | volumes of this type are encrypted  |
| `replicated` | volumes of this type are replicated (at least threefold)  |

Further features may be added in the future, as outlined in detail in the [decision record regarding volume
types.](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

## Advertising features

The features of a volume type MAY be advertised by putting a _feature list_ in front of its description.
A feature list has the following form:

`[feat:`feat1,feat2,...,featN`]`

where the entries (feat1, ..., featN) are sorted alphabetically, and each entry occurs at most once.

## Recommended volume types

At least one volume type SHOULD feature encryption.

At least one volume type SHOULD feature replicaton.

Note that the two preceding conditions can be satisfied by a single volume type if it has both features.
In this case, the description of this volume type would start as follows:

`[feat:encrypted,replicated]`

## Related Documents

- corresponding [decision record document](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0111-v1-volume-type-decisions.md)

## Conformance Tests

The script `/Tests/iaas/volume-types/volume-types-check.py` connects to an OpenStack environment and tests
the following:

- for each volume type: if its description starts with `[feat:....]`, then this prefix is a feature list
  (sorted, each entry at most once), and each entry is one of the possible features described here,
- the recommended volume types are present (otherwise, a WARNING is produced).

The return code is zero precisely when the test could be performed and the conditions are satisfied.
Otherwise, detailed errors and warnings are output to stderr.
