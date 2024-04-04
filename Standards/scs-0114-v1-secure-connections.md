---
title: Secure Connections
type: Standard  # | Decision Record | Procedural
status: Draft
track: IaaS  # | IaaS | Ops | KaaS | IAM
---

<!---
This is a template striving to provide a starting point for
creating a standard or decision record adhering to scs-0001.
Replace at least all text which is _italic_.
See https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md
--->

## Introduction

A lot of internal and external connectivity is established to and within a cloud infrastructure.
Due to the nature of the IaaS approach, many communication channels may occasionally or even primarily carry potentially sensitive data of customers.
To protect this data from both tampering and unintended disclosure, communication channels need to be properly secured.

For this reason, [SCS](https://scs.community) standardizes the use of common protection mechanisms for communication channels in OpenStack infrastructures. 

## Motivation

As mentioned above, a lot of communication channels in an OpenStack infrastructure carry data that is potentially sensitive.
For example this includes authentication data of customers and internal OpenStack configuration data such as encryption keys among others.
OpenStack does not generically mandate or preconfigure the use of specific protection mechanisms by itself and instead only makes recommendations about best practices in its offical [Security Guide](https://docs.openstack.org/security-guide/).

To address the potential lack of implementation of such mechanisms by a CSP and to establish a reliable foundation for communication data protection in SCS clouds, SCS formulates this standard for securing communication channels in the infrastructure, so that a customer can rely on adequate security mechanisms being in use.

## Design Considerations

There are many communication channels in OpenStack with different characteristics, location and eligible means of protection.
Not all channels are equally easy to secure and some protection mechanisms might put unbearable burdens on a CSP.
Hence, careful assessment is required to determine for which SCS will either mandate or recommend the use of a protection mechanism.

For this distinction to be made, communication channels must be categorized and classified accordingly.

### Communication Channels

The following overview will classify the main communication channels.

| # | Classification | Details | Example solution |
|---|---|---|---|
| 1 | Database backend traffic | Replication and sync between database instances | SSL/TLS |
| 2 | Database frontend traffic | Communication between OpenStack services and databases | SSL/TLS |
| 3 | Message queue traffic | Message queue communication between OpenStack components as provided by oslo.messaging | SSL/TLS |
| 4 | Internal API communication | HTTP traffic to services registered as internal endpoints in the Keystone service catalog | SSL/TLS |
| 5 | External API communication | HTTP traffic to services registered as external endpoints in the Keystone service catalog | SSL/TLS |
| 6 | Nova VM migration traffic | Nova VM migration data transfer traffic between compute nodes | QEMU-native TLS |
| 7 | Neutron network traffic | Traffic within Neutron SDN networks exchanged between internal systems as well as the outside | IPsec |

### Options considered

#### _Option 1_

Option 1 description

#### _Option 2_

Option 2 description

## Open questions

RECOMMENDED

## Decision

Decision

## Related Documents

- [OpenStack Security Guide](https://docs.openstack.org/security-guide/)
    - [OpenStack Security Guide: Secure communication](https://docs.openstack.org/security-guide/secure-communication.html)
    - [OpenStack Security Guide: Database transport security](https://docs.openstack.org/security-guide/databases/database-transport-security.html)
    - [OpenStack Security Guide: Messaging transport security](https://docs.openstack.org/security-guide/messaging/security.html#messaging-transport-security)
- [Nova Documentation: Secure live migration with QEMU-native TLS](https://docs.openstack.org/nova/latest/admin/secure-live-migration-with-qemu-native-tls.html)

## Conformance Tests

Conformance Tests, OPTIONAL
