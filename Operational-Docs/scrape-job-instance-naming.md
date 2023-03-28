# How to ensure human readable prometheus job instance names in Grafana dashboard

Kolla-natively, Prometheus does not scrape endpoints by FQDN, as it does not integrate the infrastructure into hostname files. This leads to Grafana only showing nodes by IP, which can be confusing and unintuitive. A better alternative would be clean FQDN names for the Grafana Dashboards provided by prometheus scrape jobs.

Conventienly, OSISM delivers "hard-coded" FQDN functionality with `osism-generic hosts` (<https://github.com/osism/ansible-collection-commons/tree/main/roles/hosts>) so we can leverage this to help Prometheus to scrape endpoints by FQDN.

To achieve this, we need to add a custom `prometheus.yml` as well as custom scrape definitions in prometheus.yml.d and, most importantly, custom hosts to the `hosts_additional_entries` dict object in `environments/configuration.yml`

## Example: prometheus_node_exporter stanza

```yaml
{% if enable_prometheus_node_exporter | bool %}
  - job_name: node
    static_configs:
      - targets:
{% for host in groups['prometheus-node-exporter']|default([])|sort %}
        - '{{ host }}:{{ hostvars[host]['prometheus_node_exporter_port'] }}'
{% endfor %}
{% endif %}
```

The catch is to iterate through `{{ host }}` and not the kolla-native `{{ 'api' | kolla_address(host) | put_address_in_context('url') }}` to force Kolla-Ansible to iterate through hostnames instead of IPs.

During the rollout via `osism-kolla prometheus` the prometheus.yml in `environments/prometheus/prometheus.yml` will be merged with the .yml-files in `prometheus.yml.d`.

Kolla-Ansible is able to merge the `prometheus.yml` and the .yml files in the `prometheus.yml.d` in a functional way. Defining the scrape jobs for custom services we wish to hold in prometheus ought to be done in `prometheus.yml.d`.

The `prometheus-server` container mounts the `/etc/hosts` file of the Docker host into the container and is as such able to resolve other hosts in the infrastructure.

Of course it is also possible to scrape endpoints of custom services not integrated into OSISM. This can be achieved by adding their FQDNs to the `hosts_additional_entries` dict object in `environments/configuration.yml` and then creating a custom scraping stanza iterating through a dict of the custom endpoints.
