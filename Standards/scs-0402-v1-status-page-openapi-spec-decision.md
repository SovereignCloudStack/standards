---
title: Status page OpenAPI decision
type: Decision Record
status: Draft
track: Ops
---

## Introduction

While defining the [OpenAPI spec](https://github.com/SovereignCloudStack/status-page-openapi) some considerations and decisions are made and should be documented.

## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

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

#### IdList

List of IDs are used to reference other resources in an API object.

#### Incremental

An `Incremental` is used in combination with other identifiers to identify a sub resource of any kind. `Incremental`s themselves are not globally unique, but unique for every sub resource of an unique resource.

### API objects

All objects which are used as payload, either as request or response, are defined by schemas. This centralizes the maintanence of field names and types, for both requests and responses.

The only exception are responses which return lists. The list of API objects is only used once and the definition of an array type is trivial.

### API object fields

Most fields of objects are not required. This allows usage as request and response payloads.

Responses of payload objects, which contain an ID or an `Incremental` typed field, MUST fill the ID or `Incremental` field to fully identify the (sub) resource.

Requests on a single resource MUST contain the ID in the path parameters. Request on sub resources MUST contain the ID and `Incremental` typed value as path parameters. The payload SHOULD NOT contain the ID or `Incremental` typed field.
If it contains these fields as payload, they SHALL NOT change them.

Requests to updating operations SHOULD contain the minimum of the changed fields, but MAY contain the full object. ID and `Incremental` typed fields MUST follow the same rules as stated above.

### Endpoint naming

The endpoints are named in plural form, even when handeling single objects, to keep uniform paths.

### Phase list

The list of phases that an incident can go through has a crucial order. So it MUST be handled as the given list.

Delete or update operations are FORBIDDEN.

To "change" a phase list, a new one must be created. The old one must be kept. For this mechanic the lists are structured in generations. All references to phases MUST include their generation to ensure correct references.

### Labels

Labels are identifying metadata to components. They do not represent a resource or sub resource of any kind. They are designed as non system critical pieces of information, mainly intended for human consumption.

They represent a key value pair as structured data for a single component. Same value keys and values do not reference each other necessarily.

### Impact

An impact defines the relation between an incident and a component. A component can be affected by multiple incidents and an incident can affect multiple components. Each of these impacts can have a different type depending on the incident and component, like for example connectivity or performance issues.

To reflect this, each component and incident can have a list of impacts, stating the type of impact and a reference to the incident or component, it refers to.

### Return of `POST` requests

Generally `POST` requests create new resources. These endpoints do not return the new resource, but a unique identifier to the resource e.g. an UUID.

In most cases the new resource won't be used directly after creation. Most often list calls are used. If the new resource is used directly, it can be retrieved by the returned identifier.

Payloads to POST requests SHALL NOT include ID or `Incremental` typed fields, it lies in the responsibility of the API server to assign IDs and `Incremental`s to objects.

### Return of `PATCH` requestes

Most commonly `PATCH` requests are used to partially or fully change a resource. These requests do not respond with the changed resource, nor an identifier.

Both the old state as well as the new state are known on the client at that point in time and if they need to load the actual recent version from the server, the identifier is already known.

### `PATCH` vs `PUT` for updating resources

The `PUT` requests is most commonly used to update full objects, whereas `PATCH` is used for partial updates.

`PATCH` is used as the default method for updating resources because it does not require the full object for an update, but does not discourage the use of the complete object.

### Authentication and authorization

The API spec does not include either authentication (AuthN) nor authorization (AuthZ) of any kind. The API server MUST be secured by an reverse/auth proxy.
