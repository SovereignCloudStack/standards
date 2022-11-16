# Helm Charts vs. Operators: When to Use?

If both a Helm Chart and separately an Operator are available to manage an application (e.g. Grafana or Prometheus), a choice needs to be made.

In general, Helm Charts may be preferable over operators because they are purely declarative. All Helm charts only depend on the helm tool and do not run their own code (beyond the templates). This reduces the scope for bugs and the amount of resources required to run them.

On the other hand, operators can help the user with maintenance tasks such as scheduled backups or upgrades of the application. In addition, operators integrate better with standard kubernetes tooling as they are integrated more closely with the kubernetes API.

In general, for stability, we prefer Helm charts over operator, unless the operator provides us with additional features which are required (such as the ones described above).

TL;DR: Prefer Helm charts over Operators (less code is better, as code has bugs), unless:

* You need to manage many instances of a thing (an Operator integrates better with k8s tooling incl. monitoring)
* The operator allows to manage operational tasks (scheduled backups / upgrades ...) and those operational tasks are required and cannot be delivered with built-in k8s utilities.
