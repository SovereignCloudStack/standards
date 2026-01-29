---
title: "SCS Entropy: Implementation and Testing Notes"
type: Supplement
track: IaaS
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

The following testcases [are implemented](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py):

- `scs-0101-image-property` ensures that each flavor has the extra spec `hw_rng:allowed=True`,
- `scs-0101-flavor-property` ensures that each public image has the property `hw_rng_model: virtio`,
- `scs-0101-rngd` ensures that the service `rngd` is present on a sample VM,
- `scs-0101-entropy-avail` ensures that the special file `/proc/sys/kernel/random/entropy_avail` contains
  the value 256 (pinned since kernel 5.18) on a sample VM,
- `scs-0101-fips-test` ensures that the number of FIPS 140-2 failures is below 5 out of 1000 blocks
  tested, as determined by `cat /dev/random | rngtest -c 1000` on a sample VM.

Note: The latter two items act as surrogates for the following item, which
cannot be detected directly:

- CPU instructions for accessing entropy are available to the VMs.

Note that the requirement regarding the kernel patch level will not be
checked, because of two reasons: (a) we already check the file `entropy_avail`
(see subsection on Errors), and (b) users can always choose a recent image,
as ensured by the image metadata standard.

## Manual tests

None.
