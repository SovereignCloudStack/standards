# Adaption costs for SCS standards

This document outlines the adaption costs for the IaaS/OpenStack standards of the SCS project. Tests and estimates were
done using Yaook especially `yaook/k8s` and `yaook/operator` which together provided a functioning OpenStack instance.
Nonetheless, other OpenStack types should have similar costs for adapting standards, since in the end, the frontend
is an OpenStack.

## Standards

### SCS Flavor Naming Standard (scs-v100-v3-flavor-naming)

The [SCS Flavor Naming Standard (scs-v100-v3-flavor-naming)](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-v100-v3-flavor-naming.md)
requires all flavors starting with `SCS-` to follow a certain schema in order to apply with the standard.
Flavors required by [SCS Standard Flavors and Properties (scs-0103-v1-standard-flavors)](#scs-standard-flavors-and-properties-scs-0103-v1-standard-flavors)
and created with the ["osism-flavor-manager"](https://github.com/osism/openstack-flavor-manager) already comply to this flavor naming.

It is a bit more complicated for flavors not included in the standard flavors. A CSP would need to decide if he wants
to add additional flavors, especially if he provides some not yet covered by the standard flavors.
A CSP could decide to only provide a part of their flavors, since complete adoption could be a quite demanding process.

The biggest time consumption for non-standard flavors would be the correct naming of the flavors.
This could be assisted by different tools, like the ["Flavor Site"](https://flavors.scs.community) (if available), which
could reduce the time spent on research and information retrieval for this standard.

Time for these scales linearly with the number of non-standard flavors that need to be named.

Estimated cost: 1 man-hour + 5 minutes for every flavor

### SCS Entropy Standard (scs-0101-v1-entropy)

The entropy standard mainly defines recommended flavor attributes to be available and also requires a high enough and
consistent entropy to be available for all possible flavors. This is primarily tested with "FIPS 140-2 failures" as well
as the entropy count available under `/proc/sys/kernel/random/entropy_avail`.
This is mostly the case on modern linux kernels (especially on 5.18 or higher), but if older kernels are made available,
the CSP needs to provide entropy by offering CPU instructions that provide entropy without being filtered by the hypervisor.

All newer CPUs offer instructions for this kind of use-case (e.g. Intel introduced RDRAND in 2014 in their Broadwell architecture)
and the expectation is, that most CSPs don't use older processors.

The only scenario with slightly higher adaption costs would be a CSP with old hardware and a customer that requires
systems with old kernels. The cost here would probably be estimated on the base of moving the customer to a newer system
with support for entropy instructions on CPUs.

In a normal case though, the costs are estimated to be much lower, since they only involve labelling flavors, which
should be done in little time, especially if tools like the ["osism-flavor-manager"](https://github.com/osism/openstack-flavor-manager) are used.

Estimated cost: 1 man-hour

### SCS Image Metadata Standard (scs-0102-v1-image-metadata)

Image metadata can mostly be covered by using the ["osism-image-manager"](https://github.com/osism/openstack-image-manager) tool.
The tool expects a file containing information about the images including the metadata information required by the
SCS standards. Handling these information within a single file would be convenient and time saving, if multiple clusters
or clusters with many images need to be worked on.

A better estimate can be read in the section [SCS Standard Images (scs-0104-v1-standard-images)](#scs-standard-images-scs-0104-v1-standard-images)
due to their close interaction.

Estimated cost: 1-2 man-hours (already included in [SCS Standard Images (scs-0104-v1-standard-images)](#scs-standard-images-scs-0104-v1-standard-images))

### SCS Standard Flavors and Properties (scs-0103-v1-standard-flavors)

The expected flavors with correctly standardized names and properties can simply be created and updated
by using the ["osism-flavor-manager"](https://github.com/osism/openstack-flavor-manager) tool.
Using the tool with the command `openstack-flavor-manager --name scs --recommended` simplifies the whole process
down to a simple command in addition to the previous installation.

The costs for this are very small and can be estimated with a maximum of one hour.

If a manual approach is taken, a maximum of eight hours can be estimated. In this case, it would already be recommended
to create a simple (bash) script in order to automate the process internally for future usage in setups.

Estimated cost: 1 man-hour

### SCS Standard Images (scs-0104-v1-standard-images)

The expected images with correctly standardized names and properties can simply be created and updated
by using the ["osism-image-manager"](https://github.com/osism/openstack-image-manager) tool.
The `openstack-image-manager` expects a file containing information about the images. This isn't provided by the SCS
project, but can be derived from the information available in the standard documents. Through this mechanism, the
`openstack-image-manager` also enables the adaption of the "SCS Image Metadata Standard (scs-0102-v1-image-metadata)".

This project provides an `images.yaml` file containing the standard images expected by this standard in order to cut
down on future adaption costs. The file will be up-to-date with the current standard version.

Additional images must be included and their properties adapted to the needs of the provider,
which should make them SCS-compatible, if all properties listed in the `images.yaml` are set.
For more information on this read either the ["Image metadata" standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0102-v1-image-metadata.md)
or the ["SCS compliance" document](scs-compliance.md).

Using the tool with the command `openstack-image-manager --cloud CLOUD --images images.yaml` simplifies the whole process
down to a simple command in addition to the previous installation and modification of the `images.yaml`.

If the "osism-image-manager" is used, adaption should be relatively quick depending on the number of images.
Obviously a large number of images scales the time for this process linearly, so for big deployments, some additional
automation should be done.

For a simple setup with only the standard images, a maximum of two hours for standard adaption with the "osism-image-manager"
is expected.
A manual approach is not recommended, since this process would involve a multitude of OpenStack commands and could easily
take multiple days depending on the setup.

Estimated cost: 1-2 man-hours

### SSD Flavors (scs-0110-v1-ssd-flavors)

This Decision Record added new SSD flavors to the `SCS Standard Flavors and Properties (scs-0103-v1-standard-flavors)`
which requires the CSPs to provide SSDs for this flavor set. Creating the flavors itself isn't that time-consuming,
but equipping and modifying a server system to include SSDs for these flavors (if that isn't the case) could be quite
costly, especially in initial material costs and the necessity for technical work on the servers.

An estimation for this is hard, but a terabyte of SSD in the datacenter space around the time of writing this was around
130€. Installation time is dependent on the complexity of the system involved and can vary quiet a bit, but doesn't
scale linearly if multiple SSDs need to be installed. Due to the scale of variation, no man-hour estimation will be done
here for the hardware part.

Estimated cost: 1 man-hour (just for the flavors)

## Summary

In summary, a time of 4 man-hours up to multiple days can be estimated depending on the size of the deployment and the
usage of tools for automating this process.
Multiple adaptions can decrease the time required on subsequent runs.
