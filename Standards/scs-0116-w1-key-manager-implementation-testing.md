---
title: "SCS Key Manager Standard: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0116-v1-key-manager-standard.md
---

## Implementation

A Key Manager service can have different backends.
For Barbican these are called Plugins.
The standard plugin is `simple_crypto`, which has the Master-KEK written in the Barbican config file.
In that case the Master-KEK needs additional protection.
When the `simple_crypto` plugin is used, securing the Master-KEK can be achieved through protection of the Barbican config e.g. through running Barbican in an enclave.

Another option to secure the Master-KEK would be using an HSM with a corresponding plugin in Barbican.
In that case the Master-KEK will be stored inside the HSM and encryption and decryption of the Project-KEKs will also happen in the HSM.
There are also software HSMs available, that should be tested for their integration into the Barbican workflow.

Other Plugins in Barbican are the KMIP plugin and Vault[^1].
They are storing the keys differently and CSPs need to make sure, that the access to the keys is configured securely.

:::tip

Barbican supports deploying out-of-tree drivers what enables operators to satisfy their specific needs.

:::

[^1]:[Barbican Plugins](https://docs.openstack.org/barbican/latest/install/barbican-backend.html)

### Policies

When a Key Manager is used, but it uses the old policies and does not enforce the new secure RBAC work, the roles between Barbican and the other IaaS services differ.
This can be done with a small change in the policy.yaml file. The `creator` has to be defined like this:

```yaml
"creator": "role:member"
```

## Automated Tests

The check for the presence of a Key Manager is done with a test script, that checks the presence of a Key Manager service in the catalog endpoint of Openstack.
This check can eventually be moved to the checks for the mandatory an supported service/API list, in case of a promotion of the Key Manager to the mandatory list.

## Manual Tests

It is not possible to check a deployment for a correctly protected Master KEK automatically from the outside.
Even audits would need to check the complete host for plain-text keys.
CSPs are responsible for ensuring the protection of the Master KEK and they have to make at least their architecture for that protection auditable.
