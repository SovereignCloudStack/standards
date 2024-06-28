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

Correct system time is important for the validation of TLS certificates and correlation of log entries across multiple systems.
To counteract drifting of the system time, it is common practice to syncronise servers to a public time server via the NTP protocol.
This requires access to the internet, however, and the network latency encountered when connecting to a public NTP server may reduce the clock precision.
Communicating with an external NTP server will also expose small bits of information (mainly the existence of the system) to the operator of the time server.

Ideally, the CSP would provide a means of time synchronization to servers, so that no outward NTP traffic is necessary.
Doing so comes with two challenges:
1. Providing an apropriate method of time synchronization. This could be NTP, PTP, hardware clock emulation or para-virtualization.
2. Getting guest servers to actually use the provided time synchronization method. This may involve preconfigured images, DHCP, cloud metadata, or user documentation.

The options for configuring time synchronisation in guests are often dependant on the method of synchronisation, so it makes most sense to discuss them in that context.

### RTC emulation

Since their early days, IBM-compatible PCs have included a battery-backed real-time clock (RTC).
Originally this was the MC146818 CMOS clock, which was able keeps track of seconds, minutes, hours, days, months, and years.
As other manufacturers replicated the interface of the chip, it became a defacto standard and is supported by practically all operating systems designed to run on a PC platform.

Qemu supports emulation of a MC146818-compatible clock that will by default replicate the host's system time, but can also set to run independently (which will also keep the time from moving on for suspended guests).
If the host itself is synchronized to an acurate time source, then the emulated RTC of the guest will be equally accurate.

The benefits of an emulated RTC are its wide support among guest operating systems and it's independence from network connectivity.

The main disadavantage is it's low resolution of only one second.
Linux will typically initialize the system time on boot using the RTC and then use a higher resolution clock source (like the CPU's timestamp counter) to advance the system time without resyncing with the RTC.
It is possible to resync the system time to the RTC, but that appears not to be default behavior, so any outside time corrections would typically be lost on a running system.

Another drawback of RTC emulation is it's reliance on the hypervisor, though it seems likely that other hypervisors besides KVM/Qemu would have similar features.

### NTP/SNTP

The Network Time Protocol (NTP) is a UDP-based protocol used to synchronize time between a client and one or multiple servers.
NTP will transmit the current time of the server, but also try to determine and correct for the transmission delay.
Out of multiple time servers, it will try to select the most accurate one.
Depending on the network distance of the time server and factors such as network congestion, NTP can achive acuracy from 100ms down to less then 1ms.

The Simple Network Time Protocol (SNTP) is a simplified (but compatible) subset of NTP that only allows synchronization to a single server and is generally less acurate.

Most ready-made cloud images will include an NTP client (typically _chrony_), or at least an SNTP client (typically _systemd-timesyncd_), with a preconfigured public NTP server or server pool.
They will mostly also accept NTP servers supplied via DHCP, which allows CSPs to automatically provide their own local NTP servers for improved accuracy.
This will not work in all cases though, because Openstack supports the configuration of servers without DHCP, and also because the OVN implementation of DHCPv6 is still missing support for providing NTP servers.

If servers are configured without DHCP, they must get their network configuration from the metadata provided via config drive.
There is currently no standardized field to supply NTP servers in either Openstacks own metadata format, or the EC2 Format which Openstack also supports.

Openstacks own metadata format also supports vendor data, which is an unstructured JSON document that can be used to pass CSP-specific information to servers.
This document could be used to communicate local NTP servers, though there is currently no established format for this.
Cloud-init does support embedding its own _cloud-config_ format into openstack vendor data, which does in fact have support for configuring NTP.
However, this feature is rather intrusive, as cloud-init will try to install NTP client packages if it finds that none are present in the system.

Some IaaS providers, such as AWS and GCP, will provide their own NTP servers to VMs under a fixed link-local IP address, which are often preconfigured in images targeting those platforms.

### PTP

(TBD)

### Paravirtualization

(TBD)

## Decision

(TODO: discuss different approaches for provider images and user images)

Independently of the choosen method of clock synchronization, CSPs should make sure that they are available to VMs with as little user interaction as possible.
This is of course somewhat dependent on the guest operating system, and CSPs should validate that the provided methods of clock synchronization cloud are compatible with the provided cloud images.

The great benefit of Hypervisor-based clock synchronisation is that it works independent of network connectivity.
If this feature is well supported by the used hypervisor, it should be enabled by the CSP, though CSPs must take care that the time source of the hypervisor is itself synchronized to a precise time source.

CSPs should also provide a local static NTP server that is reachable via a default external network, and should be provided to VMs as vendordata via metadata service or config drive.
The NTP server can optionally also be provided via DHCP, but not all standard cloud images enable NTP configuration via DHCP.

Injecting NTP servers into subnets is not something that is currently supported by OpenStack, but should be possible to implement in a similar fashion to subnet-DHCP, or the metadata service.
If this feature becomes available at a later date, CSPs should prefer it to a static local NTP server, as it also supports isolated subnets.

## Consequences

What becomes easier or more difficult to do because of this change?

## Related Documents

Related Documents, OPTIONAL
