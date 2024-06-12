---
title: "SCS Key Manager Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-XXXX-v1-vN-key-manager-standard.md
---

## Implementation

A Key-Manager can have different backends, for Barbican there are called Plugins.
The standard plugin is simple crypto, which has the Master-KEK written in the Barbican config file.
To secure that Master-KEK it is advised to protect the Barbican config e.g. through running Barbican in an enclave.

Another option to secure the Master-KEK would be using an HSM with a corresponding plugin in Barbican.
In that case the Master-KEK will be stored inside the HSM and encryption and decryption of the Project-KEKs will also happen in the HSM.
There are also software HSMs available, that should be tested for their integration into the Barbican workflow.

## Automated Tests

The check for the presence of a Key Manager is done with an test script, that checks the presence of a key manager service in the catalog endpoint of openstack.
This check can eventually be moved to the checks for the mandatory an supported service/API list, in case of a promotion of the key-manager to the mandatory list.

## Manual Tests

There need to be a manual test that searches the physical host of the Key-Manager host for the present of a Master-KEK in Plain-Text, e.g. in the Barbican config file.
