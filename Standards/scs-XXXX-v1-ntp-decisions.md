---
title: Recommendations on VM clock synchronization
type: Decision Record
status: Draft
track: IaaS
---

## Abstract

The system clocks of virtual machines may drift over time, and will also be affected by pausing or migrating the VM.
Ensuring a correct system time usually requires synchronization with an external time source.
There are multiple options for VM clock synchronization which this document will explore and evaluate for use in SCS clouds.

## Terminology

Example (abbr. Ex)
  This is the description for an example terminology.

## Context

Correct system time is important for the validation of TLS certificates and corelation of log entries across multiple systems.
It is common practice to syncronise the system clock of VMs with a public time server via the NTP protocol.
However, using public NTP servers may reduce the clock precision of the synchronized system due to network latency.
It will also expose small bits of information (mainly the existence of the system) to the operator of the NTP server, and it excludes systems that are not connected to the internet.

There are multiple options available to synchronize clocks with a time source local to the CSP:
* The CSP may provide a local static NTP service that is reachable from VMs via a provider entwork.
* The CSP may inject an NTP server into project subnets, like OpenStack injects DHCP servers and the metadata service IP.
* Some hypervisors support synchronisation of the guest clock with the clock of the host. CSPs could support this feature.

If the CSP chooses to provide an NTP server, there are also multiple ways in which VMs can be configured to use this feature.
* DHCP
* OpenStack Vendordata
* Modification of cloiud images

## Decision

Independently of the choosen method of clock synchronization, CSPs should make sure that they are available to VMs with as little user interaction as possible.
This is of course somewhat dependent on the guest operating system, and CSPs should validate that the provided methods of clock synchronization cloud are compatible with the provided cloud images.

The great benefit of Hypervisor-based clock synchronisation is that it works independent of network connectivity.
If this feature is well supported by the used hypervisor, it should be enabled by the CSP, though CSPs must take care that the clock source of the hypervisor is itself synchronized to a precise clock source.

CSPs should also provide a local static NTP server that is reachable via a default external network, and should be provided to VMs as vendordata via metadata service or config drive, as this is supported by cloud-init, which is the de facto standard for VM configuration.
The NTP server can optionally also be provided via DHCP, but not all standard cloud images enable NTP configuration via DHCP.
Generally, the CSPs should not modify third-party cloud images to hard-code local NTP servers, as there are a lot of benefits to supporting unmodified standard images.

Injecting NTP servers into subnets is not something that is currently supported by OpenStack, but should be possible to implement in a similar fashion to subnet-DHCP, or the metadata service.
If this feature becomes available at a later date, CSPs should prefer it to a static local NTP server, as it also supports isolated subnets.

## Consequences

What becomes easier or more difficult to do because of this change?

## Related Documents

Related Documents, OPTIONAL
