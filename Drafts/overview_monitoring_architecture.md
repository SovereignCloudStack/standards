# Overview of Monitoring Architecture

## Objective

The objective of this document is to establish a common understanding of the monitoring architecture of the SCS stack. This document refers to various roles. These are defined in the [overall role definitions](https://github.com/SovereignCloudStack/standards/blob/master/Drafts/terms_and_roles_identity_and_access_management.md).

## Definitions

The term _monitoring_ is used to describe methods that enable **Anomaly Detection**, provide
**Operational Visibility** and allow **Capacity Planning**.

Furthermore it is being distinguished between _whitebox monitoring_ and _blackbox monitoring_.

| Intent                 | Whitebox Monitoring | Blackbox Monitoring |
| ---------------------- | ------------------- | ------------------- |
| Capacity Planning      | x                   | -                   |
| Anomaly Detection      | x                   | x                   |
| Operational Visibility | x                   | x                   |

The term **monitoring** includes:

- Healthcheck data (state)
- Telemetry (metrics)
- Centralized Log aggregation

## Roles

There are various roles within the SCS scope that interact from different viewpoints with the monitoring (data). While the _operator_ needs to be able to have a full stack view, the _supporter_ looks from a slightly different viewpoint upon the monitoring.

| Role                 | Capacity Planning | Anomaly Detection | Operational Visibility |
| -------------------- | ----------------- | ----------------- | ---------------------- |
| Operator (Provider)  | x                 | x                 | x                      |
| Supporter (Provider) | -                 | (x)               | x                      |
| Integrator           | (x)               | x                 | (x)                    |
| Developer            | -                 | x                 | -                      |

Aside from these roles there are further cases that will use data aggregated as part of the monitoring:

- Provider Invoicing will need telemetry on usage data in order to provide billing.
- The SCS vendor will need anonymized usage data on the overall SCS stack adoption.

## Alerting

Wether the source are logs, metrics or health checks alerts need to be aggregated and transported via the _alert routing_ to the provider-specific alerting engine. This allows the flexibility of each Provider coming with their specific alerting engine while keeping the alert routing within the SCS stack standardised.

## Architecture

Monitoring happens on two layers: _infrastructure layer_ and the _container layer_. This is illustrated in [the overview diagram](https://github.com/SovereignCloudStack/standards/blob/1fb174da1ee906f0da6a8bbefbd3d95884df5669/Drafts/overview_monitoring_architecture.svg).
Each layer has their own set of components to assure independence.
