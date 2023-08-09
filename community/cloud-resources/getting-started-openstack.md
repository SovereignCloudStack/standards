---
title: Getting Started with OpenStack
version: 2023-08-04
author: Ralf Heiringhoff, Eduard Itrich, Mathias Fechner
---

## Getting Started with OpenStack CLI

## OpenStackClient (CLI)

The OpenStackClient is installable via all major Linux Distributions:

for debian and ubuntu with apt:

```bash
sudo apt install python3-openstackclient
```

for ubuntu with snap openstack CLI is installable too:

```bash
sudo snap install openstackclients
```

>[!NOTE]
>Versions from Linux repository could be in a stable but old state.

Install it directly via [pypi](https://pypi.org/project/python-openstackclient)
from upstream is the recommend way.

Here for example RHEL:

```bash
sudo dnf install python3 python3-devel gcc python3-pip
```

Here for example Debian and Ubuntu:

```bash
sudo apt install python3-minimal python3-pip python3-venv python3-dev build-essential
```

 Here as example for SUSE

```bash
sudo zypper in python3-pip python3-venv python3-dev
```

Here for example with Apple's MacOS

```bash
brew install python3
```

>[!NOTE]
>Python installation for windows systems please use the [python installation guide](https://www.python.org/downloads/windows/)
>or recommend use the [Linux Subsystem WSL](https://learn.microsoft.com/de-de/windows/wsl/install)

Python Virtualenv

It is also recommended to use virtual environments, here as an example for
Linux and MacOS:

```bash
python3 -m venv oscli
source oscli/bin/activate
pip install --upgrade pip
pip install python-openstackclient \
python-cinderclient \
python-designateclient \
python-glanceclient  \
python-neutronclient \
python-novaclient \
python-octaviaclient \
python-barbicanclient

```

For further Information see the OpenStack Project upstream website
[python-openstackclient](https://docs.openstack.org/python-openstackclient/latest/index.html).

This repo holds examples for [clouds-public.yaml](clouds-public.yaml) + [clouds.yaml](clouds.yaml.sample).

Alternatively you can download an OpenRC Environment file when you're logged
in to Horizon:

- upper right side :arrow_right: `<your login name>`
- OpenStack RC File

```bash
$ source ./<your file>-openrc.sh
Please enter your OpenStack Password for project XXX as user YYY:
```

```bash
openstack --help
```

when you're using clouds.yaml you can specify multiple endpoints and
select the specific endpoint by passing `--os-cloud=` to the
openstack cmdline or setting `OS_CLOUD`.

```bash
openstack --os-cloud MYCLOUD
```

or

```bash
export OS_CLOUD=MYCLOUD
openstack
```

OpenStack Client in action inside of the OSISM testbed:
![Example OpenStackClient in testbed](getting_started_openstack_anim.gif)

## Object Storage (S3)

Create AWS like credentials with `openstack ec2 credentials create`.
If you use libs3, store the access field in `S3_ACCESS_KEY_ID` and the secret
field in`S3_SECRET_ACCESS_KEY` and set `S3_HOSTNAME=<Object Storage endpoint>`.
You will see the same buckets (containers) and objects whether you access your
object store via the swift or via the s3 protocol.

## References

- [OpenStack](https://www.openstack.org "OpenStack Site")
- [SovereignCloudStack](https://github.com/SovereignCloudStack "SovereignCloudStack on github")
- [OSISM](https://github.com/osism "OSISM on github")
- [ansible](https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html "Ansible Module OpenStack")
- [terraform](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs "OpenStack Terraform Provider")
- [cloud-init](https://cloudinit.readthedocs.io/en/latest/ "cloud-init documentation")
