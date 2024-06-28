---
title: "SCS Entropy: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0101-v1-entropy.md
---

## Implementation notes

We presume that almost nothing has to be done (or indeed can be done), as
long as the CPUs and VM images are reasonably recent.
The already mentioned failure testing and entropy count is available
on modern linux kernels (especially on 5.18 or higher),
but if older kernels are made available, the CSP needs to provide entropy
by offering CPU instructions that provide entropy without being filtered by the hypervisor.
All newer CPUs offer instructions for this kind of use-case (e.g. Intel introduced RDRAND
in 2014 in their Broadwell architecture) and the expectation is,
that most CSPs don't use older processors.

Most times, only the flavor and image attributes required by the standard have to be set:

- flavor: `hw_rng:allowed=True` ,
- image: `hw_rng_model: virtio` .

## Automated tests

### Images sample

Some checks need to be performed on a live instance. For these checks, it is
necessary to choose a sample of VM images to test on.

For the time being, the sample MUST contain at least one public image reported
by OpenStack. This may be extended in the future.

### Errors

For every image in the chosen sample, the following items MUST be detected and
reported as an error:

- the service `rngd` is not running,
- the special file `/proc/sys/kernel/random/entropy_avail` does not contain
  the value 256 (pinned since kernel 5.18),
- the number of FIPS 140-2 failures exceeds 3 out of 1000 blocks
  tested, as determined by `cat /dev/random | rngtest -c 1000` .

Note: The latter two items act as surrogates for the following item, which
cannot be detected directly:

- CPU instructions for accessing entropy are not available to the VMs.

### Warnings

The following items MUST be detected and reported as a warning:

- any flavor missing the attribute `hw_rng:allowed=True`,
- any image missing the attribute `hw_rng_model: virtio`,

Note that the requirement regarding the kernel patch level will not be
checked, because of two reasons: (a) we already check the file `entropy_avail`
(see subsection on Errors), and (b) users can always choose a recent image,
as ensured by the image metadata standard.

### Implementation

The script [`entropy-check.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/entropy/entropy-check.py)
connects to OpenStack and performs the checks described in this section.

## Manual tests

None.
