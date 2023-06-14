---
title: Push-based approach for providing usage data
type: Decision Record
status: Draft
track: Ops
---

<!-- This file uses semantic linebreaks. See <https://sembr.org/> for more info. -->

## Introduction

In the past we noticed missing events in the telemetry stack of OpenStack.
This results in situations where the Cloud Service Provider (CSP)
may think that a resource is still in use while the owner shut it down,
or may not be aware of a resource which has been created.

Such inaccurate data is a problem,
when it is supposed to be used for billing purposes.

This document discusses how such metering data should be made available
to the cloud service provider
for forwarding into their own billing solution.

## Definitions

- Push-based flow:
  In a push-based flow,
  the system generating data actively sends that data to a consumer.

- Pull-based flow:
  In a pull-based flow,
  the system generating data waits for the system consuming the data
  to ask for that data.

- Metering:
  Collection of usage data of a cloud,
  for the specific purpose of creating invoices
  to bill customers for the resources they have allocated.

- Billing:
  The entire process of creation, management and sending of invoices
  generated from metering data.

## Motivation

Being able to bill users
for the resources they use
is a prerequisite for commercially operating a cloud.
The SCS project wants to deliver a cloud stack
which can be used for that purpose,
hence providing reliable metering data is a requirement.

We generally expect that cloud providers already have
some kind of customer-relation management or billing system in place.
Hence, it is important that the SCS is not too opinionated
on this implementation detail,
but provides a system which can easily interface with other systems.

This is similar to how the SCS specified the monitoring stack.

## Design Considerations

The following requirements exist for the process for providing metrics to the cloud service provider:

- MUST scale to different timescales:
  We expect to have metrics which change frequently (e.g. object store usage)
  and metrics which change rarely (e.g. cinder volume sizes).

### Options

#### Push-based flow

In a push-based flow,
the to-be-implemented metering system pushes events to the sink
as soon as it is reasonably confident
that the event can be used for billing purposes.

#### Poll-based flow

In the poll-based flow,
whichever system the CSP runs would be responsible for polling the metering API
in a frequency sufficient to capture all data with sufficient granularity.

## Open questions

- What is necessary to extend the availability of sending to various sinks?
- How does the configuration look like that is needed to push to a sink from the same type that will be already implemented?

## Decision

As we need to support very different time scales of data,
the push-based flow is more suitable:
it allows the producer of the data,
which knows about the interval in which it changes,
when to provide new data to the consumer.
In contrast to that,
a poll-based flow would need the consumer to know about change intervals,
or alternatively poll in the highest change frequency ever expected.

## Related Documents

- SCS-0410-v1

## Conformance Tests

None (this is a decision record).
