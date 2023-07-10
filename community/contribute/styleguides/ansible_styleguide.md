# Ansible Style Guide

We use nearly all default rules of ansible lint. A listing of all these rules can be found in the Ansible Lint documentation:
<https://ansible.readthedocs.io/projects/lint/rules/>.
Please always use the ansible linting to check if the code complies with the default linting rules.
However, since in most cases we always use the latest version of packages and Ansible lint does not provide this, we decided to
disable the package_latest rule.

## Task naming

* Tasks must always have names. The only exception allowed is for forked playbooks.
* A name never starts with a small letter
* Names are written in present tense
* No punctuation is used in names

## Key Order

To check the key order we use our own rule. This can be found [here](https://github.com/osism/zuul-jobs/tree/main/roles/ansible-lint/files).

### Positioning and use of the become directive

The become directive is only set when needed and is always set explicitly for each task that needs it.

Blocks, roles or playbooks are never executed in a privileged mode.

We always insert the become directive between the name of a task and the task itself. This also applies to related directives
like *become_user* or *become_flags*. This is for better visibility if a task is privileged or not.

```yaml
- name: Copy hddtemp configuration file
    become: true
      ansible.builtin.copy:
      src: "{{ ansible_os_family }}/hddtemp"
      dest: "{{ hddtemp_conf_file }}"
      owner: root
      group: root
      mode: 0644
    notify: Restart hddtemp service
```

### Position of the when condition

If you need to use the when condition please add this at the end-section from the task where it is needed. This makes the code
easier to understand for others. Ansible lint provides the when condition under the task name for blocks. To keep the code clear
we decided against it. Please disable this with a noqa if necessary. For example:

```yaml
- name: "Archive existing {{ resolvconf_file }} file"
    become: true
    ansible.posix.synchronize:
      src: "/etc/resolv.conf"
      dest: "/etc/resolv.conf.{{ ansible_date_time.date }}"
      archive: true
    delegate_to: "{{ inventory_hostname }}"
    when: stat_resolvconf_file.stat.islnk is defined and not stat_resolvconf_file.stat.islnk
```

## Usage of collections

Collections are always defined as in the following example.

**netbox.netbox** is here the collection that is used.

```yaml
- name: Configure netbox manufacturers
  netbox.netbox.netbox_manufacturer:
    netbox_url: "{{ netbox_url }}"
    netbox_token: "{{ netbox_token }}"
    data:
      name: "{{ item.value.name }}"
      slug: "{{ item.value.slug }}"
      description: "{{ item.value.description | default('') }}"
    state: present
  with_dict: "{{ netbox_data_manufacturers }}"
```

Please don´t declare it in this way!:

```yaml
collections:
    - netbox.netbox

  tasks:
    - name: Manage Discworld site
      netbox_site:
        netbox_url: "{{ netbox_url }}"
        netbox_token: "{{ netbox_token }}"
        validate_certs: false
        data:
          name: Discworld
          slug: discworld
        state: present
```

If you have to use collections please define them in a requirements.yml.

Example yaml:

```yaml
roles:
  - name: geerlingguy.certbot
    version: master
    type: git
    src: git+https://github.com/geerlingguy/ansible-role-certbot.git
...

collections:
  - name: ansible.netcommon
    source: https://galaxy.ansible.com

  - name: https://github.com/ansible-collections/ansible.posix.git
    type: git
    version: main
```

## Usage of roles from other collections

If you want to reuse roles please do it in the following way:

First you have to declare the role or collection in the requirements.yml like shown in the example before.

Than you can use it in playbooks like this

```yaml
  roles:
    - role: osism.services.auditd
```

## Parameters that offer lists

Parameters that provide a list are always defined as in the following example.

**docker_hosts_defaults** sets the defaults in the role. Overriding is only possible with the **ansible-defaults** repository.

In the configuration repository, docker_hosts_extra is then used to add additional items to the list.

**docker_hosts** itself is never modified from the outside.

```yaml
   docker_hosts_defaults:
     - "unix:///var/run/docker.sock"
   docker_hosts_extra: []
   docker_hosts: "{{ docker_hosts_defaults + docker_hosts_extra }}"
```

## Usage of changed_when

Please think twice before turning off changed_when. It's a fairly simple yet safety-relevant linting rule and is quite easy to
implement.

## Disable linting rules

In principle, it is only allowed to disable rules if there is really no other possibility.
Please do not disable rules in general but only in individual cases via Noqa. Please use in this case the full rulename and not
the numbers, because them are depricated. If it makes sense to ignore a rule, please open up an issue in the
<https://github.com/osism/issues> repository with a label discussion.
