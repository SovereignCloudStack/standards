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

Cloud-init does support embedding its own _cloud-config_ format into openstack vendor data, which does have support for configuring NTP.
This feature is rather intrusive, however, as cloud-init will attempt to install NTP client packages if it finds that none are present in the system.

Some IaaS providers, such as AWS and GCP, will provide their own NTP servers to VMs under a fixed link-local IP address, which are often preconfigured in images targeting those platforms.

### PTP

The Precision Time Protocol (PTP) is, like NTP, a network-based time synchronization protocol, that supports both UDP and ethernet transports.
PTP is designed to offer higher precision than NTP, particularly in local area networks, e.g. by measuring the timing of synchronization messages directly at the network interface, if supported.
Master clocks will also continually broadcast synchronization messages to their network, making them discoverable for clients, but also generating more traffic than NTP.

Linux has a kernel-based driver for PTP, which will provide the synchronized time through a device file, which can then be used by services such as _phc2sys_ or _chrony_ to update the system time.

It is unclear if PTP would have offer any better precision than NTP in tunneled networks with virtual interfaces, and it does not seem to get any use in IaaS at all.

### Paravirtualization

Unlike PTP as a protocol, it's driver interface in Linux seems to be a popular choice for time synchronization in the form of paravirtualization.
The _ptp\_kvm_ kernel module will communicate directly with the KVM hypervisor to provide a PTP device file that follows the system time of the host.
Hyper-V also offers time synchronization through a PTP device file, managed by its _Linux Integration Services_.

Paravirtualized time synchronization has the benefit of generally offering the highest precision.
Like RTC clock emulation, it also works independently of the guest system's network connectivity.
The main drawback is the dependency on a specific combination of hypervisor and guest operating system, because it requires hypervisor-specific drivers to run in the guest.

## Decision

From looking at the available options, it becomes apparent that there is no single optimal solution for time synchronization.
The most precise option is the least portable, but the most widely supported option also requires the most provider-specific configuration.

The aim of SCS is to improve interoperability between Openstack clouds, so the preferable standard solution is one that works across a wide range of setups.
This perspective clearly favours NTP as a standardized method of time synchronization, because of it's wide support in cloud images and it's independence from other components, such as the hypervisor.

However it is still useful for a CSP to offer less portable, but more precise methods of time synchronization, especially if they are integrated into the default cloud images offered by the CSP.

So, we should standardize a portable NTP setup that users can assume when developing images to work well in any SCS cloud.
We should not try to prevent CSPs from supporting paravirtualized or other methods of time synchronization that may offer significant benefits over NTP.

## Consequences

A standardized NTP setup will allow SCS users and third party image providers to develop images that support local time synchronization accross SCS clouds.

As discussed in the NTP section above, there are a number of limitations in OpenStack and related projects that a standardized NTP setup has to work with:

* OpenStack currently has no support for providing NTP servers to VMs under a fixed link-local address, like AWS and GCP are doing.
  Such a feature could probably be implemented by re-using the metadata service IP (`169.254.169.254`) and the mechanisms to inject it into subnets.
  If this feature becomes available in the future, it will be an attractive target for standardization, but until then it seems more sensible to focus on servers available through provider networks.
* Making NTP servers accessible via provider networks will limit availability to those VMs that are connected to the provider network, either directly or via a virtual router
* Without mandating fixed IP addresses or domain names for local NTP servers, CSPs will need a method of informing VMs of available NTP servers.
  DHCP is the currently best supported mechanism for this, but is not guaranteed to be available to VMs, as users may disable it for their subnets.
  Also, OVN's DHCPv6 implementation currently does not support the required option, but that seems to be a relatively straightforward feature to add.
* The alternative to DHCP is of course the metadata service, though there is currently no standard field for providing NTP servers.
  Cloud-init's proprietary format may not be good option because of the automatic package installation in guests, but any other option will require support to be added to whatever init tool is used.
  A new NTP server key in OpenStack's standard metadata will require upstream changes, but is more likely to get supported by cloud-init or other init tools (though most seem to focus exclusively on the EC2 format).
  A custom key in the vendor data could just be defined in the standard, but would be less likely to get support by any third party tools, and thus only be useful with custom scripts or init-tool plugins.

## Related Documents

Related Documents, OPTIONAL
