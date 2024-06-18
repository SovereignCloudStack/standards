---
title: Key-Manager Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

To encrypt user data like volumes or in the future also Images and ephemeral storage for VMs, the key is need to be known in the infrastructure.
To provide the key to those operations without including the user every time a Key Manager within the infrastructure can be utilized to store the keys and apply authorization policies on requests.
OpenStack offers a Key Manager implementation that is named Barbican, which provides these features.
This standard aims to provide a base level of security for Cloud Service Providers that integrate a Key Manager into their deployments.

## Terminology

| Term | Meaning |
|---|---|
| API | Application Programming Interface, often referring to the REST API interfaces provided by OpenStack and related services |
| Barbican | The Key Manager implementation in OpenStack |
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| IaaS | Infrastructure-as-a-Service |
| HSM | Hardware Security Module |
| KEK | Key Encryption Key |

## Motivation

User data encryption requires an encryption key to be known during encryption and decryption processes.
Key Managers like Barbican provide this functionality on the IaaS-Level.
Not every IaaS deployment currently offers user data encryption as part of their standard offering.
A first step towards more security is to encourage CSPs to provide better data security by offering data encryption to the customers.
It is also important to take a closer look into the Key Manager and to apply aim for an appropiate level of security there.
The Key Manager service manages keys in a secure manner.
This can be achieved differently and is not primarily in scope of this standard.
Barbican stores keys encrypted with the project specific KEK, including the KEK itself, in the database.
The Master-KEK, used to encrypt the project specific KEKs is not stored in the database and is stored differently depending on the backend storage plugin used.
This standard also abstracts the used plugins and wants to ensure that the Master-KEK is protected, too.

## Design Considerations

While discussing what this standard should aim for it was discovered that some CSPs don't use Barbican or another Key Manager at all and do not provide the feature to encrypt user data to their customers.
This should change, but the exact change comes with financial burden, when choosing a plugin in Barbican to store the Master-KEK.
To minimize the burden and enable more CSPs to step up and provide encryption, this standard will only make recommendations about plugins.

### Options considered

#### _Option 1_

It was considered to only recommend a certain set of plugins or backends for the Key Manager, but this may be very prone to change if e.g. Barbican adds a new plugin.
As the SCS only wants to mandate the API that can be abstracted through the Castellan library in OpenStack, integrating any other Key Manager implementation is not uncommon, so this standard needs to consider other possible Key Managers as well.
Due to these reasons this option was disregarded.

#### _Option 2_

Looking into the available Barbican plugins and possible attack vectors one design decision in the plugins is very important: where and how to store the Master-KEK.
Because the Plugins might use different technologies, but most of them increase the security level by not storing the Master-KEK in plain text on the physical machine Barbican is running on.
This mechanism as a whole, is something that CSPs should aim to do.

## Standard

To increase the level of security and overall user data encryption CSPs SHOULD implement the Key Manager API (e.g. implemented by Barbican) with a security level of storing Keys encrypted and storing the Master-KEK in another place than the Keys.

If possible CSPs SHOULD NOT store the Master-KEK in plain-text on the physical host the Key Manager is running on.

## Related Documents

[Barbican Plugins](https://docs.openstack.org/de/security-guide/secrets-management/barbican.html)

## Conformance Tests

Conformance must be tested in two steps.

1. The check whether a Key Manager is present can be done in a similar way as in the mandatory OpenStack service APIs standard and the test should be merged into the mandatory service test as soon as a Key Manager is required in scs-conformant infrastructures.
2. The check, that there is no Master-KEK present on the Key Manager Node, has to be done by the CSP themself.
