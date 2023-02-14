# Testsuite for SCS standards

The tool `scs-compliance-check.py` parses a 
[compliance definition file](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md)
and executes the test executables referenced in there for
the specified layer (`iaas` or `kaas`).

## Local execution (Linux, BSD, ...)

On your Linux machine, ensure you have `python3-openstacksdk` and
`python3-PyYAML` installed, a cloud environment configured in your
`~/.config/openstack/clouds.yaml` and `secure.yaml` and then run
```shell
./scs-compliance-check.py scs-compatible.yaml iaas --os-cloud CLOUDNAME
```
Replace `CLOUDNAME` with the name of your cloud environment as
specified in `clouds.yaml`.

The exit code indicates success (0) or failure (!= 0).
You can also request a YAML report using the option `-o OUTPUT.yaml`

## Usage information (help output)
```text
Usage: scs-compliance-check.py [options] compliance-spec.yaml layer [layer [layer]]
Options: -v/--verbose: More verbose output
 -q/--quiet: Don't output anything but errors
 -s/--single-layer: Don't perform required checks for dependant layers
 -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
 -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
 -c/--os-cloud CLOUD: Use specified cloud env (instead of OS_CLOUD env var)
 -o/--output path: Generate yaml report of compliance check under given path
```

## Testing in docker containers
### Build a docker container
```shell
docker build --tag scs-test .
```

### Run tests in a docker container
```shell
docker run -it --env OS_CLOUD=CLOUDNAME -v ~/.config/openstack:/root/.config/openstack:ro scs-test
```

### Debugging
```shell
docker run -it --env OS_CLOUD=CLOUDNAME -v ~/.config/openstack:/root/.config/openstack:ro --entrypoint /bin/bash scs-test
```
