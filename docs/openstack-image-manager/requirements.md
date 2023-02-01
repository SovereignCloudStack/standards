# Requirements

## OpenStack image service

The image service for OpenStack is called Glance. This service is needed to upload and discover data assets that are used by other
services. You can configure the Glance service as you need.

> **Note:**
> See upstream glance documentation for more details: <https://docs.openstack.org/glance/yoga/configuration/sample-configuration.html>

Since this script stores many images in a project, the Glance quota must be set accordingly high or to unlimited.

```ini
[DEFAULT]
user_storage_quota = 1TB
```

With most storage backends it makes sense to convert the imported images directly to RAW. So it is required for using Ceph and it´s
features too. Recited from the Ceph documentation <https://docs.ceph.com/en/latest/rbd/qemu-rbd/> and
<https://docs.ceph.com/en/nautilus/rbd/rbd-openstack/>:

>"The raw data format is really the only sensible format option to use with RBD. Technically, you could use other QEMU-supported formats
>(such as qcow2 or vmdk), but doing so would add additional overhead, and would also render the volume unsafe for virtual machine live
>migration when caching (see below) is enabled."
>
>"Important Ceph doesn't support QCOW2 for hosting a virtual machine disk. Thus if you want to boot virtual machines in Ceph (ephemeral
>backend or boot from volume), the Glance image format must be RAW."

This requires the following parameter for the image import workflow.

```ini
[taskflow_executor]
conversion_format = raw

[image_import_opts]
image_import_plugins = ['image_decompression', 'image_conversion']

[image_conversion]
output_format = raw
```

## S3 storage backend

If the mirror functionality is used, an S3 storage backend is required. The use of the mirror functionality is optional and is not
used by default. S3 Storage Backend can store files without a size limitation. It is accessible via APIs.
With S3, among other things, versioning and fine grained access rights can be configured.

Therefore, no S3 storage backend is required to use the OpenStack Image Manager.
