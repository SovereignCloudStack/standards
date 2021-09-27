# SCS Monitoring

For release 1 we focus on adopting within OSISM the best of
pre-existing monitoring options from kolla-ansible. In particular:

* Centralised debug logs, as provided by fluentd and elasticsearch
* Prometheus based alerts and dashboards

We are looking for feedback from users on what ares are in most need
of attention. We have already identified some areas for future work
including:

* audit logging framework
* adding any missing promtheus exporters (e.g. libvirt, OVN)
* improving the performance of existing exports, such as the OpenStack exporter
* billing telemetry sources (e.g. Notifications, CloudKitty, etc)

## Centralised Logging

Details on kolla-ansible and its support for elasticserach,
Fluentd, Kibana and elasticserach curator can be found here:
https://docs.openstack.org/kolla-ansible/latest/reference/logging-and-monitoring/central-logging-guide.html

## Prometheus based monitoring

We are collaborating on a common set of dashboards and alerts here:
https://github.com/osism/kolla-operations

We hope to make them as widely applicable as possible through collaboration
with all members of the SCS community, including those that do not make use
of either OSISM or kolla-ansible.

For more details on what kolla-ansible provides, please see:
https://docs.openstack.org/kolla-ansible/latest/reference/logging-and-monitoring/prometheus-guide.html
