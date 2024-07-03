---
title: Key Manager Standard
type: Standard
status: Draft
track: IaaS
---

## Introduction

To encrypt user data like volumes or in the future also Images and ephemeral storage for VMs, the key has to be present in the infrastructure.
A Key Manager service within the infrastructure can be utilized to store keys.
Consequently providing keys for every encryption or decryption is possible without including the user.
Also authorization policies can be applied on every request to the Key Manager servicer.
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
| RBAC | Role Based Access Control |

## Motivation

User data encryption requires an encryption key to be known during encryption and decryption processes.
Key Managers like Barbican provide this functionality on the IaaS-Level.
Not every IaaS deployment currently offers user data encryption as part of their standard offering.
This standard should encourage CSPs to integrate a Key Manager and thus increase the amount of Clouds witch offerings of data encryption.
It is also important to take a closer look into the Key Manager and analyze how such a service can be configured securely.

A Key Manager service manages keys in a secure manner, but this can be achieved differently and is not primarily in scope of this standard.
The OpenStack Key Manager Barbican stores keys encrypted with the project specific KEK, including the KEK itself, in the database.
The Master-KEK, used to encrypt the project specific KEKs is not stored in the database and is stored differently depending on the backend storage plugin used.
This standard also abstracts the used plugins and wants to ensure that the Master-KEK is protected, too.

## Design Considerations

While discussing what this standard should aim for it was discovered that some CSPs don't use Barbican or another Key Manager at all and do not provide the feature to encrypt user data to their customers.
This should change, but the exact change comes with financial burden, when choosing a plugin in Barbican to store the Master-KEK.
To minimize the burden and enable more CSPs to step up and provide encryption, this standard will only make recommendations about plugins.

### Options considered

#### Recommend or even mandate specific Key Manager plugins

It was considered to only recommend a certain set of plugins or backends for the Key Manager, but this may be very prone to change if e.g. Barbican adds a new plugin.
As the SCS only wants to mandate the API that can be abstracted through the Castellan library in OpenStack, integrating any other Key Manager implementation is not uncommon, so this standard needs to consider other possible Key Managers as well.
Due to these reasons this option was disregarded.

#### Recommendation regarding the handling of the Master KEK

Looking into the available Barbican plugins and possible attack vectors one design decision in the plugins is very important: where and how to store the Master-KEK.
Because the Plugins might use different technologies there are many locations for the Master KEK possible.
Most of the Plugins increase the security level by not storing the Master-KEK in plain text on the physical machine Barbican is running on.
This mechanism as a whole, is something that CSPs should aim to do.

#### Standardization of the Key Manager Policy

Because this standards recommends or even eventually mandates the presence of a Key Manager, the situation about the policy of the Key Manager needs to be discussed.
The policy of an IaaS service should use the same roles as the other IaaS services.
Unfortunately this does not apply to the Key Manager implementation Barbican.
It has the roles 'reader', 'audit' and 'creator', which are not present in the Keystone role concept.
The roles a customer usually gets through the Identity API is 'member'.
Leaving it this way will prevent users from creating and using secrets even when a Key Manager is integrated.

To unify the roles among all IaaS services, there is currently work done in the OpenStack Community.
This initiative is called secure RBAC[^1].
Also the SCS is discussing a standard concerning the roles[^2].
When this is done, there is no further work needed.
But as of the 2024.1 release, this is still under development.

In conclusion this standard should mandate everyone who uses a Key Manager that does not include the secure RBAC, to adjust the policies to have a mapping between the internal 'creator' and the identity-based 'member' role.
This will result in a 'member' being allowed to do everything a 'creator' can do.

[^1]: [Secure RBAC work in OpenStack](https://etherpad.opendev.org/p/rbac-goal-tracking)
[^2]: [Issue for a role standard in SCS](https://github.com/SovereignCloudStack/issues/issues/396)
 
## Key Manager Standard

To increase security and allow user data encryption, CSPs SHOULD implement the Key Manager API (e.g. implemented by Barbican).
The Keys managed by this Key Manager MUST be stored encrypted and the Master-KEK of the Key Manager MUST be stored in another place than the Keys.

If possible CSPs SHOULD NOT store the Master-KEK in plain-text on the physical host the Key Manager is running on.

### Key Manager Policies

If a Key Manager without secure RBAC enabled is used, the policies MUST be adjusted to let the 'member' role of the Identity service be equivalent to the Key Manager internal 'creator' role.

## Related Documents

[Barbican Plugins](https://docs.openstack.org/de/security-guide/secrets-management/barbican.html)

## Conformance Tests

Conformance must be tested in two steps.

1. The check whether a Key Manager is present can be done in a similar way as in the mandatory OpenStack service APIs standard and the test should be merged into the mandatory service test as soon as a Key Manager is required in scs-conformant infrastructures.
2. The check, that there is no Master-KEK present on the Key Manager Node, has to be done by the CSP themself.
