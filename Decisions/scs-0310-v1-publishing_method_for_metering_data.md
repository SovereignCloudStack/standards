---
title: pushing as publishing method for metering
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
We want to be fast and efficient. in implementing the metering project also as in the daily usage of the provided data.

## Options considered

### building an REST-api

We need to define a REST-Api structure.
The CSP has to implement requests against this API.

### pushing Daisies

We will send all new data as fast as we can reconcile there origin and in a simple manner to a defined sink.
A CSP only has to implement its own method for sending to a sink if it is not already supported.

# Open questions

What is necessary to extend the availability of sending to various sinks?
How does the configuration look like that is needed to push to a sink from the same type that will be already implemented?



# Decision

We will go the pushing way.

# Related Documents


# Conformance Tests

