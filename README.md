# SCS Documentation
Entry point for SCS Docs

# What is SCS? Why should I care?

# Get it and test it: Testbed
The easiest way to get in touch with SCS is to deploy an SCS cloud virtually.

This means that you set up an SCS test installation including all the infrastructure
pieces such as database, message queueing, ceph, monitoring and logging, IAM, the
[OpenStack](https://openstack.org/) core services, and (soon) the Container layer 
on top of an existing
IaaS platform. Currently, only OpenStack is supported as IaaS under the SCS cloud
(so you end up using OpenStack on top of OpenStack -- with nested virtualization
enabled, this performs decently). There is no fundamental limitation -- just
noone has done the porting if the terraform recipes to AWS, libvirt, VMware, ...

SCS is based on [OSISM](https://osism.tech/). Read on the 
[OSISM testbed docs](https://docs.osism.de/testbed/) to learn how to get the
testbed running.

Hint: If you are using one of the supported clouds

# Existing SCS Clouds
A few production clouds are already based on SCS: betacloud and PlusCloud Open.
More will come soon. There is also a how to 
[get started guide for PlusCloud](https://github.com/SovereignCloudStack/documentation/blob/master/GettingStarted.MD)

CityNetwork, Open Telekom Cloud, OVH clouds are also known to support the
testbed well. (There are a few caveats with the latter two, but those are
documented and no blockers.)

# Releases and Roadmap

# Contribute and Connect

# Standards, Conformity and Certification

# Issues and bugs

# Other resources
