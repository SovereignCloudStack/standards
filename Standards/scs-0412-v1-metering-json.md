---
title: Exposition of IaaS metering data as JSON
type: Standard
status: Draft
track: Ops
---

## Introduction

The Sovereign Cloud Stack project intends to standardise an infrastructure-as-a-service (IaaS) layer.
In order to economically sustainably run a cloud,
it is generally useful to know which user or tenant consumes which amount of resources in which time frame.

Similarly to how the SCS provides an interface for connecting monitoring services to detect outages,
this standard aims for providing an interface for connecting systems which aggregate customer resource usage.

## Motivation

In general,
users of the SCS (i.e. cloud operators) may already have different systems in place
for tracking customer relationships
as well as billing.

Those systems are unlikely to have a uniform interface across all possible implementations.
Likewise, those systems are unlikely to have a way to interface with OpenStack,
the reference IaaS layer in SCS.

In order to provide SCS operators with a way to integrate the SCS IaaS layer with their billing,
this document shall provide a standard format,
upon which shim conversion layers (to whichever billing system is in place)
can be built.

## Design Considerations

In order to define a standard,
the various options for formats need to be considered.
However, all formats also come with different implementation costs.

These aspects are weighed in this section.

### Options considered

#### Use Ceilometer HTTP hook format

The OpenStack Ceilometer project,
which serves as a hub for all things telemetry and metering,
provides an HTTP-based hook to extract metering data.
This hook receives JSON-formatted data.

Using this data has the advantage
that we do not need to implement another component to translate the format
which may in turn be a point of failure.

#### Use another format

In this option,
a format for metering data is researched and reused, or defined and specified by the SCS project.

This option was not explored deeply, for the reasons explained in the decision.

## Open questions

None.

## Decision

We chose the Ceilometer HTTP hook format, described below, for the following reasons:

- Ceilometer is a component which needs to be there anyway for successful metering of OpenStack. Re-using the format makes sense.
- Using any other format requires a translation layer. However, users will likely need their own translation layer *anyway*, to integrate the metering with their own infrastructure. Hence, it makes more sense to expose the data from Ceilometer directly.

  A notable downside of this approach is that a change in Ceilometers format will inevitably cause issues in all downstream consumers.

## Related Documents

- SCS-0410-v1
- SCS-0411-v1

## Conformance Tests

None.
