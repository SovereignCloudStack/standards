# Overview

<!---**ToDo**: Image/Map SCS context-->

The OpenStack Image Manager is an easy to use Application for managing all images in the OpenStack horizont.

## Mirroring of images

Since the upstreams often only keep their images for a short time, we mirror most of the images on our **minio.services.osism.tech**
mirror. This makes us independent of the availability of the images in the individual upstreams.

## Updating images

Some of the images are automatically updated by a CI job. The latest available build at the time of the CI job execution is mirrored and
made available as the current version.

Currently, the following images are updated once a week (every Sunday at 0 am):

* Almalinux
* CentOS
* Debian
* Rockylinux
* Ubuntu

## Mapping to SCS Image Metadata

The value of **login** is stored as **image_original_user** in the metadata of an image.

If **image_description** is not set as meta information, **image_description** is set to the name of the image.

The value of **build_date** of a specific version of an image is stored as **image_build_date** in the metadata of an image.

The value of **url** of a specific version of an image is stored as **image_source** in the metadata of an image.
