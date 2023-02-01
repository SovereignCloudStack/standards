# Quickstart

This quickstart guide will upload a single, small, private image to your OpenStack.

## Installation

First, you need to install the openstack-image-manager. You can either use pip:

```sh
pip3 install openstack-image-manager
```

Or you can clone the repository and run it via `tox`:

```sh
tox -- --help
```

## Uploading an image to your OpenStack

To be able to upload an image to your OpenStack, you need to have at least one config file.

### Create a config

Create a config file ending with _.yml_ in a directory, e.g. _~/images_

```yaml
---
images:
  - name: MyCirros
    format: qcow2
    login: cirros
    password: gocubsgo
    min_disk: 1
    min_ram: 32
    status: active
    visibility: private
    multi: false
    meta:
      architecture: x86_64
      hw_disk_bus: scsi
      hw_rng_model: virtio
      hw_scsi_model: virtio-scsi
      hw_watchdog_action: reset
      os_distro: cirros
      replace_frequency: never
      uuid_validity: none
      provided_until: none
    tags: []
    versions:
      - version: '0.6.0'
        url: https://github.com/cirros-dev/cirros/releases/download/0.6.0/cirros-0.6.0-x86_64-disk.img
        checksum: "sha256:94e1e2c94dbbae7d4bdc38e68590a1daf73c9de2d03dd693857b4b0a042548e8"
        build_date: 2022-09-28
```

### Run the image manager

Run the manager against an OpenStack cloud (here called _my-cloud_).
Only run it against config files where the name matches _Cirr_.
Also provide the location of your image files (_~/images/_).

```bash
openstack-image-manager --cloud my-cloud --name "*Cirr*" --images ~/images/
```

