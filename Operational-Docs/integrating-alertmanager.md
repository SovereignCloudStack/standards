# Integrating Alertmanager

SCS integrates [alertmanager](https://github.com/prometheus/alertmanager) as part of the
monitoring stack. In order to integrate alertmanager with existing on-call infrastructure
configurations can be deployed via the overlays.
The overlays can be deployed from the manager node. Overlays are placed in:

`/opt/configuration/environments/kolla/files/overlays`

Examples of integrations can be found (and added) to this document.


## Opsgenie

To integrate with [Opsgenie](https://www.atlassian.com/software/opsgenie) the following snippet
can be used:

```
---
global:
  resolve_timeout: 5m
  opsgenie_api_key: <opsgenie-api-key>

route:
  receiver: opsgenie
  group_by: [alertname, datacenter, app]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: opsgenie
    opsgenie_configs:
      - responders:
          - id: <opsgenie-responder-id>
            type: team
```
