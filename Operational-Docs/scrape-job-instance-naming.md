# How to create better job instance names through fqdn-based scraping

Kolla-natively, Prometheus does not scrape endpoints by FQDN, as it does not integrate the infrastructure into hostname files. Conventienly, OSISM delivers this functionality with `osism-generic hosts` (https://github.com/osism/ansible-collection-commons/tree/main/roles/hosts) so we can leverage this to help Prometheus to scrape endpoints by FQDN.

To achieve such, we need to add a custom `prometheus.yml` as well as custom scrape definitions in prometheus.yml.d and, most importantly, custom hosts to the `hosts_additional_entries` dict object in `environments/configuration.yml`

## Example: prometheus_node_exporter stanza

```
{% if enable_prometheus_node_exporter | bool %}
  - job_name: node
    static_configs:
      - targets:
{% for host in groups['prometheus-node-exporter']|default([])|sort %}
        - '{{ host }}:{{ hostvars[host]['prometheus_node_exporter_port'] }}'
{% endfor %}
{% endif %}
```

The catch is to iterate through `{{ host }}` and not the kolla-native `{{ 'api' | kolla_address(host) | put_address_in_context('url') }}` to force Kolla-Ansible thusly to just iterate through hostnames instead of IPs.

During the rollout via `osism-kolla prometheus` the prometheus.yml in `environments/prometheus/prometheus.yml` will be merged with the .yml-files in `prometheus.yml.d`.

Kolla-Ansible is able to merge together the `prometheus.yml` and the .yml files in the `prometheus.yml.d` in a functional way. Defining the scrape jobs for custom services we wish to hold in prometheus ought to be done in `prometheus.yml.d`.

The `prometheus-server` container mounts the `/etc/hosts` file of the Docker host into the container and is as such able to resolve other hosts in the infrastructure.

It is of course also possible to scrape endpoints of custom services not integrated into OSISM. This can be achieved by adding their FQDNs to the `hosts_additional_entries` dict object in `environments/configuration.yml` and then creating a custom scraping stanza iterating through a dict of the custom endpoints.
