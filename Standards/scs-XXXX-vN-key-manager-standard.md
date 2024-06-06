---
title: Key-Manager Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

To encrypt user data like volumes or in the future also Images and ephemeral storage for VMs, the key is needed to be present in the infrastructure.
Therefore a key-manager is needed to store the keys and apply authorization policies on requests.
The OpenStack key-manager implemenation that can bu utilized for this is named Barbican.
This standard aims to provide a base level of security for Cloud Service Providers that integrate a key-manager into their deployments.

## Terminology

| Term | Meaning |
|---|---|
| API | Application Programming Interface, often referring to the REST API interfaces provided by OpenStack and related services |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| IaaS | Infrastructure-as-a-Service |
| HSM | Hardware Security Module |
| KEK | Key Encryption Key |

## Motivation

When user data is encrypted the keys need to be stored securely in the Infrastructure to be present, when a possible encryption or decryption needs to take place.
Key-managers like Barbican provide this functionality on the IaaS-Level.
Using such a key-manger and thus provide to customers the possibility to encrypt user data is not yet implemented everywhere in IaaS deployments.
A first step towards more security is to encourage CSPs to use this service and provide the feature of using encrypted resources to customers.
It is also important to take a closer look into the key-manager and to apply aim for an appropiate level of security there.
The Key-Manager is responsible for storing the keys securely, which can be done by encrypting them with a KEK and storing them in a database and store the KEK either also encrypted in the database or to store it somewhere else.
Barbican as the OpenStack implementation of a key-manager is relying on a Master-KEK, which encrypts project-specific KEKs, which encrypt the Keys within a project.
All keys except for the Master-KEK are stored in a database.
This Master-KEK is stored differently for each plugin and needs to be protected.

## Design Considerations

While discussing what this standard should aim for it was discovered that some CSPs don't use Barbican or another key-manager at all and do not provide the feature to encrypt user data to their customers.
This should change, but the exact change comes with financial burden, when choosing a plugin in Barbican to store the Master-KEK.
To minimize the burden and enable more CSPs to step up and provide encryption, this standard will only make recommendations about plugins.

### Options considered

#### _Option 1_

It was considered to only recommend a certain set of plugins or backends for the key-manager, but this may be very prone to change if Barbican adds a new plugin.
As the SCS only wants to mandate the API that can be abstracted through the Castellan library in OpenStack, integrating any other key-manager implementation is not uncommon, so this standard needs to consider other possible key-managers as well.
Due to these reasons this Option was disregarded.

#### _Option 2_

Looking into the plugins and possible attack vectors one design decision in the plugins is very important: where and how to store the Master-KEK.
Because the Plugins might use different technologies, but most of them increase the security level by not storing the Master-KEK in plain text on the physical machine Barbican is running on.
This mechanism as a whole, is something that CSPs should aim to do.

## Standard

To increase the level of security and overall user data encryption CSPs SHOULD implement the key-manager API (e.g. implemented by barbican) with a security level of storing Keys encrypted and storing the KEK in another place than the Keys.

If possible CSPs SHOULD NOT store the Master-KEK in plain-text on the physical host the key-manager is running on.

## Related Documents

[Barbican Plugins](https://docs.openstack.org/de/security-guide/secrets-management/barbican.html)

## Conformance Tests

Conformance must be tested in two steps.

1. The check whether a key-manager is present can be done in a similar way as in the mandatory OpenStack service APIs standard and the test should be merged into the mandatory service test as soon as a key-manager is required in scs-conformant infrastructures.
2. The check, that there is no Master-KEK present on the Barbican Node, has to be done by the CSP themself.
