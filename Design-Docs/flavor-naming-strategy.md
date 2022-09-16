---
title: SCS Flavor Naming Strategy
version: 2022-09-16-001
authors: Kurt Garloff
state: draft
---

Standardizing the flavor naming has created some discussions in the SCS and the
broader OpenStack community. This is ongoing and we may not have responded well
to all points yet. This document explains some of the thoughts and learnings
and is supposed to serve as starting point for further discussions.

## Why encoding all the details in a flavor name?

The [SCS flavor standard](https://github.com/SovereignCloudStack/Docs/blob/main/Design-Docs/flavor-naming.md)
allows to encode a lot of details about the properties of a flavor into the name.
Why put it all in the name?

By putting the details in the name, two things are achieved:
* We create transparency about the detailed properties of a flavor
* We allow customers to explicitly chose these properties when starting a VM

There are better ways to creating transparency and providing discoverability than
putting standardized abbreviations into a flavor name. OpenStack flavors have metadata
called `extra_specs`, that could be further standardized to provide transparency.
Actually, we intend to do so, see below.

However, there is not a good way for users to chose the properties of a VM except
for chosing it by a flavor name. There is some possibility to have image properties
being matched with flavor `extra_specs`. It is however not reasonable for users to
register duplicated images with some extra properties just in order to select the
right flavor. Our conclusion was that flavor selection must happen by name in most
cases.

Larger cloud providers tend to offer a large variety of hardware; hardware with special
capabilities (such as e.g. GPUs), different CPU generations and speed etc. These
can be used to fulfill a very diversified set of requirements from customers.

Using arbitrary names and requiring customers to use discovery for the flavors is
an option, but it is tedious and does not integrate well with the common Infra-as-Code
tools out there. Having a way to express needs from the flavor in a cloud-neutral way
thus adds convenience.

## I don't want hundreds of flavors!

The spec allows for flavors to understate its own capabilities and does not force to
expose all details; we don't mandate the
very detailed names that encode Disk types, CPU vendor, generation, speed grade, hypervisor
into the name. Actually we explicitly recommend for flavors to be available under the
short `SCS-nV:m:l` names (with `n`, `m`, `l` being numbers that denote #CPUs, RAM in GiB
and disk size in GB resp.) and even mandate a small number of them to be available.

For providers that have moderate size and low variance in their offering, we would
actually recommend to leave it there: Keep the short names only and make the details
of what the flavors entail discoverable via the to-be-defined `extra_specs` properties.
(This is future work, see below.)

For large providers with a high variance, the long names (in addition to the short
ones) are a good way to create names that allow users to specify precisely what
flavor capabilities they want by chosing the detailed name and actually have that
work across different cloud vendors.

Horizon does not currently seem to handle very long lists of flavors so well, so
that will need work.

## The names are complex!

True. The long names take some time to get used to: To take a worst-case example:
You will need some time before
you can parse `SCS-4C:32:100s-kvm-hwv-i3h-GNa:64` into 4 dedicated cores, 32GiB
Ram, 100GB SSD on a KVM hypervisor with nested virtualization support on an intel
IceLake high clocked CPU and a pass-through nVidia Ampere GPU with 64 Compute Units
without looking it up in the Spec. You might want to throw such a name at the tool
```
./tools/flavor-name-check.py -v SCS-4C:32:100s-kvm-hwv-i3h-GNa:64
Flavor: SCS-4C:32:100s-kvm-hwv-i3h-GNa:64
 CPU:RAM: #vCPUs: 4, CPU type: Dedicated Core, ?Insec SMT: False, ##GiB RAM: 32.0, ?no ECC: False, ?RAM Over: False
 Disk: #:NrDisks: 1, #.GB Disk: 100, .Disk type: SSD
 Hypervisor: .Hypervisor: KVM
 Hardware/NestedVirtualization: ?HardwareVirt: True
 CPUBrand: .CPU Vendor: Intel, #.CPU Gen: Ice Lake, Performance: High Perf
 GPU: .Type: Pass-Through GPU, .Brand: nVidia, .Gen: Ampere, #.CU/EU/SM: 64, Performance: Std Perf
 No Infiniband
```
and learn in addition that the provider promises not to have insecure
SMT enabled or other CPU vulnerability protections turned off and
that your memory is protected by ECC or better and not oversubscribed.

You can also use the interactive mode `-i` to construct flavor names.

If you dislike the hassle of parsing the names, you may want to consider them
as opaque handles that you look up in a table from your cloud provider.
No worse than `ai1-1-GPU` ...

If you don't have complex requirements and you are looking for a flavor
with just 4 vCPUs, 16 GiB of RAM and a 50GB disk, you ask for just that: `SCS-4V:16:50`
No advanced training needed for this, no?

## I don't like exposing `i`(nsecure), `L`(ow CPU share), `u`(nprotected memory), `o`(versubscribed mem) flags!

We were considering not even allowing this ...
In the end, the market demands may be more diverse than we can imagine and there
may be scenarios, where cloud providers offer oversubscribed memory to their
customers at a good price that makes both sides happy.

However, we can not allow this not being transparent.

A flavor name carries a certain promise of what's included.
We feel a need to force transparency to create a level playing field in
our ecosystem. This is needed to ensure that users can use many cloud
operators together and find a somewhat similar level of performance.

So yes, these caveats need to be made transparent and be visible
even in the flavor name. And we will have a close look to ensure
that noone claiming SCS compliance will cheat.

## Suggested naming strategy going forward

If you are a large provider with lots of different flavors, the long `SCS-`
names allow you to offer all the variance in a systematic way. The naming is
cloud-vendor neutral, so there is a chance that users find the same flavor
names elsewhere. So we recommend to use these names. We don't mandate it -- only
the 26 mandatory `SCS-` flavors are required to be present. All names with
`SCS-` however do need to follow the SCS specification.

When you are a small provider that has not so much variance in its offerings,
we would recommend to not expose all details (hypervisor, CPU vendor and
generation, ...) via the optional name extensions. Keep your names short
by *not* encoding all features (e.g. hw virt) and technical details (e.g.
hypervisor and cpu brand and generation)
until your growth and customer demand requires a more fine-grained offering.
The spec does allow for not disclosing details and for overdelivering.

This will result in a number of flavor details not being discoverable
via the name.

We are thus intending to advance the standardization of `extra_specs`
in flavors to make all these details transparent in a standardized
way. Proposals on this will happen soon.

## Gaia-X Self-Descriptions

The Gaia-X Self-Descriptions have started with making the legal entities
behind offerings transparent. We have been contributing to pushing efforts
to also expose technical details of platforms via self-descriptions.
So this would become another avenue to provide discoverability
of the flavor properties.

Our suggested approach is to read out the platform features (the flavor properties
and `extra_specs`, also interpret the names if they are `SCS-` names) and use
them to automatically generate self-descriptions.
Some early-stage work has been done during Gaia-X Hackathon #4 and is available
in the gx-self-description-generator repository.
