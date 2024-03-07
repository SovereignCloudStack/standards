# SCS compliance

In order to be SCS-compliant, the standards defined by the [SCS project](https://github.com/SovereignCloudStack/) need
to be adapted and complied to. For this reason, SCS provides standard documents and tests in its
[Standards repository](https://github.com/SovereignCloudStack/standards).
If a provider can run the tests supplied in that repository against his infrastructure without a test failure, that
part of his infrastructure can be considered SCS-compliant. It is important to note, that only tests of "stabilized"
standards need to passed, so some standards and also their tests might either be deprecated or still in a draft phase.

Standards and their tests are separated into a few general categories:

## IaaS

Standards for IaaS can be found under the handle scs-01XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for IaaS can be found in the `Tests/iaas` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.

## KaaS

Standards for KaaS can be found under the handle scs-02XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for KaaS can be found in the `Tests/kaas` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.

## IAM

Standards for IAM can be found under the handle scs-03XX-vY-NAME with XX specifying their standard number and Y specifying their version.
Tests for IAM can be found in the `Tests/iam` directory and don't comply with the schema used by the standards.
Instead, they (mostly) borrow the NAME of the standard document to show their link with a specific standard. More specific
information can most of the time be found in a section of the standard, which specifies the test used to check if their requirements are fulfilled.

# Making Yaook/OpenStack SCS-compliant

In order to make Yaook (OpenStack) SCS-compliant, the main question is how to make OpenStack SCS-compliant.

This requires the OpenStack cluster in question to be compliant with the standards currently stabilized and therefore passing
the provided tests. But it also requires forward planning to be compliant with future standards that are currently in the
draft phase. Since tests are often not available for these drafts and only are created in a later phase, some reading and
understanding of these standards needs to be done to future-proof an OpenStack instance.

## Stable standards and their tests

This section attempts to list all stabilized standards and their tests relevant for OpenStack, and therefore for Yaook,
in order to provide the requirements that need to be fulfilled for a currently SCS-compliant cluster.

### SCS Flavor Naming Standard (scs-v100-v3-flavor-naming)

	The SCS Flavor Naming Standard provides a systematic approach for naming instance flavors in OpenStack
	environments, ensuring backward compatibility and clarity on key features like the number of vCPUs, RAM,
	and Root Disk, as well as extra features like GPU support and CPU generation. The standard aims for
	usability and portability across all SCS flavors.

This standard is already in its 3rd iteration and requires a specific naming schema to be used for OpenStack flavors.
The general naming schema can be seen in the [following table](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0100-v3-flavor-naming.md)

| Prefix | CPUs & Suffix     | RAM[GiB]           | optional: Disk[GB]&type       | opt: extensions |
|--------|-------------------|--------------------|-------------------------------|-----------------|
| `SCS-` | N`L/V/T/C`\[`i`\] | `-`N\[`u`\]\[`o`\] | \[`-`\[M`x`\]N\[`n/h/s/p`\]\] | \[`_`EXT\]      |

The naming schema consists of multiple parts describing CPU, RAM and optionally disk and extensions used for a
flavor. `N` and `M` are non-linked numbers that provide the quantity of the parts they're describing.
Letters in the schema are case-sensitive.

Each part of the schema also has specific suffixes that describe different properties. The tables
describing these can be found below or in the [standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0100-v3-flavor-naming.md).
It is also important to note, that the order of these suffixes matters; in general the ordering found
in the schema above should be kept (if suffixes are used).

To comply with this standard, SCS expects an OpenStack instance to provide all flavors with its described
naming schema. It is also expected, that the flavor description isn't overstating security, performance or
capabilities. All of these features can be deduced from the schema and an overstatement would mean a falsification
of the presented data, which could lead to problems for the customer.
Understating on the other hand is allowed, but not encouraged.

The standard can be tested with the `Tests/iaas/flavor-naming` test and should output no errors, if compliance
is to be achieved.

#### CPU suffixes

| Suffix | Meaning                       |
|--------|-------------------------------|
| C      | dedicated Core                |
| T      | dedicated Thread (SMT)        |
| V      | vCPU (oversubscribed)         |
| L      | vCPU (heavily oversubscribed) |
| i      | Insufficient (old) micro code |

#### RAM suffixes

| Suffix | Meaning                  |
|--------|--------------------------|
| u      | No ECC memory is used    |
| o      | Memory is oversubscribed |

#### Disk suffixes

| Suffix | Meaning                                     |
|--------|---------------------------------------------|
| n      | Network shared storage (ceph/cinder)        |
| h      | Local disk (HDD: SATA/SAS class)            |
| s      | Local SSD disk                              |
| p      | Local high-perf NVMe                        |
| Mx     | States that the disk is provisioned M times | 

#### Extension schema

The extension schema can contain the following parts
\[`_`hyp\]\[`_hwv`\]\[`_`arch\[N\]\[`h`\]\]\[`_`\[`G/g`\]X\[N\]\[`-`M\]\[`h`\]\]\[`_ib`\]

The parts of this sub-schema can be seen below. Like in the main schema, the ordering should be
kept like its seen, if multiple parts are used.

##### Hypervisor schema

| Abbreviation | Meaning           |
|--------------|-------------------|
| kvm          | KVM               |
| xen          | Xen               |
| vmw          | VMware            |
| hyv          | Hyper-V           |
| bms          | Bare Metal System |

##### Virtualization schema

hwv - supports hardware-accelerated virtualization

##### Architecture schema
The architecture schema consists of multiple parts, describing the architecture and vendor of a CPU as well as its
generation and base frequency over all cores.
Parts of this schema are described below and further described in the provided tables.

arch - vendor/architecture (arch)
	 - generation (N)
	 - frequency (h)

| Letter | vendor/architecture | Corresponding image architecture |
|--------|---------------------|----------------------------------|
| (none) | Generic x86-64      | `x86_64`                         |
| `i`    | Intel x86-64        | `x86_64`                         |
| `z`    | AMD (Zen) x86-64    | `x86_64`                         |
| `a`    | ARM v8+             | `aarch64`                        |
| `r`    | RISC-V              | (not yet listed in Glance)       |

| Generation | i (Intel x86-64) | z (AMD x86-64) | a (AArch64)        | r (RISC-V) |
|------------|------------------|----------------|--------------------|------------|
| 0          | pre Skylake      | pre Zen        | pre Cortex A76     | TBD        |
| 1          | Skylake          | Zen-1 (Naples) | A76/NeoN1 class    | TBD        |
| 2          | Cascade Lake     | Zen-2 (Rome)   | A78/x1/NeoV1 class | TBD        |
| 3          | Ice Lake         | Zen-3 (Milan)  | A71x/NeoN2 (ARMv9) | TBD        |
| 4          | Sapphire Rapids  | Zen-4 (Genoa)  |                    | TBD        |

| Suffix | Meaning           |
|--------|-------------------|
| h      | >2.75GHz all-core |
| hh     | >3.25GHz all-core |
| hhh    | >3.75GHz all-core |

##### GPU support schema

GPU support is described with `_`\[`G/g`\]X\[N\]\[`-`M\]\[`h`\], which provides the following parts:

| Abbreviation | Meaning                                                     |
|--------------|-------------------------------------------------------------|
| G            | pass-through                                                |
| g            | virtual GPU                                                 |
| X            | vendor, described in separate table                         |
| N            | generation, described in separate table                     |
| M            | number of processing units, described in table about vendor |
| h            | high performance indicator, can be duplicated               |

| letter X | vendor | processing units                |
|----------|--------|---------------------------------|
| `N`      | nVidia | streaming multiprocessors (SMs) |
| `A`      | AMD    | compute units (CUs)             |
| `I`      | Intel  | execution units (EUs)           |

| letter N | vendor | possible generations                                                                     |
|----------|--------|------------------------------------------------------------------------------------------|
| -        | nVidia | f=Fermi, k=Kepler, m=Maxwell, p=Pascal, v=Volta, t=turing, a=Ampere, l=Ada Lovelace, ... |
| -        | AMD    | GCN-x=0.x, RDNA1=1, RDNA2=2, RDNA3=3, ....                                               |
| -        | Intel  | Gen9=0.9, Xe(12.1)=1, ....                                                               |

Note: This table isn't in a final form, as noted by standard, and probably needs to be adapted again alter on.

##### Networking schema

This extension only indicates infiniband networking at the moment.

| Suffix | Meaning               |
|--------|-----------------------|
| ib     | Infiniband networking |

### SCS Entropy Standard (scs-0101-v1-entropy)


### SCS Image Metadata Standard (scs-0102-v1-image-metadata)

	The SCS-0102 Image Metadata Standard outlines how to categorize and manage metadata for cloud-based operating
	system images to ensure usability and clarity. The standard encompasses naming conventions, technical requirements,
	image handling protocols including updating and origin, and licensing/support details. These guidelines ensure
	that users can understand, access, and utilize OS images effectively, with clear information on features, updates,
	and licensing provided through well-defined metadata properties.



### SCS Standard Flavors and Properties (scs-0103-v1-standard-flavors)

	The SCS-0103 standard outlines mandatory and recommended specifications for flavors and properties in OpenStack
	environments to ensure uniformity across SCS clouds. Mandatory and recommended flavors are defined with specific
	configurations of vCPUs, vCPU types, RAM, and root disk sizes, alongside extra specs like scs:name-vN, scs:cpu-type,
	and scs:diskN-type to detail the flavor's specifications. This standard facilitates guaranteed availability and
	consistency of flavors, simplifying the deployment process for DevOps teams.



#### Mandatory

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type         |
|------------------|-------|--------------|-----------|----------------|-------------------|
| SCS-1V-4         | 1     | shared-core  | 4         |                |                   |
| SCS-2V-8         | 2     | shared-core  | 8         |                |                   |
| SCS-4V-16        | 4     | shared-core  | 16        |                |                   |
| SCS-4V-16-100s   | 4     | shared-core  | 16        | 100            | Local SSD or NVME |
| SCS-8V-32        | 8     | shared-core  | 32        |                |                   |
| SCS-1V-2         | 1     | shared-core  | 2         |                |                   |
| SCS-2V-4         | 2     | shared-core  | 4         |                |                   |
| SCS-2V-4-20s     | 2     | shared-core  | 4         | 20             | Local SSD or NVME |
| SCS-4V-8         | 4     | shared-core  | 8         |                |                   |
| SCS-8V-16        | 8     | shared-core  | 16        |                |                   |
| SCS-16V-32       | 16    | shared-core  | 32        |                |                   |
| SCS-1V-8         | 1     | shared-core  | 8         |                |                   |
| SCS-2V-16        | 2     | shared-core  | 16        |                |                   |
| SCS-4V-32        | 4     | shared-core  | 32        |                |                   |
| SCS-1L-1         | 1     | crowded-core | 1         |                |                   |

#### Recommended

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type |
|------------------|-------|--------------|-----------|----------------|-----------|
| SCS-1V-4-10      | 1     | shared-core  | 4         | 10             | (any)     |
| SCS-2V-8-20      | 2     | shared-core  | 8         | 20             | (any)     |
| SCS-4V-16-50     | 4     | shared-core  | 16        | 50             | (any)     |
| SCS-8V-32-100    | 8     | shared-core  | 32        | 100            | (any)     |
| SCS-1V-2-5       | 1     | shared-core  | 2         | 5              | (any)     |
| SCS-2V-4-10      | 2     | shared-core  | 4         | 10             | (any)     |
| SCS-4V-8-20      | 4     | shared-core  | 8         | 20             | (any)     |
| SCS-8V-16-50     | 8     | shared-core  | 16        | 50             | (any)     |
| SCS-16V-32-100   | 16    | shared-core  | 32        | 100            | (any)     |
| SCS-1V-8-20      | 1     | shared-core  | 8         | 20             | (any)     |
| SCS-2V-16-50     | 2     | shared-core  | 16        | 50             | (any)     |
| SCS-4V-32-100    | 4     | shared-core  | 32        | 100            | (any)     |
| SCS-1L-1-5       | 1     | crowded-core | 1         | 5              | (any)     |

### SCS Standard Images (scs-0104-v1-standard-images)

	The SCS-0104 standard establishes guidelines for virtual machine images in Sovereign Cloud Stack (SCS) environments,
	specifying mandatory, recommended, and optional images via a YAML file, ensuring interoperability and streamlined
	deployments. It mandates that image upload via Glance must be allowed, ensuring flexibility for users. The standard's
	machine-readable document facilitates automated processing for compliance and integration purposes, promoting
	consistency and reliability in cloud environments.


```yaml
images:
- name: "Ubuntu 22.04"
  source:
  - https://cloud-images.ubuntu.com/releases/jammy/
  - https://cloud-images.ubuntu.com/jammy/
  status: mandatory
- name: "ubuntu-capi-image"
  name_scheme: "ubuntu-capi-image-v[0-9].[0-9]+(.[0-9]+)?"
  source: https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube
  status: recommended
- name: "Ubuntu 20.04"
  source:
  - https://cloud-images.ubuntu.com/releases/focal/
  - https://cloud-images.ubuntu.com/focal/
- name: "Debian 12"
  source:
  - https://cloud.debian.org/images/cloud/bookworm/
  - https://cdimage.debian.org/cdimage/cloud/bookworm/
- name: "Debian 11"
  source:
  - https://cloud.debian.org/images/cloud/bullseye/
  - https://cdimage.debian.org/cdimage/cloud/bullseye/
- name: "Debian 10"
  source:
  - https://cloud.debian.org/images/cloud/buster/
  - https://cdimage.debian.org/cdimage/cloud/buster/
```

### SSD Flavors (scs-0105-v1-standard-images)

This standard extends the required standard flavors for OpenStack to include some flavors that contain
local SSDs or faster technologies. This is required in order to satisfy access times, write times and other
speed related constraints.
The standard was mainly introduced for things like databases, that want to avoid write latencies or scheduling
of network storage, which is also important for the etcd database used by Kubernetes.

The general naming schema can be seen in the [following table](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0100-v3-flavor-naming.md),
but note that this is already included in the table found in [### SCS Standard Flavors and Properties (scs-0103-v1-standard-flavors)] and
is only here for reference.

| Recommended name | vCPUs | vCPU type    | RAM [GiB] | Root disk [GB] | Disk type         |
|------------------|-------|--------------|-----------|----------------|-------------------|
| SCS-2V-4-20s     | 2     | shared-core  | 4         | 20             | Local SSD or NVME |
| SCS-4V-16-100s   | 4     | shared-core  | 16        | 100            | Local SSD or NVME |