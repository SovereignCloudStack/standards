---
title: OpenStack API and OpenStack internal Traffic TLS encryption and PKI Infrastructure
type: Decision Record
status: Draft
track: IaaS
---

## Introduction

OpenStack is a platform used for the SCS IaaS layer (Infrastructure as a Service).
Currently, the deployment is mostly done using [Kolla](https://opendev.org/openstack/kolla-ansible).
This ADR document current status of Kolla in regard to end-to-end TLS encryption of selected OpenStack services shown below.
As implementation of most of the following measures is quite straight forward the outcome of this document is divided into two parts.
1. Proposal for implementation of configuration changes in Kolla
2. More common ADR considering adoption of PKI infrastructure.

### Services

This document will focus on the following services as they are the default ones in our IaaS layer.


1. **Keystone** - Keystone is the identity service in OpenStack, responsible for user authentication and authorization and managing domains, projects, and roles.

2. **Horizon** - Horizon is the dashboard of OpenStack, providing a web-based user interface to other services, allowing administrators and users to manage resources and services.

3. **Glance** - Glance is the image service in OpenStack, responsible for discovering, registering, and retrieving virtual machine images.

4. **Cinder** - Cinder is the block storage service, providing persistent block storage resources for virtual machine instances.

5. **Placement** - Placement is a service for tracking resource provider inventories and usages, helping in the efficient allocation of resources across the cluster.

6. **Nova** - Nova is the compute service in OpenStack, responsible for creating and managing virtual machines and compute instances.

7. **Neutron** - Neutron is the networking service providing network connectivity between interface devices managed by other OpenStack services.

8. **Heat** - Heat is the orchestration service, allowing developers to define and deploy composite cloud applications using templates.

9. **Memcached** - Memcached is a caching layer in OpenStack, improving performance by alleviating database load.

10. **MariaDB** - MariaDB is the database backend for OpenStack services, storing and managing data efficiently.

11. **RabbitMQ** - RabbitMQ is the messaging service used in OpenStack for communication between the different components and services.

12. **Redis** - Redis is a database, cache, and message broker within OpenStack, ensuring high-performance data management.

13. **OpenvSwitch** - OpenvSwitch is a multilayer virtual switch implemented to ensure effective network automation in an OpenStack environment.


### Current state

#### Non-internal OpenStack endpoints

##### OpenStack API: External client

```
   EC            --|TLS|--         HA          --|HTTP|--               OS
(External)   (public internet) (HAProxy) (OpenStack Networking)   (OpenStack Services)
   |                                                                  |      |      |
 Client                                                           Keystone  Glance  Placement ...
```

The communication between external clients and the OpenStack services is crucial. It needs to be secured to prevent data leakage and unauthorized access as this data often travels across the open internet, is highly susceptible to interception, and has considerable potential for misuse.

Kolla, out of the box, provides the ability to encrypt external traffic using a HAProxy. [Details](https://docs.openstack.org/kolla-ansible/latest/admin/tls.html#tls-configuration-for-internal-external-vip)

##### OpenStack API: Internal client

```
   IC            --|TLS|--         HA          --|HTTP|--               OS
(Internal) (OpenStack Networking) (HAProxy) (OpenStack Networking)   (OpenStack Services)
   |                                                                  |      |      |
 Client                                                          Keystone  Glance  Placement ...
```

The communication from within the OpenStack is the second most vulnerable communication. This kind of communication usually serves to manage resources from CI/CD tools or services such as the SCS KaaS layer. For the attacker to gain access, they can intercept this kind of communication, for example, from a compromised ci build.

Kolla, out of the box, can encrypt internal traffic using a HAProxy. [Details](https://docs.openstack.org/kolla-ansible/latest/admin/tls.html#tls-configuration-for-internal-external-vip)

##### HAProxy to backend services

```
   EC            --|TLS|--         HA          --|TLS|--                   OS
(External)   (public internet) (HAProxy) (OpenStack Networking)   (OpenStack Services)
   |                                                                  |      |      |
 Client                                                           Keystone  Glance  Placement ...
```

The communication from HAproxy to respective services is much harder to intercept as this traffic is internal to OpenStack; however, here, an attacker is possible from one compromised service to intercept all API traffic. 

Kolla enables end-to-end TLS encryption from HAProxy to services that support TLS Termination, currently out of the services of interest, the following services are supported:

1. Keystone
2. Horizon
3. Glance
4. Cinder
5. Placement
6. Nova
7. Netron
8. Heat
13. OpenVSwitch

Only RabbitMQ is not currently supported.

[Details](https://docs.openstack.org/kolla-ansible/latest/admin/tls.html#back-end-tls-configuration)

#### Backend services to their data services

```
   EC            --|TLS|--         HA          --|TLS|--                   OS             --|TLS|--                  DS
(External)   (public internet) (HAProxy) (OpenStack Networking)   (OpenStack Services)  (OpenStack Networking)  (Data Service)
   |                                                                  |      |      |                            |         |
 Client                                                           Keystone  Glance  Placement ...               MariaDB   Redis ...
```

To provide truly end-to-end traffic encryption within our infrastructure, all communications between services and their respective databases and brokers must be conducted via TLS (Transport Layer Security). This measure not only encrypts the data in transit but also ensures the communication channels are authenticated and integrity-protected.

##### Memcached

Memcached does support TLS; however, this support is only [experimental](https://github.com/memcached/memcached/commit/ee1cfe3bf9384d1a93545fc942e25bed6437d910), and custom build binaries are needed. For our use case, this is a no-go.


##### MariaDB

MariaDB has production-ready support for TLS encryption, and Galera Clusters does also support TLS encryption between nodes. [Details](https://mariadb.com/kb/en/secure-connections-overview/), [Galera Details](https://mariadb.com/kb/en/securing-communications-in-galera-cluster/)

Kolla does not currently support the installation of MariaDB with TLS enabled.

##### RabbitMQ

RabbitMQ does support TLS encryption for connection as well as for inter-node communication. [Details](https://www.rabbitmq.com/ssl.html)

Kolla currently supports encryption of:
* client-server traffic, typically between OpenStack services using the oslo.messaging library and RabbitMQ
* RabbitMQ Management API and UI (frontend connection to HAProxy only)

And does not support encryption of:
* RabbitMQ cluster traffic between RabbitMQ server nodes
* RabbitMQ CLI communication with RabbitMQ server nodes
* RabbitMQ Management API and UI (backend connection from HAProxy to RabbitMQ)

[Details](https://docs.openstack.org/kolla-ansible/latest/reference/message-queues/rabbitmq.html#tls-encryption)

##### Redis

Redis supports TLS encryption for client and inter-node communication; however, this has to be enabled during the build and is not feature-enabled by default.
[Details](https://redis.io/docs/management/security/encryption/)

Kolla currently does not support TLS encryption.

Note: We had issues with `oslo.cache` connecting via TLS to redis, minor upstream change might be needed.

#### Certificate management

Currently, all certificates have to be user-provided, and except for using HTTP-01 [Let's encrypt challenges on the horizon service](https://docs.openstack.org/kolla-ansible/latest/admin/acme.html). With a side note that Kolla provides built-in generation of certificates for development and testing purposes not recommended for production use, [more here](https://docs.openstack.org/kolla-ansible/latest/admin/tls.html#generating-a-private-certificate-authority).

There is a PR almost done to add Let's Encrypt support for generating all certificates. [link](https://review.opendev.org/c/openstack/kolla-ansible/+/741340)

## Motivation

As a part of our ongoing efforts to maintain high-security standards, it's crucial to encrypt the OpenStack API and OpenStack internal communication.

Encrypting this internal traffic adds a strong layer of security. It helps protect our data and operations from potential internal threats. Even if unauthorized individuals gain access to our network, the encrypted communication ensures they cannot understand or misuse the shared data across different services within the cluster.

The purpose of this Decision Record is to outline why we need to encrypt Internal traffic, what solutions are proposed, and what solution we decide to implement for our OpenStack clusters. We will explain the technical considerations, expected benefits, and possible challenges tied to this initiative. as well as a summary of the present status of various services within our ecosystem. This document provides a clear and detailed account of our decision-making process, serving as a helpful reference for any similar security enhancement efforts in the future.

## Proposal for changes in Kolla

In light of the analysis of the current state of TLS within our Kolla-OpenStack environment, several steps are proposed to enhance the security of the Internal traffic within our SCS OpenStack clusters.

### Non-internal OpenStack endpoints

#### OpenStack API: External client :white_check_mark: 

No action is needed.

#### OpenStack API: Internal client :white_check_mark:

No action is needed.

#### HAProxy to backend services :paperclip: 

Implement TLS between HAProxy and RabbitMQ.

### Backend services to their data services

#### Caching / Memcached :construction: 

Considering the experimental nature of TLS support in Memcached, we recommend transitioning to Redis as the caching layer due to its more reliable TLS encryption support. Since Redis can effectively replace all the functions of Memcached, and given that the Redis setup is already in place within Kolla, we propose replacing Memcached with Redis.

#### Database / MariaDB :paperclip: 

Our proposal involves enhancing Kolla to include support for the following:

* Enabling TLS for MariaDB clients
* Allowing MariaDB to accept TLS connections
* Implementing TLS for MariaDB Galera cluster to secure internode connections


#### Message Broker / RabbitMQ :paperclip: 

Since RabbitMQ already has partial TLS support in Kolla, we recommend completing the support by adding the following functionalities:

* Securing RabbitMQ cluster traffic between RabbitMQ server nodes with TLS encryption
* Enabling TLS for RabbitMQ CLI communication with RabbitMQ server nodes
* Establishing TLS encryption for the RabbitMQ Management API and UI, including backend connections from HAProxy to RabbitMQ

#### Caching / Redis :paperclip: 

We propose enhancing Kolla by introducing comprehensive support for Redis TLS. 

### Certificate management :paperclip: 

We recommend identifying, selecting, and implementing a robust certificate management service within your infrastructure. This service will empower users with the capability to issue, rotate, revoke, and efficiently manage their certificates from either private or public Certificate Authorities (CAs). 

Next chapter will focus solely on the certificate managment solution.

## Design Considerations

OPTIONAL

### Options considered

#### Dogtag PKI

Most used and easy to use whole PKI infrastructure automation daemon.

Supports:
* SCEP (Simple Certificate Enrollment Protocol)
* ACME (Automatic Certificate Management Environment).
* OCSP (Online Certificate Status Protocol).

#### OpenVPN Easy-RSA 3

Command line tool for PKI generation does not support any automatic protocols.

#### XiPKI

Supports:
* SCEP (Simple Certificate Enrollment Protocol)
* OCSP (Online Certificate Status Protocol).

#### OpenXPKI

Compared to XiPKI offers more broad range of encryption algorithms and provide more functionalities.

Supports:
* SCEP (Simple Certificate Enrollment Protocol)
* OCSP (Online Certificate Status Protocol).

## Open questions

RECOMMENDED

## Decision

Decision

## Related Documents

Related Documents, OPTIONAL
