---
title: Secure Connections
type: Standard  # | Decision Record | Procedural
status: Draft
track: IaaS  # | IaaS | Ops | KaaS | IAM
---

## Introduction

A lot of internal and external connectivity is established to and within a cloud infrastructure.
Due to the nature of the IaaS approach, many communication channels may occasionally or even primarily carry potentially sensitive data of customers.
To protect this data from both tampering and unintended disclosure, communication channels need to be properly secured.

For this reason, the [SCS project](https://scs.community) standardizes the use of common protection mechanisms for communication channels in OpenStack infrastructures.

### Glossary

| Term | Meaning |
|---|---|
| CSP | Cloud Service Provider, provider managing the OpenStack infrastructure |
| SSL | Secure Sockets Layer, the predecessor of TLS |
| TLS | Transport Layer Security |
| PKI | Public Key Infrastructure |
| SDN | Software-Defined Networking |

## Motivation

As mentioned above, a lot of communication channels in an OpenStack infrastructure carry data that is potentially sensitive.
For example this includes authentication data of customers and internal OpenStack configuration data such as encryption keys among others.
OpenStack does not generically mandate or preconfigure the use of specific protection mechanisms by itself and instead only makes recommendations about best practices in its offical [Security Guide](https://docs.openstack.org/security-guide/).

To address the potential lack of implementation of such mechanisms by a CSP and to establish a reliable foundation for communication data protection in SCS clouds, the SCS project formulates this standard for securing communication channels in the infrastructure, so that a customer can rely on adequate security mechanisms being in use.

## Design Considerations

There are many internal communication channels in OpenStack with different characteristics, location and eligible means of protection.
Not all channels are equally easy to secure and some protection mechanisms might put unbearable burdens on a CSP.
Hence, careful assessment is required to determine for which the SCS standard will either mandate or recommend the use of a protection mechanism.

Note that this standard only focuses on security considerations for securing the Openstack API as well as inter-component connections, which a CSP has full control over on an infrastructure level.
This standard will not address the security of customer-deployed instances and services on top of OpenStack or other IaaS implementations.

For this distinction to be made, applicable communication channels must be categorized and classified accordingly.

### Communication Channels

The following overview will classify the main communication channels.

| # | Classification | Details | Example solution |
|---|---|---|---|
| 1 | OpenStack database backend traffic | Replication and sync between database instances of the OpenStack services' databases | SSL/TLS |
| 2 | OpenStack database frontend traffic | Communication between OpenStack services and their corresponding databases | SSL/TLS |
| 3 | Message queue traffic | Message queue communication between OpenStack components as provided by oslo.messaging | SSL/TLS |
| 4 | External API communication | HTTP traffic to services registered as external endpoints in the Keystone service catalog | SSL/TLS |
| 5 | Internal API communication | HTTP traffic to services registered as internal endpoints in the Keystone service catalog | SSL/TLS |
| 6 | Nova VM migration traffic | Nova VM migration data transfer traffic between compute nodes | QEMU-native TLS |
| 7 | External Neutron network traffic | VM-related traffic between the network/controller nodes and external networks (e.g. internet) established through routed provider networks and floating IPs | VPN |
| 8 | Internal Neutron network traffic | Traffic within Neutron SDN networks exchanged between internal systems such as network/controller and compute nodes | WireGuard |

Notes about the classification categories and implications:

1. Most database clustering solutions (e.g. MariaDB Galera) offer TLS-based encryption of their backend channels. This needs no additional configuration in OpenStack and is a configuration solely concerning the database cluster.
2. The database frontend interface is the primary connection target for the OpenStack services. OpenStack supports using TLS for database connections.
3. For the message queue, AMQP-based solutions such as RabbitMQ and QPid do offer TLS natively which is also supported by OpenStack. ZeroMQ does not and requires WireGuard or CIPSO instead.
4. External API endpoints can be protected easily by using a TLS proxy. They can then be registered with their HTTPS endpoint in the Keystone service catalog. The certificates of external APIs usually need to be signed by a well-known CA in order to be accepted by arbitrary external clients.
5. Internal API endpoints can be treated and secured similarly to the external ones. Optionally, the TLS certificate provider and PKI can differ to the external ones. It is often sufficient for the CA of internal TLS endpoints to be accepted within the infrastructure and doesn't need to be a common public CA.
6. For protecting the data transferred between compute nodes during live-migration of VMs, [Nova offers support for QEMU-native TLS](https://docs.openstack.org/nova/latest/admin/secure-live-migration-with-qemu-native-tls.html). As an alternative, SSH is also a channel that Nova can be configured to use between hosts for this but requires passwordless SSH keys with root access to all other compute nodes which in turn requires further hardening.
7. Neutron's external network traffic leaves the IaaS infrastructure. This part is twofold: connections initiated by the VMs themselves (egress) and connections reaching VMs from the outside (ingress). The CSP cannot influence the egress connections but can offer VPNaaS for the ingress direction.
8. Neutron's internal network traffic is one of the hardest aspects to address. Due to the highly dynamic nature of SDN, connection endpoints and relations are constantly changing. There is no holistic approach currently offered or recommended by OpenStack itself. Encrypted tunnels could be established between all involved nodes but would require a scalable solution and reliable key management. WireGuard could be considered a good starting point for this. A per-tenant/per-customer encryption remains very hard to establish this way though.

### Options considered

#### Option 1: fully mandate securing all channels without differentiation

This option would reach the highest security standard and establish protection on all identified communication channels simultaneously.
However, this would burden CSPs greatly due to the difficulty of addressing some of the channels and properly maintaining the solution.
Also there is a risk of making this incompatible with existing infrastructures due to some of their specifics being mutually exclusive to the more intricate protection mechanisms such as cross-node WireGuard configurations.
As a third aspect, not all mechanisms might fulfill the CSPs requirements regarding performance and stability and the SCS standard cannot in good faith force CSPs to use technologies not suited to their infrastructures.

This seems like a bad option from many perspectives.
It also allows very little flexibility and might even make SCS conformance unappealing to CSPs due to the immense effort required to reach it.

#### Option 2: only make recommendations

This option would limit the SCS project to only recommend mechanisms in this standard like presented in the OpenStack Security Guide.
Although this can increase awareness about the best practices recommended by OpenStack and maybe encourage CSPs to abide by them, it would actually contribute very little to the security baseline of SCS infrastructures as a whole since everything would stay optional.

This option would be very easy to standardize and get consensus on due to its lightweight and optional nature.
However, the actual added value for SCS is questionable at best.

#### Option 3: mix recommendations and obligations

This option forms a middle ground between options 1 and 2.
For this, the standard needs to carefully assess each communication channel, mechanisms for protecting it and the effort required to do so as well as the implications.
Then, only for mechanisms that are known to be reliable, are feasible to implement and for which the benefits clearly outweigh the integration effort required, should this standard enforce their implementation in a permissive way.
For any remaining mechanisms the SCS standard should only make recommendations and refer to known best practices where applicable.

This option would still offer improvements over arbitrary OpenStack clouds by establishing a baseline that goes beyond mere recommendations while still taking into account that not all communication channels are equally easy to secure and allowing necessary flexibility for the CSP.

## Open questions

### Verifying standard conformance for internal mechanisms

Most of the mentioned communication channels to be secured are part of the internal IaaS infrastructure of a SCS cloud.
When an internal protection mechanism is implemented by the CSP it cannot be verified from outside of the infrastructure without administrative access to the infrastructure.

Thus, the SCS community is unable to fully assess a CSPs conformance to this standard without a dedicated audit of the infrastructure.

## Decision

This standard will mandate or recommend appropriate measures for securing the communication channels based on existing standards and recommendations.
It will reference documents like the [OpenStack Security Guide](https://docs.openstack.org/security-guide/) where applicable.

### Transport Layer Security (TLS)

All server-side TLS configurations integrated into the infrastructure as covered by this standard MUST adhere to the folllowing rules:

- The following deprecated TLS versions MUST NOT be used:
  - v1.0
  - v1.1
- The following cipher suites MUST NOT be used:
  - any RC4 cipher suite
  - any DES cipher suite
  - any cipher suite involving MD5 hash algorithms
  - any cipher suite with less than 128-bit encryption
- Cipher suites utilizing CBC mode SHOULD NOT be used
- Cipher suites with Perfect Forward Secrecy (using ephemeral keys with the 'E' suffix, e.g. DHE, ECDHE) SHOULD be used instead of their static key counterpart (e.g. DH, ECDH)

### API Interfaces

- Internal API endpoints of all OpenStack services MUST use TLS. Their endpoint as registered in the Keystone service catalog MUST be an HTTPS address.
- External API endpoints of all OpenStack services MUST use TLS. Their endpoint as registered in the Keystone service catalog MUST be an HTTPS address.

You MAY refer to [TLS proxies and HTTP services](https://docs.openstack.org/security-guide/secure-communication/tls-proxies-and-http-services.html) and [Secure reference architectures](https://docs.openstack.org/security-guide/secure-communication/secure-reference-architectures.html) of the OpenStack Security Guide for best practices and recommendations.

### Database Connections

- The database servers used by the OpenStack services MUST be configured for TLS transport.
- All OpenStack services MUST have TLS configured for the database connection via the `ssl_ca` directive. See [OpenStack service database configuration](https://docs.openstack.org/security-guide/databases/database-access-control.html#openstack-service-database-configuration).
- Database user accounts for the OpenStack services SHOULD be configured to require TLS connections via the `REQUIRE SSL` SQL directive. See [Require user accounts to require SSL transport](https://docs.openstack.org/security-guide/databases/database-access-control.html#require-user-accounts-to-require-ssl-transport).
- Security MAY be further enhanced by configuring the OpenStack services to use X.509 client certificates for database authentication. See [Authentication with X.509 certificates](https://docs.openstack.org/security-guide/databases/database-access-control.html#authentication-with-x-509-certificates).

### Message Queue Connections

- If using RabbitMQ or Qpid as the message queue service, the SSL functionality of the message broker MUST be enabled and used by the OpenStack services. See [Messaging transport security](https://docs.openstack.org/security-guide/messaging/security.html#messaging-transport-security).
  - If using RabbitMQ, the OpenStack services' oslo.messaging configuration for RabbitMQ MUST use the `kombu_ssl_*` options accordingly to enable SSL.
  - If using Qpid, the OpenStack services' oslo.messaging configuration for Qpid MUST set the `qpid_protocol` option to `ssl` to enable SSL.
- If using Apache Kafka, the server listener MUST be configured to accept SSL connections. See [Apache Kafka Listener Configuration](https://kafka.apache.org/documentation/#listener_configuration).
  - The OpenStack services' oslo.messaging configuration for Kafka MUST specify `security_protocol` as either `SSL` or `SASL_SSL` and the related options appropriately. See [Kafka Driver Options](https://docs.openstack.org/oslo.messaging/latest/admin/kafka.html#driver-options).

### Hypervisor and Live Migration Connections

- If using libvirt on compute nodes, the libvirt port (as per `listen_addr`) MUST NOT be exposed to the network in an unauthenticated and unprotected fashion. It SHOULD be bound to `127.0.0.1`.
- If QEMU and libvirt are used as the hypervisor interface in Nova, QEMU-native TLS SHOULD be used. See [Secure live migration with QEMU-native TLS](https://docs.openstack.org/nova/latest/admin/secure-live-migration-with-qemu-native-tls.html).

### External VM Connections

- As an OPTIONAL measure to assist customers in protecting external connections to their OpenStack networks and VMs, the infrastructure MAY provide VPNaaS solutions to users.
  - For example the Neutron VPNaaS service MAY be integrated into the infrastructure with the Neutron VPNaaS API extension enabled. See the [Neutron VPNaaS documentation](https://docs.openstack.org/neutron-vpnaas/latest/).

### Internal Neutron Connections

- As an OPTIONAL measure to protect Neutron SDN traffic between physical nodes within the infrastructure, encrypted tunnels MAY be established between nodes involved in Neutron networks, such as compute and network controller nodes, at the network interfaces configured in Neutron (e.g. via WireGuard or similar solutions).

## Related Documents

- [OpenStack Security Guide](https://docs.openstack.org/security-guide/)
  - [OpenStack Security Guide: Secure communication](https://docs.openstack.org/security-guide/secure-communication.html)
  - [OpenStack Security Guide: Database transport security](https://docs.openstack.org/security-guide/databases/database-transport-security.html)
  - [OpenStack Security Guide: Messaging transport security](https://docs.openstack.org/security-guide/messaging/security.html#messaging-transport-security)
- [Nova Documentation: Secure live migration with QEMU-native TLS](https://docs.openstack.org/nova/latest/admin/secure-live-migration-with-qemu-native-tls.html)
- [Guide to TLS Standards Compliance](https://www.ssl.com/guide/tls-standards-compliance/)

## Conformance Tests

Conformance tests are limited to communication channels exposed to users, such as the public API interfaces.

There is a test suite in [`tls-checker.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/secure-connections/tls-checker.py).
The test suite connects to the OpenStack API and retrieves all public API endpoints from the service catalog.
It then connects to each endpoint and verifies the compliance to the standard by checking SSL/TLS protocol versions and cipher suites offered by the server against the guidelines of this standard.
Please consult the associated [README.md](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/secure-connections/README.md) for detailed setup and testing instructions.
