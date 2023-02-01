# Configuration

The configuration consists of different parameter settings, such as values for minimum RAM or the visibility of the image. Have a look at
the example below for all parameters. After a change to the configuration, validate it with **tox -- --dry-run**.

## Image with regular rebuilds

> **caution:** multi: true

```yaml
...
  - name: Ubuntu 16.04
    format: qcow2
    login: ubuntu
    min_disk: 8
    min_ram: 512
    status: active
    visibility: public
    multi: true
    meta:
      architecture: x86_64
      hw_disk_bus: scsi
      hw_scsi_model: virtio-scsi
      hw_watchdog_action: reset
      os_distro: ubuntu
      os_version: '16.04'
    tags: []
    versions:
      - version: '20180928'
        url: https://cloud-images.ubuntu.com/xenial/20180928/xenial-server-cloudimg-amd64-disk1.img
      - version: '20181004'
        url: https://cloud-images.ubuntu.com/xenial/20181004/xenial-server-cloudimg-amd64-disk1.img
...
```

This configuration creates the following images:

* **Ubuntu 16.04 (20180928)**
* **Ubuntu 16.04**

If a newer build is added, the following rotation takes place:

* **Ubuntu 16.04** becomes **Ubuntu 16.04 (20181004)**
* the new image becomes **Ubuntu 16.04**

>**note:** last 3 images will be used see [osism/openstack-image-manager/issue#51](https://github.com/osism/openstack-image-manager/issues/51)

## Image without regular rebuild

> **caution:** multi: false

```yaml
...
  - name: RancherOS
    format: qcow2
    login: rancher
    min_disk: 8
    min_ram: 2048
    status: active
    visibility: public
    multi: false
    meta:
      architecture: x86_64
      hw_disk_bus: scsi
      hw_scsi_model: virtio-scsi
      hw_watchdog_action: reset
    tags: []
    versions:
      - version: '1.3.0'
        url: https://github.com/rancher/os/releases/download/v1.3.0/rancheros-openstack.img
      - version: '1.4.0'
        url: https://github.com/rancher/os/releases/download/v1.4.0/rancheros-openstack.img
      - version: '1.4.1'
        url: https://github.com/rancher/os/releases/download/v1.4.1/rancheros-openstack.img
...
```

This configuration creates the following images:

* **RancherOS 1.3.0**
* **RancherOS 1.4.0**
* **RancherOS 1.4.1**

If a new version is added, no rotation takes place. The new version is added
as **RancherOS x.y.z**.

>**note:** last 3 images will be used see [osism/openstack-image-manager/issue#51](https://github.com/osism/openstack-image-manager/issues/51)

## Modify image properties

* Removal of properties is not yet possible
* URL, name and format can not be changed
* Any keys can be added to **meta**, these will be added to the image
* Existing keys in **meta** can be changed, the same applies to **min_disk**
  and **min_ram**

## Modify image tags

You can tag images like described in the Usage section or you can add or remove tags to the **tags** list.

## Deactivate/reactivate image

* deactivation: change **status** to **deactivated**
* reactivation: change **status** to **active**

Also you can deactivate images like described in the Usage section.

## Visibility

A full documentation about the visibility of images you can find in the
[OpenStack API Documentation](https://developer.openstack.org/api-ref/image/v2/index.html) --> **Image visibility**

* public: set **visibility** to **public**
* community: set **visibility** to **community**
* shared: set **visibility** to **shared**
* private: set **visibility** to **private**
