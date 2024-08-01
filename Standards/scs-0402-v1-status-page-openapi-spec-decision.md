---
title: Status page OpenAPI decision
type: Decision Record
status: Draft
track: Ops
---

## Introduction

While defining the [OpenAPI spec](https://github.com/SovereignCloudStack/status-page-openapi) some considerations and decisions are made and should be documented.

## Requirements

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

In addition, "FORBIDDEN" is to be interpreted equivalent to "MUST NOT".

## Motivation

The spec should be as minimal as possible, while being as understandable as possible, so some choices to the design of API objects, requests and responses are made.

## Decision

### Common definitions

Some defined schemas are used as common types. These common definitions help to simplify the actual object definitions by providing meaningful names, and reduce duplication. A change of ID type for example only needs one change in the common definition, and not in any of the object definitions which include an ID.

Special mentions:

#### Id

IDs are used for identification of resources, which can be retrieved by the API.

UUIDs are used, to ensure uniqueness. Also, they can be visually recognized as identifier.

#### Incremental

An `Incremental` is used in combination with other identifiers to identify a sub resource of any kind. `Incremental`s themselves are not globally unique, but unique for every sub resource of a unique resource.

#### Generation and order

`Generation` and `Order` are predefined objects which include a `Incremental` typed field for the common usages of the `Incremental` value.

#### SeverityValue

A `SeverityValue` is an unsigned integer ranging from 0 to 100 inclusively. It MUST be utilized by an `Impact` when referenced by a requested `Component` to gauge the severity of the impact on that component. It MUST be added to an `Impact` when referenced by an `Incident`, when its created. While being described as an unsigned integer, implementing this value MAY not require it to be an uint data type in any form, because its range even fits in a signed int8 (byte) data type. Each severity value SHOULD be unique, as multiple severities with the same value will be ambiguous.

### API objects

All objects which are used as payload, either as request or response, are defined by schemas. This centralizes the maintenance of field names and types, for both requests and responses.

### API object fields

Most fields of objects are not required. This allows usage as request and response payloads.

Responses of payload objects, which contain an ID or an `Incremental` typed field, MUST fill the ID or `Incremental` field to fully identify the (sub) resource.

Requests on a single resource MUST contain the ID in the path parameters. Request on sub resources MUST contain the ID and `Incremental` typed value as path parameters. The payload SHOULD NOT contain the ID or `Incremental` typed field.
If it contains these fields as payload, they SHALL NOT change them.

Requests to updating operations SHOULD contain the minimum of the changed fields, but MAY contain the full object. ID and `Incremental` typed fields MUST follow the same rules as stated above.

### Endpoint naming

The endpoints are named in plural form, even when handling single objects, to keep uniform paths.

### Phase list

The list of phases that an incident can go through has a crucial order. So it MUST be handled as the given list.

Delete or update operations are FORBIDDEN.

To "change" a phase list, a new one must be created. The old one must be kept. For this mechanic the lists are structured in generations. All references to phases MUST include their generation to ensure correct references.

To reference a single phase a `PhaseReference` MUST include a generation and an order field. This MAY be used to reference a single generation too.

### Labels

Labels are identifying metadata to components. They do not represent a resource or sub resource of any kind. They are designed as non system critical pieces of information, mainly intended for human consumption.

Labels are simple key/value pairs attached to components, categorizing them dynamically.

### Impact

An impact defines the relation between an incident and a component. A component can be affected by multiple incidents and an incident can affect multiple components. Each of these impacts can have a different type depending on the incident and component, like for example connectivity or performance issues.

To reflect this, each component and incident can have a list of impacts, stating the type of impact and a reference to the incident or component, it refers to.

Furthermore, a `SeverityValue` MUST be supplied to the `Impact` when referenced by a `Component`, to gauge the impact's severity on that component.

### Severity

A severity contains a name, that MUST be unique and will be used as identifier. The `SeverityValue` marks the upper boundary of the severity.

The severity's value range is calculated by taking the previous severity's (`SeverityA`) value and adding 1 to obtain the starting point and taking the current severity's (SeverityB) value as the end point. These limits are inclusive.

```acsii
0, ... , SeverityA.value, SeverityA.value, + 1, ... , SeverityB.value - 1, SeverityB.value, SeverityB.value + 1, ... , 100
                        |<------------range of severity values for SeverityB------------->|
```

Example:

```json
[
  {
    "displayName": "operational",
    "value": 33
  },
  {
    "displayName": "limited",
    "value": 66
  },
  {
    "displayName": "broken",
    "value": 100
  }
]
```

A special severity of type "maintenance" is given the exact value of 0.

This means:

- maintenance at 0
- operational from 1 to 33
- limited from 34 to 66
- broken from 67 to 100.

A value of 100 is the maximum of the severity value.

A severity with the value of 100 MUST always be supplied. This is the highest severity for the system. If no severity with a value of 100 exists, e.g. the highest severity value is set at 90, an `Impact` with a higher `SeverityValue` WILL be considered to be an _unknown_ severity.

### Component impacts

Components list their impacts, which they are affected by, as read only. Only an incident creates an impact on a component. Components MUST only list their currently active impacts.

An optional `now` parameter can be supplied, to set a reference time to show all incidents, active at that time, even when they are inactive currently.

### Maintenance

An `impact`, having the special `SeverityValue` of 0 indicates a maintenance time slot, as such it MUST include a start and end time.

### Return of `POST` requests

Generally `POST` requests create new resources. These endpoints do not return the new resource, but a unique identifier to the resource e.g. a UUID.

In most cases the new resource won't be used directly after creation. Most often list calls are used. If the new resource is used directly, it can be retrieved by the returned identifier.

Payloads to POST requests SHALL NOT include ID or `Incremental` typed fields, it lies in the responsibility of the API server to assign IDs and `Incremental`s to objects.

### Return of `PATCH` requests

Most commonly `PATCH` requests are used to partially or fully change a resource. These requests do not respond with the changed resource, nor an identifier.

Both the old state as well as the new state are known on the client at that point in time and if they need to load the actual recent version from the server, the identifier is already known.

### `PATCH` vs `PUT` for updating resources

The `PUT` requests is most commonly used to update full objects, whereas `PATCH` is used for partial updates.

`PATCH` is used as the default method for updating resources because it does not require the full object for an update, but does not discourage the use of the complete object.

### Authentication and authorization

The API spec does not include either authentication (AuthN) nor authorization (AuthZ) of any kind. The API server MUST be secured by a reverse/auth proxy.
