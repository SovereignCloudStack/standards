# Overview

Service providers often times want to communicate the status of their systems transparently to their users.
A commonly used pattern is to provide a "status page" web application, where the current system health as well as recent incidents are made available.

SCS strives to implement a status page that works well, while being interoperable with other systems.

:::note

How was the decision to implement a new status page application made? What were the requirements? See the [decision record](https://github.com/SovereignCloudStack/standards/blob/1fb174da1ee906f0da6a8bbefbd3d95884df5669/Standards/scs-0400-v1-status-page-create-decision.md).

:::

To be easily interoperable with other software, being "API-first" is a priority.
As such, the status page should not _need to_ be a typical monolithic web application (even though it could be), hence making it possible to split functionality into an API server and a frontend component.

## The SCS status page **API**

The SCS status page **API** (as opposed to actual implementations) is supposed to be as un-opinionated as possible regarding deployment, user management, persistence and tech stack, to allow operators/developers (1) to make their own decisions regarding these topics and (2) to quickly implement the API with their own tech stack opinions, if the reference implementation does not fit theirs.

In particular, the **API** has no opinion about:

- How authentication/authorization is done (apart from splitting Read-only from Read-write [^1]; See below)
- Server implementation, used database, deployment automation, high availability

However, as un-opinionated the API (in its first iteration) strives to be, it is...:

- a REST API (no GRPC/GraphQL/...)
- defined using an OpenAPI file to make use of OpenAPI tooling
- split in two parts [^1]:
  1. Read-only anonymous access
  2. Read-write authenticated access

[^1]: In the future

### Reference implementation

It is envisioned to have a well-maintained reference implementation of the status page API with some basic tech stack decisions made, to not _require_ anyone to implement the API themselves:

- Programming Language: Go
- Persistence: Postgres compatible database

## The SCS status page **frontend**

The SCS status page **frontend** is supposed to be an application which uses the status page API to get information. This could be an CLI tool as well as an web application.

### Reference implementation

It is envisioned to have a well-maintained reference implementation of an status page frontend with some basic tech stack decisions made:

- Platform: Web (HTML/JS/...)
- Framework: VueJS, Vuetify
