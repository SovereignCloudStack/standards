---
title: "SCS Key Manager Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-XXXX-v1-vN-key-manager-standard.md
---

## Implementation

A Key-Manager service can have different backends, for Barbican these are called Plugins.
The standard plugin is `simple_crypto`, which has the Master-KEK written in the Barbican config file.
To secure that Master-KEK when the `simple_crypto` plugin is used it is advised to protect the Barbican config e.g. through running Barbican in an enclave.

Another option to secure the Master-KEK would be using an HSM with a corresponding plugin in Barbican.
In that case the Master-KEK will be stored inside the HSM and encryption and decryption of the Project-KEKs will also happen in the HSM.
There are also software HSMs available, that should be tested for their integration into the Barbican workflow.

Other Plugins in Barbican are the KMIP plugin and Vault[^1].
They are storing the keys differently and CSPs need to make sure, that the access to the keys is configured securely.

[^1]:[Barbican Plugins](https://docs.openstack.org/barbican/latest/install/barbican-backend.html)

## Automated Tests

The check for the presence of a Key Manager is done with a test script, that checks the presence of a Key-Manager service in the catalog endpoint of Openstack.
This check can eventually be moved to the checks for the mandatory an supported service/API list, in case of a promotion of the key-manager to the mandatory list.

## Manual Tests

There needs to be a manual test that searches the physical host of the Key-Manager host for the presence of a Master-KEK in Plain-Text, e.g. in the Barbican config file.
