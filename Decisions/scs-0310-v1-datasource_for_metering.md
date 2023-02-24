---
title: gnocchi as datasource for metering
type: Decision Record
status: Draft
track: IaaS
---


# Introduction

In the past we notice missing events in the telemetry stack of openstack. this results in situations where the Service provider may think that a resource is still in use while the owner shut it down.
Such missing data makes it difficult for the CSP to provide accurate invoices

# Motivation

we want to fill the gab between measuring resource consumption and having reliable data for invoicing.

# Design Considerations

In the first place we want to use as much of the already existing infrastructure as possible.
Also, we want to rely on the already existing APIs as we expect them to be stable over new releases.
If it shows to be insufficient to use certain apis because of high costs we consider to use a direct Information gathering from the services databases.

## Options considered

### using Gnocchi

Gnocchi is already part of the openstack cosmos and has its roots there.
Also, it provides the ability to long term store and offer measures and events.

### using Prometheus

Prometheus is able to store measures only short time. 

### using the openstack services apis and rabbitmq

We would have to provide a storage for historical data and whole in on a gnocchi2

### using the openstack services databases

We would have to provide a storage for historical data and whole in on a gnocchi2

### using data from openstack backends like libvirt, qemu, ceph, ovs/ovn and the hosts filesystem 

That means starting from nearly zero.

# Open questions

* What will be the bottlenecks?
* What will the granularity of the events meta information?



# Decision

We will use gnocchi in the first place

# Related Documents


# Conformance Tests

