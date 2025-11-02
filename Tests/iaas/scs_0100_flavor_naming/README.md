# SCS flavor name tooling

This directory contains two basic tools:

- `cli.py`, a command-line interface for syntax-checking flavor names, turning them into prose descriptions
  or yaml documents, and interactively constructing flavor names;
- `flavor-form.py`, a CGI script for a web form that offers roughly the same features.

Besides, it contains the scripts `flavor-name-check.py` and `flavor-name-describe.py`, which have been
superseded by `cli.py`, and it contains `flavor-form-server.py`, which is a most simple webserver that can
be used to test the `flavor-form.py` CGI script.

## cli.py

The command-line syntax of this script is best shown via the built-in help function:

```console
$ ./cli.py --help
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --debug
  -v, --verbose
  --help         Show this message and exit.

Commands:
  input  Interactively constructs a flavor name.
  parse  Validates flavor names, optionally turns into prose/yaml.
```

### Parse

```console
 ./cli.py parse --help
Usage: cli.py parse [OPTIONS] {v1|v1/v2|v2/v1|v2|v3|latest} [NAME]...

  Validates flavor names, optionally turns into prose/yaml.

  The first argument selects the version of the flavor naming standard upon
  which to base the syntax validation. With 'v1/v2', flavor names of both
  kinds are accepted, but warnings are emitted for v2, and similarly with
  'v2/v1', where warnings are emitted for v1.

Options:
  -o, --output [none|prose|yaml]  select output format (default: none)
  --help                          Show this message and exit.
```

Here is an example invocation:

```console
$ ./cli.py parse --output prose v1/v2 SCS-16T-64-3x10s_bms_hwv_i3h_GNa-64_ib 
WARNING: Name is merely tolerated v2: SCS-16T-64-3x10s_bms_hwv_i3h_GNa-64_ib
SCS flavor with 16 High Perf Intel Ice Lake SMT Threads with 64.0 GiB RAM on Bare Metal System with HW virt and SSD 3x10GB root volume and Pass-Through GPU nVidia Ampere (w/ 64 CU/EU/SM) and Infiniband
```

And one example with a wrong name:

```console
$ ./cli.py parse --output prose v3 SCS-2T-4_ic
Extra characters: _ic: SCS-2T-4_ic
```

Noteworthy: if `--verbose` is used, the output format `none` will produce an output for every name (even
those that are valid):

```console
$ ./cli.py --verbose parse v3 SCS-16T-64 SC-2T-4 SCS-2-4
OK: SCS-16T-64
NOT an SCS flavor: SC-2T-4
Failed to parse main part: SCS-2-4
```

### Input

```console
$ ./cli.py input --help
Usage: cli.py input [OPTIONS]

  Interactively constructs a flavor name.

Options:
  --help  Show this message and exit.
```

Example invocation:

```console
$ ./cli.py input
CPU-RAM
 #vCPUs: 16
 CPU type Options:
  L: LowPerf vCPUs
  V: vCPUs
  T: SMT Threads
  C: Dedicated Cores
 CPU type: T
 ?Insec SMT: 
 ##GiB RAM: 64
 ?no ECC: 
 ?RAM Over: 
Disk
 #.NrDisks: 3
 #.GB Disk: 10
 Disk type Options:
  : (unspecified)
  n: Networked
  h: Local HDD
  s: SSD
  p: HiPerf NVMe
 Disk type: s
Hypervisor
 Hypervisor Options:
  kvm: KVM
  xen: Xen
  hyv: Hyper-V
  vmw: VMware
  bms: Bare Metal System
 Hypervisor: bms
Hardware/NestedVirtualization
 ?HardwareVirt: y
CPUBrand
 CPU Vendor Options:
  i: Intel
  z: AMD
  a: ARM
  r: RISC-V
 CPU Vendor: i
 #.CPU Gen Options:
  : (unspecified)
  0: Unspec/Pre-Skylake
  1: Skylake
  2: Cascade Lake
  3: Ice Lake
  4: Sapphire Rapids
 #.CPU Gen: 3
 Performance Options:
  : Std Perf
  h: High Perf
  hh: Very High Perf
  hhh: Very Very High Perf
 Performance: h
GPU
 Type Options:
  g: vGPU
  G: Pass-Through GPU
 Type: G
 Brand Options:
  N: nVidia
  A: AMD
  I: Intel
 Brand: N
 Gen Options:
  : (unspecified)
  f: Fermi
  k: Kepler
  m: Maxwell
  p: Pascal
  v: Volta
  t: Turing
  a: Ampere
  l: AdaLovelace
 Gen: a
 #.CU/EU/SM: 64
 Performance Options:
  : Std Perf
  h: High Perf
  hh: Very High Perf
  hhh: Very Very High Perf
 Performance: 
Infiniband
 ?IB: y
SCS-16T-64-3x10s_bms_i3h_GNa-64_ib
```

Where the final line is the constructed flavor name, and everything above is the interactive session.

## flavor-form.py

This CGI script produces a small web form that can be used to construct (and deconstruct) flavor names. It
can be tested using `flavor-form-server.py` like so:

```console
$ ./flavor-form-server.py 
The form is accessible at http://0.0.0.0:8000/cgi-bin/flavor-form.py
^C
Keyboard interrupt received, exiting.
```
