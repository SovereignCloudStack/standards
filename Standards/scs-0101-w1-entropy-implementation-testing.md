---
title: "SCS Entropy: Implementation and Testing Notes"
type: Supplement
track: IaaS
status: Draft
supplements:
  - scs-0101-v1-entropy.md
---

## Implementation notes

With reasonably recent hardware—x86 CPU with RDRAND/RDSEED (Intel from 2012,
AMD from 2015) or ARM CPU with FEAT_RNG or FEAT_RNG_TRAP—and recent VM image—Linux
kernel 5.18 or higher—, there is (almost) nothing to be done.

Only the flavor and image attributes required by the standard have to be set:

- flavor extra_spec: `hw_rng:allowed=True` ,
- image property: `hw_rng_model: virtio` .

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
- the number of FIPS 140-2 failures exceeds 5 out of 1000 blocks
  tested, as determined by `cat /dev/random | rngtest -c 1000` .

Note: The latter two items act as surrogates for the following item, which
cannot be detected directly:

- CPU instructions for accessing entropy are not available to the VMs.

### Warnings

The following items MUST be detected and reported as a warning:

- any flavor missing the attribute `hw_rng:allowed=True`,
- any image missing the attribute `hw_rng_model: virtio`,
- the number of FIPS 140-2 failures exceeds 3 out of 1000 blocks
  tested (compare with errors).

Note that the requirement regarding the kernel patch level will not be
checked, because of two reasons: (a) we already check the file `entropy_avail`
(see subsection on Errors), and (b) users can always choose a recent image,
as ensured by the image metadata standard.

### Implementation

We implemented the following testcases that reflect the items in the above section
on automated tests:

- `scs-0101-image-property`,
- `scs-0101-flavor-property`,
- `scs-0101-entropy-avail`,
- `scs-0101-rngd`,
- `scs-0101-fips-test` (covers both the error and warning case).

These testcases can be checked using [`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py).

## Manual tests

None.
