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

[Go](https://go.dev/) and [PostgreSQL](https://www.postgresql.org/) were chosen, because of maturity and wide spread usage as industry standard. Go, in particular, is a modern programming language and is commonly used in network and cloud computing environments.
