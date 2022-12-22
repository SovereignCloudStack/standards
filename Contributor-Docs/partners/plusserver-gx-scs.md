---
title:  Getting Started Gaia-X Demonstrator @ plusserver
version: 2022-12-21
author: Ralf Heiringhoff, Mathias Fechner
---

# Getting Started for the Gaia-X Demonstrator @ PlusServer

# URLs for access

*  UI (Horizon): https://ui.gx-scs.sovereignit.cloud/
*  API auth url (Keystone): https://api.gx-scs.sovereignit.cloud:5000
*  Object Storage endpoint (S3/SWIFT): https://api.gx-scs.sovereignit.cloud:8080

## Authentication (UI)

For your login you will need:

*  Username (`u500924-<github handle>`)
*  Password
*  Domain (`d500924`)

## OpenStackClient (CLI)

The OpenStackClient is installable via all major Linux Distibitions (`apt search openstackclient`)
or directly via [pypi](https://pypi.org/project/python-openstackclient). For
further Information see the OpenStack Project upstream website
[python-openstackclient](https://docs.openstack.org/python-openstackclient/latest/index.html).

This repo holds examples for `clouds-public.yaml` + `clouds.yaml`.

Alternatively you can download an OpenRC Environment file when you're logged in to Horizon:
*  upper left side :arrow_right: <your login name>
*  OpenStack RC File

```
$ source ./<your file>-openrc.sh
Please enter your OpenStack Password for project XXX as user YYY:
```

when you're using clouds.yaml you can specify multiple endpoints and select the specific endpoint
by passing `--os-cloud=` to the openstack cmdline or setting `OS_CLOUD`.

## Object Storage (S3)

Create AWS like credentials with `openstack ec2 credentials create`.
If you use libs3, store the access field in `S3_ACCESS_KEY_ID` and the secret field in
`S3_SECRET_ACCESS_KEY` and set `S3_HOSTNAME=<Object Storage endpoint>`.
You will see the same buckets (containers) and objects whether you access your object store
via the swift or via the s3 protocol.

# References

*  [OpenStack](https://www.openstack.org "OpenStack Site")
*  [SovereignCloudStack](https://github.com/SovereignCloudStack "SovereignCloudStack on github")
*  [OSISM](https://github.com/osism "OSISM on github")
*  [ansible](https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html "Ansible Module OpenStack" )
*  [terraform](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs "OpenStack Terraform Provider")
*  [cloud-init](https://cloudinit.readthedocs.io/en/latest/ "cloud-init documentation")
