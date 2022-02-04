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

## Matrix

To integrate with the [matrix](https://matrix.org/) protocol a bot that is able to receive webhooks such as 
[alertmanager\_matrix](https://github.com/dkess/alertmanager_matrix) or 
[matrix-alertmanager](https://github.com/jaywink/matrix-alertmanager) can be used.
This example serves as a reference for any kind of system that works via webhooks.
Within alertmanager a webhook is set as the receiver:

```
receivers:
- name: 'matrix'
  webhook_configs:
    - url: <webhook-of-matrix-bot>
```

## Signalilo

To integrated with [Signalilo](https://github.com/vshn/signalilo) the following can be used :

```
global:
  resolve_timeout: 5m
route:
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: default
  routes:
  - match:
      alertname: DeadMansSwitch
    repeat_interval: 5m
    receiver: deadmansswitch
receivers:
- name: default
  webhook_configs:
  - send_resolved: true
    http_config:
      bearer_token: "*****"
    url: https://<webhook-of-signalio-service>/webhook
- name: deadmansswitch
```

the container for Signalilo  you will get here: [quay.io](https://quay.io/repository/vshn/signalilo)
