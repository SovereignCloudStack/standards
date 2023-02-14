# Testsuite for SCS standards

The tool `scs-compliance-check.py` parses a 
[compliance definition file](https://github.com/SovereignCloudStack/standards/pull/214#issuecomment-1429883879)
and executes the test executables referenced in there for
the specified layer (`iaas` or `kaas`).

## Local execution (Linux, BSD, ...)

On your Linux machine, ensure you have python3-openstacksdk and
python3-PyYAML installed, a cloud environment configured in your
`~/.config/openstack/clouds.yaml` and `secure.yaml` and then run
```shell
./scs-compliance-check.py scs-compatible.yaml iaas --os-cloud CLOUDNAME
```
Replace `CLOUDNAME` with the name of your cloud environment as
specified in `clouds.yaml`.

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
