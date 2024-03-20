# Testsuite for SCS standards

The tool `scs-compliance-check.py` parses a
[compliance definition file](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md)
and executes the test executables referenced in there for
the specified layer (`iaas` or `kaas`).

## Local execution (Linux, BSD, ...)

On your Linux machine, please ensure you have installed the testsuite dependencies
from `requirements.txt`. We recommended using Python >= 3.10 and to install the
requirements into a virtualenv as follows:

```shell
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

With a cloud environment configured in your `~/.config/openstack/clouds.yaml`
and `secure.yaml`, then run

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
docker build --tag scs-compliance-check .
```

### Run tests in a docker container

```shell
docker run -it --env OS_CLOUD=CLOUDNAME -v ~/.config/openstack:/root/.config/openstack:ro scs-compliance-check
```

The Docker entrypoint uses [scs-compatible-iaas.yaml](scs-compatible-iaas.yaml)
on the `iaas` layer by default. You can use an alternative spec file by simply
appending it to the above call, e.g.

```shell
docker run -it --env OS_CLOUD=CLOUDNAME -v ~/.config/openstack:/root/.config/openstack:ro scs-compliance-check my-own-certification.yaml iaas
```

### Debugging

```shell
docker run -it --env OS_CLOUD=CLOUDNAME -v ~/.config/openstack:/root/.config/openstack:ro --entrypoint /bin/bash scs-compliance-check
```

## Information for developers

## Unit and regression tests

Some of the conformance tests scripts are themselves tested with unit tests.

To run them, first ensure that you have installed the unit test dependencies:

```shell
python3 -m venv .venv && source .venv/bin/activate   # if not already done
pip install -r test-requirements.txt
```

Now you can run the unit tests with `pytest`:

```shell
# Option A: let pytest discover and run all unit tests (**/*_test.py)
pytest

# Option B: run only a subset of the tests
pytest kaas/k8s-version-policy/k8s_version_policy_test.py
```

You are encouraged to cover new conformance tests with unit tests!
We run the tests on a regular basis in our GitHub workflows.

## Maintaining the Python dependencies

We manage Python dependencies in `requirements.in` and `test-requirements.in`.
The latter is a superset of the former one and lists the additional dependencies
for the [unit tests](#unit-and-regression-tests).
The `*.in` files are fed to `pip-compile` to produce corresponding `*.txt` files
that contain an exact listing of *all* dependencies, including transitive ones.

`pip-compile` can be installed via `pip install pip-tools`.
It needs to be run in two cases:

1. You modified an `*.in` file: run `pip-compile <INFILE>` (e.g.,
   `pip-compile test-requirements.in`).
2. You want to bump the pinned dependencies: add the `--upgrade` flag to the
   `pip-compile` invocation (e.g., `pip-compile --upgrade requirements.in`).

Note: The Python version used for running `pip-compile` should be consistent. The currently
used version is documented in the header of the `requirements.txt`. It should match the
version used in the Docker image (see [Dockerfile](Dockerfile)) and in our GitHub
workflows (`lint-python.yml` and `test-python.yml` in `.github/workflows`).
