---
title: SCS Flavor Naming Standard
type: Standard
status: Stable
stabilized_at: 2023-06-14
track: IaaS
replaces: scs-0100-v2-flavor-naming.md
description: |
  The SCS Flavor Naming Standard provides a systematic approach for naming instance flavors in OpenStack
  environments, ensuring backward compatibility and clarity on key features like the number of vCPUs, RAM,
  and Root Disk, as well as extra features like GPU support and CPU generation. The standard aims for
  usability and portability across all SCS flavors.
---

## Introduction

This is the standard v3.1 for SCS Release 5.
Note that we intend to only extend it (so it's always backwards compatible),
but try to avoid changing in incompatible ways.
(See at the end for the v1 to v2 transition where we have not met that
goal, but at least managed to have a 1:1 relationship between v1 and v2 names.)

## Motivation

In OpenStack environments there is a need to define different flavors for instances.
The flavors are pre-defined by the operator, the customer can not change these.
OpenStack providers thus typically offer a large selection of flavors.

While flavors can be discovered (`openstack flavor list`), it is helpful for users (DevOps teams),
to have a naming scheme that is used across all SCS flavors, so flavor names have the same meaning everywhere.

While not all details will be encoded in the name, the key features should be obvious:
Number of vCPUs, RAM, Root Disk.
Extra features are important as well: There will be flavors with GPU support, fast disks for databases,
memory-heavy applications, and other useful aspects of an instance.

It may also be important to make the CPU generation clearly recognizable, as this is always a topic in
discussions with customers.

Note that not all relevant properties of flavors can be discovered; creating a specification
to address this is a separate but related effort to the name standardization.
Commonly used infrastructure-as-code tools do not provide a way to use discoverability
features to express something like "I want a flavor with 2 vCPUs, 8GiB of RAM, a local
20GB SSD disk and Infiniband support but I don't care whether it's AMD or intel" in a
reasonable manner. Using flavor names to express this will thus continue to be useful
and we don't expect the need for standardization of flavor names to go away until
the commonly used IaC tools work on a higher abstraction layer than they currently do.

## Design Considerations

### Type of information included

From discussions of our operators with their customers we learned that
the following characteristics are important in a flavor description:

| Type              | Description                                            |
| :---------------- | :----------------------------------------------------- |
| Generation        | CPU Generation                                         |
| Number of CPU     | Number of vCPUs - suffixed by L,V,T,C (see below)      |
| Amount of RAM     | Amount of memory available for the VM                  |
| Performance Class | Ability to label high-performance CPUs, disks, network |
| CPU Type          | X86-intel, X86-amd, ARM, RISC-V, Generic               |
| "bms"             | Bare Metal System (no virtualization/hypervisor)       |

This list is likely not comprehensive and will grow over time.

Rather than using random names `s5a.medium` and assigning a discrete set of properties
to them, we wanted to come up with a scheme that allows to systematically derive
names from properties and vice versa. The scheme allows for short names (by not
encoding all details) as well as very detailed longer names.

## Complete Proposal for systematic flavor naming

| Prefix | CPUs & Suffix     | RAM[GiB]           | optional: Disk[GB]&type       | opt: extensions |
| ------ | ----------------- | ------------------ | ----------------------------- | ----------------|
| `SCS-` | N`L/V/T/C`\[`i`\] | `-`N\[`u`\]\[`o`\] | \[`-`\[M`x`\]N\[`n/h/s/p`\]\] | \[`_`EXT\]      |

Note that N and M are placeholders for numbers here.
The optional fields are denoted in brackets (and have opt: in the header.
See below for extensions.

Note that all letters are case-sensitive.

Typical flavor names look like `SCS-4V-16-50` for a flavor with 4vCPUs (with limited
oversubscription), 16GiB RAM and a 50GB disk (of unspecified type).

## Proposal Details

### [REQUIRED] CPU Suffixes

Next to the number of vCPUs, these vCPUs need to be characterized to describe their nature.

| Suffix | Meaning                       |
| ------ | ----------------------------- |
| C      | dedicated Core                |
| T      | dedicated Thread (SMT)        |
| V      | vCPU (oversubscribed)         |
| L      | vCPU (heavily oversubscribed) |

#### Baseline

Note that vCPU oversubscription for a `V` vCPU should be implemented such, that we
can guarantee _at least 20% of a core in >99% of the time_; this can be achieved by
limiting vCPU oversubscription to 5x per core (or 3x per thread when SMT/HT is enabled)
or by more advanced workload management logic. Otherwise `L` (low performance) instead
of `V` must be used. The >99% is measured over a month (1% is 7.2h/month).

Note that CPUs should use latest microcode to protect against CPU vulnerabilities (Spectre, Meltdown, L1TF, etc.).
In particular,

- microcode must be updated within less than a month of a new release; for CVSS scores above 8,
  providers should do it in less than a week.
- all mitigations that are enabled by default in the Linux kernel and the KVM hypervisor
  should be enabled,
- CPUs that are susceptible to L1TF (intel x86 pre Cascade Lake) should have hyperthreading
  disabled OR (in the future) use core scheduling implementations that are deemed to be secure by the SCS security team.

That is to say, except when the suffix `i` is used, the provider commits itself to implementing the appropriate mitigations
if and when they become available, within the timeframes mentioned above.

If a provider does not want to commit to deploying available microcode fixes and upstream kernel/hypervisor updates within a month or
if the provider wants to enable hyperthreading on compute hosts despite having CPUs susceptible to L1TF there
(and no SCS-accepted core-scheduling mechanism is used for mitigation),
the flavors must be declared insecure with the `i` suffix (see below).

#### Higher oversubscription

Must be indicated with a `L` vCPU type (low performance for > 5x/core or > 3x/thread oversubscription and
the lack of workload management that would prevent worst case performance < 20% in more than 7.2h per month).

#### Insufficient microcode

Not using these mitigations must be indicated by an additional `i` suffix for insecure
(weak protection against CPU vulns through insufficient microcode, lack of disabled hyperthreading
on L1TF susceptible CPUs w/o effective core scheduling or disabled protections on the host/hypervisor).

#### Examples

- SCS-**2C**-4-10n
- SCS-**2T**-4-10n
- SCS-**2V**-4-10n
- SCS-**2L**-4-10n
- SCS-**2Li**-4-10n
- ~~SCS-**2**-\*\*4-10n~~ - CPU suffix missing
- ~~SCS-**2iT**-4-10n~~ - This order is forbidden

### [REQUIRED] Memory

#### Baseline

Cloud providers should use ECC memory.
Memory oversubscription should not be used.
It is allowed to specify half GiBs (e.g. 3.5), though this is should not be done for larger memory sizes (>= 10GiB).

#### No ECC

If no ECC is used, the `u` suffix must indicate this.

#### Enabled Oversubscription

If memory is oversubscribed, you must expose this with the `o` suffix.

#### Examples

- SCS-2C-**4**-10n
- SCS-2C-**3.5**-10n
- SCS-2C-**4u**-10n
- SCS-2C-**4o**-10n
- SCS-2C-**4uo**-10n
- ~~SCS-2C-**4ou**-10n~~ - This order is forbidden

### [OPTIONAL] Disk sizes and types

Disk sizes (in GB) should use sizes 5, 10, 20, 50, 100, 200, 500, 1000.

| Disk type | Meaning                              |
| --------- | ------------------------------------ |
| n         | Network shared storage (ceph/cinder) |
| h         | Local disk (HDD: SATA/SAS class)     |
| s         | Local SSD disk                       |
| p         | Local high-perf NVMe                 |

#### Baseline

Note that disk type might be omitted — the user then can not take any assumptions
on what storage is provided for the root disk (that the image gets provisioned to).

It does make sense for `n` to be requested explicitly to allow for smooth live migration.
`h` typically provides latency advantages vs `n` (but not necessarily bandwidth and
also is more likely to fail), `s` and `p` are for applications that need low
latency (high IOPS) and bandwidth disk I/O. `n` storage is expected to survive
single-disk and single-node failure.

For specific requirements on the SSD and NVMe disks regarding IOPS and
power-loss protection, refer to Decision Record [scs-0110-ssd-flavors](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0110-v1-ssd-flavors.md).

If the disk size is left out, the cloud is expected to allocate a disk (network or local)
that is large enough to fit the root file system (`min_disk` in image). This automatic
allocation is indicated with `-` without a disk size.
If the `-` is left out completely, the user must create a boot volume manually and
tell the instance to boot from it or use the
[`block_device_mapping_v2`](https://docs.openstack.org/api-ref/compute/?expanded=create-server-detail#create-server)
mechanism explicitly to create the boot volume from an image.

#### Multi-provisioned Disk

The disk size can be prefixed with `Mx prefix`, where M is an integer specifying that the disk
is provisioned M times. Multiple disks provided this way should be independent storage media,
so users can expect some level of parallelism and independence.

#### Examples

- SCS-2C-4-**10n**
- SCS-2C-4-**10s**
- SCS-2C-4-**10s**\_bms\_z3
- SCS-2C-4-**3x10s** - Cloud creates three 10GB SSDs
- SCS-2C-4-**3x10s**\_bms\_z3
- SCS-2C-4-**10** - Cloud decides disk type
- SCS-2C-4-**10**\_bms\_z3
- SCS-2C-4-**n** - Cloud decides disk size (min\_disk from image or larger)
- SCS-2C-4-**n**\_bms\_3
- SCS-2C-4- - Cloud decides disk type and size
- SCS-2C-4-\_bms\_z3
- SCS-2C-4-\_bms\_z3h\_GNa-64\_ib
- SCS-2C-4-\_ib
- SCS-2C-4 - You need to specify a boot volume yourself (boot from volume, or use `block_device_mapping_v2`)
- SCS-2C-4\_bms\_z3
- SCS-2C-4-3x10 - Cloud decides type and creates three 10GB volumes
- ~~SCS-2C-4-**1.5n**~~ - You must not specify disk sizes which are not in full GiBs

## Naming policy compliance

Every flavor you offer MUST satisfy the following assertion:

- If its name starts with `SCS-`, the name has to conform to the syntax outlined above, and
  the flavor must _at least_ provide the capabilities indicated by the name.

That is to say:

- You may offer flavors not following the above scheme, as long as the name does not
  start with `SCS-`.

- You are allowed to understate your performance; for instance, a flavor that satisfies
  `SCS-1C-1.5-8s` (1 dedicated core, 1.5 GiB RAM, 8 GiB SSD) may also be named
  `SCS-1T-1-5n` (1 dedicated hyperthread, 1 GiB RAM, 5 GiB network volume) or even
  `SCS-1V-1-5`. Similarly, you may offer the (v3 mandatory) `SCS-2V-4-20s` with a `SCS-2V-4-20p`
  implementation (using a local NVMe instead of an SSD).

You must be very careful to expose low vCPU guarantees (`L` instead of `V`), insecure
hyperthreading/microcode `i`, non-ECC-RAM `u`, memory oversubscription `o`. Note that omitting these qualifiers
is _overstating_ your security, reliability or performance properties and may be reason for
clients to feel betrayed or claim damages. This would prevent SCS compliance and certification;
in extreme cases, the SCS project might be forced to work with public statements.

We expect all cloud providers to offer the short, less specific flavor names (such as `SCS-8V-32-100`).
Larger providers that offer more details (using the extension below) are expected to still also
offer the short variants for usability and easier portability, even beyond the mandated flavors.

You must not extend the SCS naming scheme with your own extensions; you are encouraged however
to suggest extensions that we can discuss and add to the official scheme.

## Extensions

Extensions provide a possibility for providers that offer a very differentiated set
of flavors to indicate hypervisors, support for hardware/nested virtualization,
CPU types and generations, high-frequency models, GPU support and GPU types as
well as Infiniband support. (More extensions may be appended in the future.)

Using the systematic naming approach ensures that two providers that offer flavors
with the same specific features will use the same name for them, thus simplifying
life for their customers when consuming these flavors.

Note that there is no need to indicate all details and extra features this way.
Flavors may always perform better or have more features than indicated in a name.
Underperformance (CPU suffixes `L` or `i` or memory suffixes `o` and `u`) on the other
hand MUST be indicated in the name; this happens rarely in practice.

For smaller providers, the ability to e.g. differentiate between an AMD Milan and an intel
IceLake and exposed the slightly different feature set to customers and have slightly
different price points is often not worth the extra effort. This is because having
this extra differentiation causes fragmentation of the machines (host aggregates)
that can offer these flavors, thus resulting in a lower utilization (as the capacity
management will need to have a certain amount of headroom per machine pool to avoid
running out of capacity).

Note that it is possible for providers to register both the generic short names and the
longer, more detailed names and allow them to use the same set of machines (host aggregates).
Note that machines (hypervisors) can be part of more than one host aggregate.

The extensions have the format:

\[`_`hyp\]\[`_hwv`\]\[`_`arch\[N\]\[`h`\]\]\[`_`\[`G/g`\]X\[N\]\[`-`M\]\[`h`\]\]\[`_ib`\]

Extensions are individually optional, but the ones that are used must appear in the order
given in the above line.

Remember that letters are case-sensitive.
In case you wonder: Feature indicators are capitalized, modifiers are lower case.
(An exception is the uppercase `_G` for a pass-through GPU vs. lowercase `_g` for vGPU.)

### [OPTIONAL] Hypervisor

Format: `_`hyp

The _default Hypervisor_ is assumed to be `KVM`. Clouds that offer different hypervisors
or Bare Metal Systems should indicate the Hypervisor according to the following table:

| hyp | Meaning           |
| --- | ----------------- |
| kvm | KVM               |
| xen | Xen               |
| vmw | VMware            |
| hyv | Hyper-V           |
| bms | Bare Metal System |

#### Examples

- SCS-2C-4-10n
- SCS-2C-4-10n\_**bms**
- SCS-2C-4-10n\_**bms**\_z3h

### [OPTIONAL] Hardware virtualization / Nested virtualization

Format: `_hwv`

If the instances that are created with this flavor support hardware-accelerated
virtualization, this can be reflected with the `_hwv` flag (after the optional
Hypervisor flag). On x86, this means that in the instance, the CPU flag vmx (intel)
or svm (AMD) is available. This will be the case on Bare Metal flavors on almost
all non-ancient x86 CPUs or if your virtualization hypervisor is configured to
support nested virtualization.
Flavors without the `_hwv` flag may or may not support hardware virtualization (as we
recommend enabling nesting, but don't require flavor names to reflect all
capabilities. Flavors may over-deliver ...)

#### Examples

- SCS-2C-4-10 - may or may not support HW virtualization in VMs
- SCS-2C-4-10_kvm_**hwv** - kvm with enabled nested virtualization
- SCS-2C-4-10\_**hwv** - not recommended, but allowed
- SCS-2C-4-10\_bms\_**hwv** - better: bare metal with HW virt support (VMX on intel, SVM on AMD, ...)
- ~~SCS-2C-4-10\_**hwv**\_xen~~ - illegal, wrong ordering

### [OPTIONAL] CPU Architecture Details

Format: `_`arch\[N\]\[`h`\]

This extension provides more details on the specific CPU:

- vendor/architecture (arch)
- generation (N)
- frequency (h)

#### Generation and Vendor

The options for arch are as follows:

| Letter  | vendor/architecture  | Corresponding image architecture  |
| ------- | -------------------- | --------------------------------- |
| (none)  | Generic x86-64       | `x86_64`                          |
| `i`     | Intel x86-64         | `x86_64`                          |
| `z`     | AMD (Zen) x86-64     | `x86_64`                          |
| `a`     | ARM v8+              | `aarch64`                         |
| `r`     | RISC-V               | (not yet listed in Glance)        |

The generation is vendor specific and can be left out, but it can only be specified in
conjunction with a vendor. At present, these values are possible:

| Generation | i (Intel x86-64) | z (AMD x86-64) |  a (AArch64)       | r (RISC-V) |
| ---------- | ---------------- | -------------- | ------------------ | ---------- |
| 0          | pre Skylake      | pre Zen        | pre Cortex A76     | TBD        |
| 1          | Skylake          | Zen-1 (Naples) | A76/NeoN1 class    | TBD        |
| 2          | Cascade Lake     | Zen-2 (Rome)   | A78/x1/NeoV1 class | TBD        |
| 3          | Ice Lake         | Zen-3 (Milan)  | A71x/NeoN2 (ARMv9) | TBD        |
| 4          | Sapphire Rapids  | Zen-4 (Genoa)  |                    | TBD        |

It is recommended to leave out the `0` when specifying the old generation; this will
help the parser tool, which assumes 0 for an unspecified value and does leave it
out when generating the name for comparison. In other words: 0 has a meaning of
"rather old or unspecified".

:::note

We don't differentiate between Zen-4 (Genoa) and Zen-4c (Bergamo); L3 cache per
Siena core is smaller on Bergamo and the frequency lower but the cores are otherwise
identical. As we already have a qualifier `h` that allows to specify higher frequencies
(which Genoa thus may use more and Bergamo less or not), we have enough distinction
capabilities.

:::

#### Frequency Suffixes

| Suffix | Meaning           |
| ------ | ----------------- |
| h      | >2.75GHz all-core |
| hh     | >3.25GHz all-core |
| hhh    | >3.75GHz all-core |

#### Examples

- SCS-2C-4-10n
- SCS-2C-4-10n\_**z**
- SCS-2C-4-10n\_**z3**
- SCS-2C-4-10n\_**z3h**
- SCS-2C-4-10n\_**z3hh**
- SCS-2C-4-10n\_bms\_**z**
- SCS-2C-4-10n\_bms\_**z3**
- SCS-2C-4-10n\_bms\_**z3**
- SCS-2C-4-10n\_bms\_**z3h**
- SCS-2C-4-10n\_bms\_**z3hh** - Bare Metal, AMD Milan with > 3.25GHz all core freq

### [OPTIONAL] GPU support

Format: `_`\[`G/g`\]X\[N\]\[`-`M\]\[`h`\]

This extension provides more details on the specific GPU:

- pass-through (`G`) vs. virtual GPU (`g`)
- vendor (X)
- generation (N)
- number (M) of processing units that are exposed (for pass-through) or assigned; see table below for vendor-specific terminology
- high-performance indicator (`h`)

Note that the vendor letter X is mandatory, generation and processing units are optional.

| letter X | vendor | processing units                |
| -------- | ------ | ------------------------------- |
| `N`      | nVidia | streaming multiprocessors (SMs) |
| `A`      | AMD    | compute units (CUs)             |
| `I`      | Intel  | execution units (EUs)           |

For nVidia, the generation N can be f=Fermi, k=Kepler, m=Maxwell, p=Pascal, v=Volta, t=turing, a=Ampere, l=Ada Lovelace, ...,
for AMD GCN-x=0.x, RDNA1=1, RDNA2=2, RDNA3=3,
for Intel Gen9=0.9, Xe(12.1)=1, ...
(Note: This may need further work to properly reflect what's out there.)

The optional `h` suffix to the compute unit count indicates high-performance (e.g. high freq or special
high bandwidth gfx memory such as HBM);
`h` can be duplicated for even higher performance.

Example: `SCS-16V-64-500s_GNa-14h`
This flavor has a pass-through GPU nVidia Ampere with 14 SMs and either high-bandwidth memory or specially high frequencies.
Looking through GPU specs you could guess it's 1/4 of an A30.

### [OPTIONAL] Infiniband

Format: `_ib`

This extension indicates Infiniband networking.

More extensions may be forthcoming and appended in a later revision of this spec.

Extensions need to be specified in the above-mentioned order.

### Naming options advice

Note that we expect most clouds to prefer short flavor names,
not indicating CPU details or hypervisor types. See above list
of standard flavors to get a feeling.

However, more successful providers will often need to differentiate their
offerings in response to customer demand and allow customers to request
flavors with specific detailed properties. The goal of this proposal is to avoid
providers to invent their own names and then refer customers to (currently
incompletely standardized) `extra_specs`
or worse a non-machine-readable service descriptions to find out the details.

So a cloud provider might well evolve from offering `SCS-8T-16-50` to offering
`SCS-8T-16-50n`, `SCS-8T-16-50n_i2` and `SCS-8T-16-50n_z2` to specify that he
is using network disks and offer a choice b/w intel Cascade-Lake and AMD Rome.
We would expect the cloud provider to still offer the generic flavor
`SCS-8T-16-50` and allow the scheduler (placement service) to pick both more
specific types (or just one if e.g. capacity management considerations suggest
so). Providers in such cases should ensure that the price of a requested
flavor does not depend on the scheduler decisions.

We are looking into the [metadefs](https://docs.openstack.org/image-guide/introduction.html#metadata-definition-metadefs-service)
mechanism and [extra_specs](https://docs.openstack.org/api-guide/compute/extra_specs_and_properties.html)
to allow customers to ask for specific flavor properties without the need to
encode all these flavor details into the flavor name, so the optional pieces
may not be needed much. However, there must be a way to request flavor
properties without encoding the need into an image — the indirection via
an image is considered broken by the SCS team.

## Proposal Examples

| Example                   | Decoding                                                                                       |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| SCS-2C-4-10n              | 2 dedicated cores (x86-64), 4GiB RAM, 10GB network disk                                        |
| SCS-8Ti-32-50p_i1         | 8 dedicated hyperthreads (insecure), Skylake, 32GiB RAM, 50GB local NVMe                       |
| SCS-1L-1u-5               | 1 vCPU (heavily oversubscribed), 1GiB Ram (no ECC), 5GB disk (unspecific)                      |
| SCS-16T-64-200s_GNa-64_ib | 16 dedicated threads, 64GiB RAM, 200GB local SSD, Infiniband, 64 Passthrough nVidia Ampere SMs |
| SCS-4C-16-2x200p_a1       | 4 dedicated Arm64 cores (A76 class), 16GiB RAM, 2x200GB local NVMe drives                      |
| SCS-1V-0.5                | 1 vCPU, 0.5GiB RAM, no disk (boot from cinder volume)                                          |

## Previous standard versions

Previous versions up to version 3.0 contained the list of
mandatory/recommended flavors, which has been moved to
[a standard of its own](scs-0103-v1-standard-flavors.md).

[Version 1 of the standard](scs-0100-v1-flavor-naming.md)
used a slightly different naming syntax while the logic was exactly the same.
What is a `-` in v2 used to be a `:`; `_` used to be `-`. The reason for
the change was certain Kubernetes tools using the flavor names as labels.
Labels however are subject to stricter naming rules and in particular don't
allow for a `:`. See [PR #190](https://github.com/SovereignCloudStack/standards/issues/190)
for a discussion.

Version 1 flavor names can be translated to v2 using the following transformation:

```shell
NAMEV2=$(echo "$NAMEV1" | sed -e 's/\-/_/g' -e 's/:/-/g' -e 's/^SCS_/SCS-/')
```

and the way back can be done with

```shell
NAMEV1=$(echo "$NAMEV2" | sed -e 's/\-/:/g' -e 's/_/-/g' -e 's/^SCS:/SCS-/')
```

For the time being, the validation tools still accept the old names with a warning
(despite the unchanged `SCS-` prefix) unless you pass option `-2` to them. They will
however not count v1 flavors towards fulfilling the needs against the corresponding
v2 mandatory flavor list unless you pass the option `-1`.
In other words: An IaaS infrastructure with the 26
v1 mandatory flavors will produce 26 warnings (for using old flavors) and 26
errors (for missing the 26 mandatory v2 flavors) unless you pass `-1` in which
case no errors and no warnings will be produced. Registering the 26 mandatory
v2 flavor names in addition will result in passing the test with only 26
warnings — unless you specify `-2`. If you do and want to pass you'll need
to remove the old v1 names or rename them to no longer start with `SCS-`.

## Beyond SCS

The Gaia-X provider working group which could have created a superseding standard
does no longer exist.

However, we have been reaching out to the OpenStack Public Cloud SIG and the ALASCA
members to seek further alignment.

Getting upstream OpenStack support for flavor aliases would provide more flexibility
and ease migrations between providers, also providers that don't offer the SCS-
flavors.

We also would like to see upstream `extra_specs` standardizing the discoverability of some
properties exposed via the SCS names and work on IaC tooling (terraform ...)
to make use of these when selecting a flavor.
