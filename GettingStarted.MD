---
title:  Getting Started Gaia-X Demonstrator @ PlusServer
version: 2020-10-23-001
author: Mathias Fechner

---

# Getting Started for the Gaia-X Demonstrator @ PlusServer

# First Steps

## URLs for access

 + UI (Horizon): https://gx-scs.okeanos.dev/
 + auth_url (Keystone): https://gx-scs.okeanos.dev:5000
 + keycloak_url: https://gx-iam.okeanos.dev:5000
 + S3 endpoint (same as swift from catalog): https://gx-scs.okeanos.dev:8080

## Software Components

### Openstack U - Release (Ussuri)

 + Core Components (Keystone - auth, Cinder - block storage,
   Nova - compute, Glance - images, Neutron - networking)
 + Heat (Orchestration)
 + DNS (Designate)
 + Loadbalancer (Octavia)
 + Object Storage (Swift and S3 protocol via RadosGW, see below)
 + Secrets Management (Barbican) and Cloud Container Engine (magnum) in preparation
 + A standard set of current Linux cloud images (Ubuntu, Debian, Fedora, CentOS, OpenSUSE,
   Cirros, Clear Linux) with the standard cloud-init included for processing of user_data
   to customize them.

### Ceph N - Release (Nautilus)

+ Block-storage
+ Object-store (S3 and Swift via radosgw)

### K8S Cluster Management

We have not yet aligned on a standard built-in solution, as none of the
Open Source solutions fully uses and implements the k8s cluster API really well.
We have done successful PoCs with Rancher, Kubermatic and SAP Gardener, and
the automation for them can be found on https://github.com/SovereignCloudStack/

We have currently people working on the OpenStack k8s cluster API provider
and on Gardener to integrate something out of the box, possibly leveraging
Magnum to create a seed cluster on demand.

### Automation Tools

Continuous automated rollout in docker containers

+ Base install with MaaS, Netbox, Linux, KVM on Bare Metal
+ OSISM with kolla-ansible, ceph-ansible, infra tooling (database, msgQ, ...)
+ Monitoring tools (netdata, prometheus, ...) for operations
+ Lifecycle Management & Updates (patchman)
+ Validation (CI) with smoke tests, refstack, openstack-health-monitor

### OVN OpenVirtualNetwork SDN

+ OVN 20.09.0

## Client Software Requirements

### Debian Based Family (Debian, Ubuntu)

```console
apt install python3-openstackclient
```

### RPM Based Family (Red Hat Enterprise Linux 8, CentOS 8, or FedorcoreOS)

```console
dnf install https://www.rdoproject.org/repos/rdo-release.el8.rpm;
dnf install python-openstackclient
```

### RPM Based Family (Red Hat Enterprise Linux 7, CentOS 7)

```console
yum install centos-release-openstack-ussuri;
yum config-manager --set-enabled PowerTools;
yum install python-openstackclient
```

### SuSE

```console
#zypper ar -f obs://Cloud:OpenStack:Ussuri/ Cloud:OpenStack:Ussuri
zypper install python-PROJECTclient
```

### MacOS

```console
brew install python-openstackclient
```

### PIP

```console
pip install python-openstackclient
```

## Windows

```console
C:\>pip install python-PROJECTclient
```

## the Openstack CLI

```console
# openstack
(openstack) server ...
(openstack) network ...
(openstack) volume  ...
(openstack) image ...
```

Continue "..." with enter to show all options

Under the item [API:](https://gx-scs.okeanos.dev/project/api_access/# "API Credentials") you will find the 
OpenRC file to source in to your environment or alternatively (better) you add the downloadable
`clouds.yaml` (and `secure.yaml`) to your `~/.config/openstack/` directory and set `OS_CLOUD` or
pass `--os-cloud=`.

## Object Storage (S3)

Create AWS like credentials with `openstack ec2 credentials create`.
If you use libs3, store the access field in `S3_ACCESS_KEY_ID` and the secret field in
`S3_SECRET_ACCESS_KEY` and set `S3_HOSTNAME=gx-scs.okeanos.dev:8080`.
You will see the same buckets (containers) and objects whether you access your object store 
via swift or via s3 protocol.

## Automation

+ ansible
  os_auth, os_server

+ terraform
  openstack/provider
  [OSISM](https://github.com/osism/testbed "some terraform examples")


## Authentication (UI)

For your login you will need:

+ Domain
+ Username
+ Password

in case of Keycloak you will need just
Username and Password.

Contact us if you want to use keycloak to federate identities from another identity provider.

## References

[OpenStack](https://www.openstack.org "OpenStack Site")
[SovereignCloudStack](https://github.com/SovereignCloudStack "SovereignCloudStack on github")
[OSISM](https://github.com/osism "OSISM on github")
[Ceph](https://ceph.io/ "Ceph Site")
[OpenvSwitch](https://www.openvswitch.org "OpenvSwitch Side")
[ansible](https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html "Ansible Module OpenStack" )
[Terraform](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs "OpenStack Terraform Provider")
[cloud-init](https://cloudinit.readthedocs.io/en/latest/ "cloud-init documentation")
