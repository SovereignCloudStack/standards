---
title: SCS Image Crawler - Dynamic upstream by metainformation of versions
version: 2023-003-28-001
authors: Mathias Fechner, Benjamin Zapiec
effective-date: 2023-03-28
state: Released (v0.1)
---

# Dynamic upstream by metainformation of versions

Keep the images and their metadata up to date.
Automatically fetch new images if available and push them to your image repository.

## CSP point of view
As a CSP we want and need to provide up to date images as they are the basis for IaaS in
virtualized environments and for bare metal installations. There will be a variety of several different
images that won't be included into a given standard. On the other hand it gains some convenience for CSPs and
customers providing some "base" images. From the CSP point of view it is not necessarily important
which images to provide but how to keep them up to date. Unlike containers, that may depend on a
given container image, there is not the exact same use case to pin a virtualized service
to a specific version of an image. 

E.g. Ubuntu 22.04.2 will most likely work for your workload as Ubuntu 22.04.1 did.

Even though there might be a use case for minor versions to exist separately there is one
point where the distributor may fix an image containing some security flaws without
increasing the overall version string. So we always want to provide the most recent Ubuntu 22.04(.2)
to our customers. Keep the images up to date is what we want to achieve.

## Customer point of view

Customers will most likley not be interested in the exact build version for an image.
Building a service on top of Debian Bookworm means, that the customer will choose
Debian Bookworm and not Debian Bookworm 20221214-1234 for deployment. Special interest 
by the customer can be addressed with separate image upload mechanisms.

# Challenges
## Image crawling

There is no standardized way to fetch the latest version
for any distribution you would like to provide. That means
we need to maintain the mechanisms to fetch the latest 
version of our mandatory images. In many cases there is some
sort of change-log or meta information available. These information
can be used to create the appropriate download URL.

## Metadata for images

Fetch a new image an upload to your image repository is just one part.
Since we want to provide some metadata regarding to the image this
information needs to be refreshed if a new image version is uploaded.

## Proposal for a collection of default images (tbd)

### Mandatory images

1. LTS Ubuntu <LATES_LTS> <PREV_LTS>
* https://cloud-images.ubuntu.com/jammy/current/
* https://cloud-images.ubuntu.com/releases/streams/v1/com.ubuntu.cloud:released:download.json
2. Debian <_STABLE>
* https://cloud.debian.org/images/cloud/bullseye-backports/latest/debian-11-backports-genericcloud-amd64.json 
3. Alma Linux 8,9 (TBD)
* https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/
* https://repo.almalinux.org/almalinux/9.1/metadata/x86_64/images.json
* https://repo.almalinux.org/almalinux/9.1/metadata/x86_64/composeinfo.json

### Optional or suggested images:
1. Debian <PREV_STABLE>
2. CentOS 8,9 stream
3. Rocky 8,9
* https://rockylinux.org/download
* https://download.rockylinux.org/pub/rocky/8/images/x86_64/
* http://download.rockylinux.org/pub/rocky/imagelist-rocky
4. Fedora <_LATEST>
* https://mirrors.xtom.de/fedora/releases/37/COMPOSE_ID
5. SLES 15SP4
* https://download.opensuse.org/repositories/Cloud:/Images:/
* https://download.opensuse.org/repositories/Cloud:/OpenStack:/
6. RHEL 9, RHEL 8
7. Windows Server 2022, Windows Server 2019
8. openSUSE Leap 15.4
9. Cirros 0.5.2 (for internal use cases)
* https://github.com/cirros-dev/cirros/releases/
10. Alpine (none Cloud-init ready ) 3.16.x 3.17.x
* https://www.alpinelinux.org/posts/Alpine-3.14.9-3.15.7-3.16.4-released.html
* https://www.alpinelinux.org/
* https://www.alpinelinux.org/releases/
* https://gitlab.alpinelinux.org/alpine/cloud/alpine-cloud-images
11. Arch Linux

## Proposal

Since there is no "one fits all" solution for this it may be interesting
if we could use CI/CD (e.g. Zuul) to build the images in standardized way.
That could avoid "guessing" the right URL for some images an may also
provide additional capabilities. Especially when it comes to different instruction set architectures.
