---
title: Sustainability Monitoring Data Formats
type: Standard
status: Draft
track: Ops 
---

## Introduction

This standard defines the metric schema for sustainability monitoring in SCS-compliant environments.
A common format ensures results are comparable across environments
and consumable by any reporting layer.


## Motivation

Without a shared metric schema, sustainability data from different SCS environments
cannot be compared or audited.
This standard defines what a compliant implementation MUST expose.

## Design Considerations

- Label cardinality should stay bounded
- Device and provider labels are constrained by the infrastructure inventory 
- Tenant labels are constrained to OpenStack project identifiers

## Standard (Naming Convention)

All metrics use the `sustainability_` prefix and follow the pattern:

```
sustainability_{subject}_{phase}_{category}
sustainability_{subject}_energy_kwh
```

Where:

  - `subject` SHOULD be presented as `device`, `provider` or `tenant`;
  - `phase` SHOULD be presented as `embodied`, `operational` or `total`;
  - `category` SHOULD be presented as `gwp_kg`, `adp_kg_sb_eq`, `ced_mj` or `water_m3`.

All metrics MUST be exposed in Prometheus text format as gauges.

### Device Level

```
sustainability_device_energy_kwh{datacenter, component, device}
sustainability_device_embodied_gwp_kg{datacenter, component, device}
sustainability_device_embodied_adp_kg_sb_eq{datacenter, component, device}
sustainability_device_embodied_ced_mj{datacenter, component, device}
sustainability_device_embodied_water_m3{datacenter, component, device}
```

### Provider Level

```
sustainability_provider_energy_kwh{datacenter, component}
sustainability_provider_operational_gwp_kg{datacenter, component}
sustainability_provider_operational_adp_kg_sb_eq{datacenter, component}
sustainability_provider_operational_ced_mj{datacenter, component}
sustainability_provider_embodied_gwp_kg{datacenter, component}
sustainability_provider_embodied_adp_kg_sb_eq{datacenter, component}
sustainability_provider_embodied_ced_mj{datacenter, component}
sustainability_provider_embodied_water_m3{datacenter, component}
sustainability_provider_total_gwp_kg{datacenter, component}
sustainability_provider_total_adp_kg_sb_eq{datacenter, component}
sustainability_provider_total_ced_mj{datacenter, component}
sustainability_provider_total_water_m3{datacenter, component}
```

### Tenant Level

```
sustainability_tenant_energy_kwh{project_id, project_name}
sustainability_tenant_operational_gwp_kg{project_id, project_name}
sustainability_tenant_operational_adp_kg_sb_eq{project_id, project_name}
sustainability_tenant_operational_ced_mj{project_id, project_name}
sustainability_tenant_embodied_gwp_kg{project_id, project_name}
sustainability_tenant_embodied_adp_kg_sb_eq{project_id, project_name}
sustainability_tenant_embodied_ced_mj{project_id, project_name}
sustainability_tenant_embodied_water_m3{project_id, project_name}
sustainability_tenant_total_gwp_kg{project_id, project_name}
sustainability_tenant_total_adp_kg_sb_eq{project_id, project_name}
sustainability_tenant_total_ced_mj{project_id, project_name}
sustainability_tenant_total_water_m3{project_id, project_name}
```

## Related Documents

- [Leaf Sustainability Monitoring Service](https://github.com/eco-digit/leaf) — Reference implementation developed under the ECO:DIGIT research project
- [SCS-0413-v1 - Sustainability Monitoring Architecture](scs-0413-v1-sustainability-monitoring-architecture.md)
