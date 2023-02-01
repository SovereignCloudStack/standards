# Getting started

## Functions of the OpenStack Image Manager

All commands below are executed in this pattern:

```bash
tox -- <command> [parameters]
```

With _command_ beeing one of the options shown below.

As you can do many things with this manager here a list with possible commands:

### manage (main)

|Parameter                        |Description|
|---------------------------------|-----------|
|`--debug`                        |Enables debug messages|
|`--dry-run`                      |Perform a dry run without any changes|
|`--latest`                       |Only import latest image versions into your openstack.|
|                                 |Only applies to images that are of type multi.|
|`--cloud openstack`              |The cloud you are working on|
|                                 |Default value is **openstack**|
|`--images etc/images/`           |Location of the image configuration files|
|                                 |Default value is **etc/images/**|
|`--name foo`                     |Name of the affected image|
|`--tag foo`                      |Manage only images from your OpenStack that match the given tag.|
|                                 |Default value is **managed_by_osism**|
|`--filter foo`                   |Use only images from image config files, that apply to this regex filter|
|`--deactivate`                   |Deactivates an image. You cannot create a VM of this image any longer.|
|`--hide`                         |Hide images. You can still use the ID to create a VM of this image.|
|`--delete`                       |Delete outdated images. Only removes images, that are not used by any VM or snapshot any more.|
|`--yes_i_really_know_what_i_do`  |Force delete an image. VMs using that image will break.|
|`--use_os_hidden`                |Also manage hidden images in your OpenStack|
|`--check`                        |Check your OpenStack images metadata against the SCS standards.|
|                                 |Gives you a detailed list of missing metadata.|
|`--validate`                     |Validate your image config files metadata against the SCS standard.|
|                                 |Gives you a detailed list of unvalid metadata.|

Main command. Works through the image config files and applies the changes to your OpenStack as desired.

#### Validate config

After a change to the configuration, validate it with **tox -- --dry-run**.

#### Cloud Name

The cloud environment to be used can be specified via the **--cloud** parameter. The default-value is: **openstack**
The path of the **clouds.yaml** file to be used can be set via the environment variable: **OS_CLIENT_CONFIG_FILE**

#### Location of images

The path to the definitions of the images is set via the parameter **--images**. The default-value is: **etc/images/.**

#### Naming Convention

* Names must be unique
* Use the full name of the product / distribution, no shortcuts

Samples:

* _Ubuntu 16.04_
* _CoreOS_

#### Filter images

If you wanna use only images from a special filter use regex to find them: tox -- --filter 'Debian*'

#### Delete images

Simply remove the version of an image you want to delete or the entire image from **etc/images/.** or use **tox -- --delete --name foo**

#### Delete images fully

The deletion of images must be explicitly confirmed with the **--yes_i_really_know_what_i_do** parameter.

```bash
tox -- --delete --yes_i_really_know-what_i_do
```

#### Change the tag of the managed images

* old tag: **managed_by_betacloud**
* new tag: **managed_by_osism**

```bash
openstack --os-cloud service image list --tag managed_by_betacloud -f value -c ID | tr -d '\r' | xargs -n1 openstack --os-cloud service image set --tag managed_by_osism
```

```bash
openstack --os-cloud service image list --tag managed_by_betacloud -f value -c ID | tr -d '\r' | xargs -n1 openstack --os-cloud service image unset --tag managed_by_betacloud
```

### Add new images

Only freely accessible community images may be added. Currently, the decompression of images, as with CoreOS, is not supported.
If there is no section for the product / distribution then create it accordingly. Explicitly mark **os_version** as a string to prevent
evaluation as a double.
Useful metadata keys can be found at: <https://docs.openstack.org/glance/latest/admin/useful-image-properties.html>
Possible values for **os_distro** can be found in [libosinfo](https://gitlab.com/libosinfo/osinfo-db/tree/master/data/os) or
**osinfo-query os** (omit **os_distro** if there is no meaningful value for it).
**min_disk** and **min_ram** should always be specified. Keys do not have to be set, by default the values are 0.
At **login** specify the user with whom you can log in after the initial start. This is necessary for the generated documentation as well
as later automatic tests.
Special images offer the login via a password. This can be specified via the parameter **password**.

### mirror

|Parameter                        |Description|
|---------------------------------|-----------|
|`--debug`                        |Enables debug messages|
|`--dry-run`                      |Perform a dry run without any changes|
|`--images etc/images/`           |Location of the image configuration files|
|                                 |Default value is **etc/images/**|
|`--minio_access_key foo`         |S3 access key|
|`--minio_secret_key bar`         |S3 secret key|
|`--minio_server http://localhost`|Hostname of the S3 backend|
|`--minio_bucket images`          |Bucketname where the images are stored|

All images that are configures in the images config files are downloaded from upstream. After downloading they might be decompressed
(only applies to _bz2_, _zip_ and _xz_ files). Now they are uploaded into the S3 backend. Remaining local files are removed.

### share

|Parameter                 |Description|
|--------------------------|-----------|
|`--dry-run`               |Perform a dry run without any changes|
|`--action add`            |Either _add_ (default) or _del_ as valid options.|
|                          |Defines if the image is shared or unshared.|
|`--cloud openstack`       |The cloud you are working on|
|`--image Cirros`          |Name of the affected image|
|`--project_domain default`|Defines the OpenStack domain|
|`--target`                |Defines the OpenStack project|
|`--type`                  |Either _project_ (default) or _domain_ as valid options.|
|                          |Defines the scope where the image is (un)shared.|

Makes an image available (or unavailable). This can happen on a single project or on all projects of a domain.

### table

|Parameter             |Description|
|----------------------|-----------|
|`--images etc/images/`|Location of the image configuration files|
|                      |Default value is **etc/images/**|

Prints out a list of all images configured in the provided image config path providing login user and password for the respective image.
Example output:

```sh
tox -- table --image etc/images/
=======================  ============  ==========
Name                     Login user    Password
=======================  ============  ==========
AlmaLinux 8              almalinux
AlmaLinux 9              almalinux
CentOS 7                 centos
CentOS Stream 8          centos
CentOS Stream 9          centos
Cirros                   cirros        gocubsgo
Clear Linux              root
Debian 10                debian
Debian 11                debian
Fedora 36                fedora
Fedora CoreOS            root
Flatcar Container Linux  root
Garden Linux             admin
Kubernetes CAPI          ubuntu
OPNsense                 root          opnsense
Rocky 8                  rocky
Rocky 9                  rocky
Ubuntu 14.04             ubuntu
Ubuntu 16.04             ubuntu
Ubuntu 16.04 Minimal     ubuntu
Ubuntu 18.04             ubuntu
Ubuntu 18.04 Minimal     ubuntu
Ubuntu 20.04             ubuntu
Ubuntu 20.04 Minimal     ubuntu
Ubuntu 22.04             ubuntu
Ubuntu 22.04 Minimal     ubuntu
openSUSE Leap 15.4       opensuse
=======================  ============  ==========
```

### update

|Parameter                        |Description|
|---------------------------------|-----------|
|`--debug`                        |Enables debug messages|
|`--images etc/images/`           |Location of the image configuration files|
|                                 |Default value is **etc/images/**|
|`--minio_access_key foo`         |S3 access key|
|`--minio_secret_key bar`         |S3 secret key|
|`--minio_server http://localhost`|Hostname of the S3 backend|
|`--minio_bucket images`          |Bucketname where the images are stored|

Compares the upstream checksum of an image with the checksum provided in the image config files. If they differ, the new checksum updated
in the image config files. Additionally, the new image is downloaded to the S3 server. When the image is in a _bz2_, _zip_ or _xz_ format,
it gets extracted before uploading.

### Outdated image handling

> **note:** By default outdated images are renamed but will stay accessable. There are 3 ways to handle outdated Images:
> hide, deactivate + delete
