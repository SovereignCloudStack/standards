---
title: SCS Entropy
type: Standard
status: Draft
track: IaaS
---

## 1. Terminology of Entropy

### 1.1. Entropy in information Technology

Entropy is a concept that is widely used in the scope of information
technology. It is a measurement of the amount of disorder or randomness in
a system. Entropy is used to measure the amount of information in a
self contained systems, as well as the amount of incertitude that exists
in this system. For cryptographic procedures and operations good entropy
is a must have!

In traditional baremetal systems the amount of incertitude is generated
by the randomness of read/write cycle of the disk heads of a disk-drive,
bus timings as well as items such as keyboard timings.

### 1.2 Entropy in Virtual Instances

Virtual instances or virtual machines do not have these sources
for random numbers. An instance will operate normally, but as
cryptographic operations happen, procedures will take an abnormal long time,
because with a small entropy count cryptographic operation can not operate
in realtime. Examples are malfunctioning applications and OpenSSL
operations that will not work.

```console
  $cat /proc/sys/kernel/random/entropy_avail
  128
```

#### 1.2.1 How to generate entropy "Out-Of-Nothing" ?

One procedure that was used in the past in virtual machines or virtual appliances
was the use of an entropy daemon to ensure that here is a sufficient
amount of entropy. Today this is a common operation although for embedded devices.
[HavegeD](http://www.issihosts.com/haveged/) is one of those daemons.

```console
   $cat /proc/sys/kernel/random/entropy_avail
   1956
```

#### 1.2.2 CPU Hardware random number generator

Modern server CPUs of ARM, AMD and Intel ship Hardware random
number generator. This feature will be passed through to the virtualization
layer. This will be addressed by virtio-rng.

Baremetal systems and virtual instances will need the rng-tools or
rng-utils.

```console
     #cat /proc/sys/kernel/random/entropy_avail
     3843
```

##### 1.2.3 Changes since Linux 5.17, 5.18

Jason A. Donenfeld has rewritten the RNG Number generator for Linux, which is replacing the very old sha-1 with blake2 algorithm, "random use computational hash for entropy extraction"
the full explanation will found here: [linux-rng-5.17-18](https://www.zx2c4.com/projects/linux-rng-5.17-5.18/).
This RNG improvements make some workarounds obsolete. For an example haveged should not use
anymore. Rng-tools can continue to be used. Rng-tools bridge the hardware number generators that support RDRAND and RDSEED as they support HWRNG in modern Intel and AMD processors. 

These patches are now also arrived the upstream LTS Kernels.

This behavior will look as follows:

```console
 $cat /proc/sys/kernel/random/entropy_avail
  256
```

because here is now working the blake2 algorithm the entropy count is sufficient.

### 1.3 Entropy in SCS Clouds

#### 1.3.1 Flavors

All flavors need to have the relevant attributes activated:

```console
hw_rng:allowed=True
```

optional:

```console
hw_rng:rate_bytes - The allowed amount of bytes for the the guest
to read from the host’s entropy per period.

hw_rng:rate_period
```

#### 1.3.2 Images

Images must activate the attribute `hw_rng_model: virtio`.

#### 1.3.3 Compute Nodes

On compute nodes the rng-utils must be present and activate.
This is a requirement to guarantee working confident cryptography
in SCS Cloud Infrastructures.
