---
title: Sustainability Monitoring Architecture
type: Decision Record
status: Draft
track: Ops
---

## Introduction

Cloud infrastructure produces environmental impact in two ways:
through the energy consumed at runtime (operational emissions)
and through the manufacturing, transport and installation of hardware (embodied emissions).
Without a standardized monitoring mechanism,
cloud operators and tenants have no reliable way to measure,
compare or reduce this impact across environments.

This document provides an architectural blueprint for sustainability monitoring
in SCS-compliant environments
and describes the decisions taken to achieve it.

## Terminology

**LCA** - Life Cycle Assessment is a comprehensive methodology used to evaluate the environmental impacts of products, services or systems through their life cycle.

**Embodied emissions**- Refer to the environmental impact that is associated with the actual production, transportation and installation of hardware.

**Operational emissions** - Produced during the so-called usage phase, through energy consumption for computing workloads, cooling and network operations.

**GWP** — Global Warming Potential, kg CO2eq

**ADP** — Abiotic Depletion Potential, kg Sb eq

**CED** — Cumulative Energy Demand, MJ

## Architectural Overview

Sustainability monitoring for SCS-compliant environments addresses the need
to measure, calculate and report the environmental impact of cloud infrastructure
across two scopes:
the **provider level** (total infrastructure footprint)
and the **tenant level** (per-project/ per-vm attribution of that footprint).

The architecture is composed of four logical layers.

### Telemetry Layer

The telemetry layer collects raw operational data from the physical infrastructure.
This includes energy consumption metrics from compute servers, storage nodes,
network equipment and management hardware,
made available through a time-series database (TSDB).

Data sources at this layer include node-level power and energy readings (via RAPL, BMC/IPMI or Redfish exporters),
VM-, Container-, or Pod level energy attribution (via Kepler or hypervisor instrumentation),
and tenant-to-resource mapping via hypervisor metadata.

> Kepler itself can also get (and serve) its metrics from data obtained via RAPL/BMC/IPMI/Redfish.

### Calculation Layer

The calculation layer is an external processor that reads from the telemetry layer,
applies the environmental impact model,
and produces derived sustainability metrics.
It does not instrument hardware directly.

Required inputs to the calculation layer are:
raw energy metrics from the TSDB,
a grid carbon intensity factor (from an external API or static configuration),
hardware embodied impact values (from a hardware profile database or static configuration),
physical infrastructure topology (device inventory, roles and lifespans),
and a facility efficiency factor (PUE).

### Reporting Layer

The reporting layer scrapes the metrics endpoint exposed by the calculation layer
and stores results for querying and visualization.

### External Data Sources

Grid emission factors provide the carbon intensity of the local electricity grid,
used to convert energy consumption into operational GWP.
These can be sourced from a real-time API or configured as static values.

Hardware profiles provide embodied impact values per device model,
covering manufacturing, transport and installation.
These can be sourced from a hardware environmental database or provided as static configuration calculated using an external embedded impact calculation sheet.

### Environmental Impact Model

The model follows a lifecycle assessment (LCA) approach
aligned with ISO 14040/14044 and the GHG Protocol.

Total environmental impact is the sum of two phases:

```text
Total Impact = Embodied Emissions + Operational Emissions
```

Embodied emissions represent the manufacturing impact of hardware,
amortized over the device lifespan and reporting period.

Operational emissions represent the energy consumed during the reporting period,
multiplied by a facility efficiency factor (PUE) and a grid emission intensity factor.

Four impact categories are tracked.
GWP (Global Warming Potential, kg CO2eq) covers both embodied and operational phases.
ADP (Abiotic Depletion Potential, kg Sb eq), CED (Cumulative Energy Demand, MJ)
and Water Use (m^3) cover the embodied phase only.

### Tenant Attribution

Tenant-level impact is derived from provider-level impact
using a two-component attribution model.

The idle share represents the baseline cost of reserved capacity,
allocated proportionally by reserved vCPU, memory and storage ratios.

The dynamic share represents actual usage-phase energy measured at the VM level,
attributed proportionally to the tenant's VMs relative to total host energy.

```text
Tenant Total = Idle Share of Provider Idle Energy + Dynamic Share of Provider Active Energy
```

> A proof-of-concept implementation of this architecture is available as Leaf,
> developed under the ECO:DIGIT research project for SCS-based OpenStack environments.

## Design Considerations

The following requirements apply to a sustainability monitoring architecture
for SCS-compliant environments.

The architecture MUST separate telemetry collection from environmental impact calculation.
Coupling hardware instrumentation to carbon accounting logic
makes both harder to evolve independently
and prevents the monitoring stack from being reused across implementations.

The architecture MUST be stateless between calculation cycles.
No state from a previous cycle MUST influence the result of the next.
Results of each calculation cycle MUST be persisted to a storage backend
to ensure availability between cycles and across restarts.
The choice of storage backend is left to the implementation.

The calculation layer MUST own all query and aggregation logic.
Splitting model logic across the TSDB configuration and the calculator
creates two sources of truth for the same semantics,
making the model harder to test and evolve.

Results MUST be available for consumption independently of when the calculation runs.
The serving of results MUST NOT block on or trigger a new calculation cycle.

Model parameters (impact factors, infrastructure topology, device profiles)
MUST be separable from calculation logic.
This allows operators to audit and update parameters
without modifying the implementation,
and makes the model independently verifiable.

### Options Considered

#### Kepler exporter

We tested the Kepler exporter for providing VM-specific energy measurements. This seems to be the best option on the market right now.

#### Tested in PoC: Periodic background calculation with cached serving

The calculator runs on a configurable interval,
writes results to a cache,
and serves the last result on demand without triggering a new calculation.

#### On-demand calculation

The calculator runs each time results are requested.
This keeps results fresh
but couples serving latency to calculation time,
which may be significant for large infrastructures.

#### External processor reading from the TSDB

The calculator is deployed as a separate service.
It reads raw metrics from the TSDB via queries,
applies the environmental model,
and exposes derived metrics on its own endpoint for the TSDB to scrape.

This keeps the existing monitoring stack unchanged and exchangeable.
The calculator can be updated or replaced without touching exporters or the TSDB and vice versa.

### Decision

The external processor pattern is adopted.
The calculator reads from the TSDB, owns all query logic,
and exposes results on a separate metrics endpoint.
The TSDB is the only storage backend, but can be exchanged for a reporting database.
Calculation and serving are decoupled into two independent loops.
Model parameters are held in configuration,
separate from calculation logic.

## Related Documents

- [Leaf Sustainability Monitoring Service](https://github.com/eco-digit/leaf) — Reference implementation developed under the ECO:DIGIT research project
- [SCS-0414-v1 — Sustainability Monitoring Data Formats](scs-0414-v1-sustainability-monitoring-data-formats.md)
