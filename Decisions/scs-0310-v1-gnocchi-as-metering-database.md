---
title: Gnocchi as database for metering
type: Decision Record
status: Draft
track: IaaS
---

<!-- This file uses semantic linebreaks. See <https://sembr.org/> for more info. -->

# Introduction

In the past we noticed missing events in the telemetry stack of OpenStack.
This results in situations where the Cloud Service Provider (CSP)
may think that a resource is still in use while the owner shut it down,
or may not be aware of a resource which has been created.

Such inaccurate data is a problem,
when it is supposed to be used for billing purposes.

This document discusses how such metering data should be stored
within the SCS.
In partiuclar,
it provides rationale for the choice of Gnocchi
as time-series database for metering data
within SCS.

# Definitions

- TSDB, time-series database:
  Database which is specialised for storing data which is keyed by a timestamp.
  Popular examples are InfluxDB, Graphite, rrd, and Prometheus.

- Metering:
  Collection of usage data of a cloud,
  for the specific purpose of creating invoices
  to bill customers for the resources they have allocated.

- backfilling:
  The process of adding and modifying data in the past
  within a time-series database.

- Metric:
  A single time-series vector.
  Typically, a metric represents a single property of a resource,
  such as CPU usage of an instance.

- Resource metrics:
  A group of metrics belonging to a single resource.
  A compute instance, for instance,
  may have a metric indicating the number of CPUs allocated,
  another metric indicating the amount of RAM allocated,
  etc.

# Motivation

Being able to hold users accountable
for the resources they use
is a prerequisite for commercially operating a cloud.
The SCS project wants to deliver a cloud stack
which can be used for that purpose,
hence providing reliable metering data is a requirement.

As metering data is inherently keyed by time,
a time-series database is required.
The choice of time-series database is an important one
as different databases come with different trade-offs.
Not all databases are suitable for the kind of data
which is collected in a metering context.

# Design Considerations

The following requirements for a time-series database exist:

- MUST support backfilling:
  As we need to catch up on changes to resources
  which may have happened during a brief network interruption,
  we need to be able to modify data after it has been written to the TSDB.

- MUST be able to handle lots of resources:
  As billing should happen with a resource-level granularity,
  we expect a lot of different metrics inside the TSDB.

- MUST scale to different timescales:
  We expect to have metrics which change frequently (e.g. object store usage)
  and metrics which change rarely (e.g. cinder volume sizes).
  The TSDB must be able to cope with both types of metrics efficiently.

- SHOULD provide an efficient way to query all currently alive resources.

- SHOULD allow truncation of storage to remove old data.

- MUST be available under an appropriate Open Source license,
  even for productive use cases.

## Options

### Using Gnocchi

[Gnocchi](https://gnocchi.osci.io/) is a time-series database
which has its origins in the OpenStack ecosystem.

It supports all requirements except truncation,
which might have to be implemented.

### Using Prometheus

[Prometheus](https://prometheus.io) is a widely used time-series database
with its focus on monitoring and incident response.
While it is considered efficient for this use-case,
it has shortcomings which make it unsuitable for the metering use case:

- Explicit recommendation [against high-cardinality metrics](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels):
  As we would have to label metrics by resource IDs and project IDs,
  we have to expect a very high cardinality,
  also with a significant amount of metric churn.

- Backfilling, [albeit possible](https://prometheus.io/docs/prometheus/latest/storage/#backfilling-from-openmetrics-format), is not well-supported.

### Using InfluxDB

[InfluxDB](https://www.influxdata.com/) is a widely used time-series database
with its focus on monitoring.

In contrast to Prometheus, it does support backfilling.
However, like Prometheus,
it seems to run [into scalability issues in high-cardinality scenarios](https://docs.influxdata.com/influxdb/cloud/write-data/best-practices/resolve-high-cardinality/).

In addition,
clustering is only available in commercial licensing options.

### Creating a custom TSDB implementation

A custom TSDB implementation
is a non-trivial project to pursue.

## Decision

We use Gnocchi.
According to research,
it mostly fulfills the requirements.
While some small development efforts may be needed,
to make it fully usable,
the amount of work is anticipated much less
than making Prometheus or Influx fit the bill
(due to backfilling / cardinality scaling constraints),
let alone rolling a custom implementation.

### Open questions

* What will the granularity of the events meta information?

  If we decide to use resource metadata
  as a place to store slow-changing information
  (e.g. instance flavors, volume sizes),
  we need to know what the granularity of that is.

# Related Documents

None yet.

# Conformance Tests

None (this is a decision record).
