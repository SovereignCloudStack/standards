---
title: SCS Entropy
type: Standard
status: Draft
track: IaaS
---

## Introduction

### Entropy in information technology

Entropy is a concept that is widely used in the scope of information
technology. It is a measurement of the amount of disorder or randomness in
a system. Entropy is used to measure the amount of information in a
self-contained system, as well as the amount of incertitude that exists in this
system.

### Real-world uses of entropy

Cryptography is a very prominent, albeit not the only application that
heavily relies on entropy for operations such as creating secure keys.
These operations can stall and take an abnormally long amount of time
when the available _entropy runs out_, leading to malfunctioning OpenSSL
operations and applications such as load balancers.

### Sources of entropy

In _traditional baremetal systems_ the amount of incertitude is sourced
from the randomness of read/write cycle of the disk heads of a disk drive,
bus timings as well as items such as keyboard timings.

_More recent methods_ of generating entropy include measuring IRQ jitter
(available in Linux since kernel 5.4 or, before that, via a daemon such as
[HavegeD](http://www.issihosts.com/haveged/)) as well as a special CPU
instruction set (RDRAND/RDSEED), which is present in all modern CPUs from
ARM, AMD, and Intel, and even in the consumer-grade Raspberry Pi
(1b onwards).

Finally, a dedicated device can be utilized -- if present -- that is
called _hardware random number generator_ or HW RNG for short. For instance,
the [trusted platform module](https://en.wikipedia.org/wiki/Trusted_Platform_Module)
includes a HW RNG. On Linux systems, the HW RNG appears as `/dev/hwrng`.
Note that, while the RDRAND/RDSEED instruction set can be construed as
a HW RNG, it is not treated as such by the kernel, i.e., it _does not_
appear as `/dev/hwrng`!

The Linux kernel combines multiple sources of entropy into a pool. To this
end, it will use all of the sources discussed so far with one exception:
the HW RNG must be fed into the pool (if so desired) via the daemon `rngd`.
The kernel converts the entropy from the pool into cryptographically
secure random numbers that appear under `/dev/random`.

With kernel 5.18, the algorithm that accomplishes
said conversion has been drastically improved (see 
[linux-rng-5.17-18](https://web.archive.org/web/20230321040526/https://www.zx2c4.com/projects/linux-rng-5.17-5.18/)),
so much so that running out of entropy is virtually ruled out.
These patches have now also arrived in the upstream LTS images.

### Entropy in virtual instances

Virtual instances or virtual machines do not have the traditional sources
of entropy mentioned above. However, the more recent methods mentioned
above do work just fine (the RDRAND instruction set is not privileged).

Alternatively, a virtualized HW RNG called `virtio-rng` can be established
that injects entropy from the host into the instance, where this
entropy can be sourced optionally from either the host's `/dev/random` or
some HW RNG in the host. This virtualized HW RNG behaves just like real
one, that is, it appears as `/dev/hwrng`, and the daemon `rngd` must
be used to feed it into the kernel's entropy pool.

In summary, with current kernels and CPUs entropy in virtual instances
is readily available to a sufficient degree. In addition, the host's
entropy sources can be injected using `virtio-rng` if so desired, e.g.,
to enable access to a HW RNG.

## Motivation

As stated above, good sources of entropy are paramount for many
important applications. Moreover, current technology makes it easy
to provide these sources to virtual instances. Therefore, this standard
mandates that these sources be made available on all conformant clouds.

## Entropy in SCS clouds

This standard does not intend to make any guarantees for linux images
that are not themselves included in the
[SCS standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0102-v1-image-metadata.md), in particular
images having a kernel below version 5.18.

### Flavors

All flavors must have the following attribute activated:

```console
hw_rng:allowed=True
```

The following attributes are optional:

```console
hw_rng:rate_bytes - The allowed amount of bytes for the the guest
    to read from the host's entropy per period.
hw_rng:rate_period - Sets the duration of a read period in seconds.
```

### Images

Images must activate the attribute `hw_rng_model: virtio`.

The daemon `rngd` must be installed (usually from `rng-tools`
or `rng-utils`).

The user may choose to use the `virtio-rng` device via `rngd`.

### Compute nodes

Compute nodes must use CPUs that offer RDRAND/RDSEED. This requirement
is both very hard to verify and almost impossible to violate, so it will
not be tested for.

Compute nodes may provide a true HW RNG via `rngd`.
