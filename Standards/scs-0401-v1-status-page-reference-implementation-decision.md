---
title: Status page reference implementation decision
type: Decision Record
status: Draft
track: Ops
---

## Introduction

For the reference implementation of the status page API defined by the [OpenAPI spec](https://github.com/SovereignCloudStack/status-page-openapi) some decision should be made to which technlogy to be used and why.

A reference implementation should be of use to most of the intended group, but is not necsessarily applicable for every use case.

## Motivation

For a reference implementation to be of any use, some common and widely used technologies should be used, so it's useful to most of the intended user group.

## Decision

### Programming Language

The status page application consists of an api server as well as a frontend. For implementing the  [api server]( ), which is generated from the [OpenAPI spec](https://github.com/SovereignCloudStack/status-page-openapi), the [Go](https://go.dev/) was chosen, because of maturity and wide spread usage as industry standard. Go, in particular, is a modern programming language and is commonly used in network and cloud computing environments.

### Database

For the database [PostgreSQL](https://www.postgresql.org/) was chosen, since it is a mature, well-known database. PostgreSQL can be run in various environments from small setups to scaled setups. 
Furthermore PostgreSQL is a very healthy project with an active community and a solid license. It easily passed the [SCS OSS health check](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/OSS-Health.md).
