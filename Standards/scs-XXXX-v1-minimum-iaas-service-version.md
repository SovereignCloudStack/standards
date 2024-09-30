---
title: Standard for the minimum IaaS services versions
type: Standard
status: Draft
track: IaaS
---

## Introduction

The services, which build the IaaS Layer are, will and should be updated on a regular basis.
Older releases or versions of the software of these services may not receive updates anymore.
Those versions should not be used in deployments, so this standard will define how to determine, which versions may be used and which should not be used.

## Terminology

| Term                | Explanation                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| CSP                 | Cloud Service Provider, provider managing the OpenStack infrastructure.                                                                  |
| Compute             | A generic name for the IaaS service, that manages virtual machines (e.g. Nova in OpenStack).                                             |
| Network             | A generic name for the IaaS service, that manages network resources (e.g. Neutron in OpenStack).                                         |
| Storage             | A generic name for the IaaS service, that manages the storage backends and virtual devices (e.g. Cinder in OpenStack).                   |

## Motivation

In software projects like e.g. OpenStack the software will be modified and receive bug fixes continously and will have releases of new versions on a regular basis.
Older releases will at some point not recieve updates anymore, because it would need to much developing persons to maintain more and more releases.
Thus older software, which may be used on the IaaS Layer, will eventually not receive security updates anymore.
This threatens the baseline security of deployments, which should be avoided under all circumstances.

## Design Considerations

OPTIONAL

### Options considered

#### _Option 1_

Option 1 description

#### _Option 2_

Option 2 description

### Open questions

RECOMMENDED

## Standard

What is the essence of this standard? Adjust heading accordingly.

## Related Documents

Related Documents, OPTIONAL

## Conformance Tests

Conformance Tests, OPTIONAL
