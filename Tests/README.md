# Testsuite for SCS standards

The tool `scs-compliance-check.py` parses a
[certificate scope specification](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md)
and executes the test executables referenced in there.

## Local execution (Linux, BSD, ...)

On your Linux machine, please ensure you have installed the testsuite dependencies
from `requirements.txt`. We recommended using Python >= 3.10 and to install the
requirements into a virtualenv as follows:

```shell
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

At the moment, there are two cloud layers that can be checked: IaaS and KaaS.
For both types of checks, the exit code indicates success (0) or failure (!= 0).
You can also request a YAML report using the option `-o OUTPUT.yaml`

### IaaS checks

With a cloud environment configured in your `~/.config/openstack/clouds.yaml`
and `secure.yaml`, then run

```shell
./scs-compliance-check.py -s CLOUDNAME -a os_cloud=CLOUDNAME scs-compatible-iaas.yaml
```

Replace `CLOUDNAME` with the name of your cloud environment as
specified in `clouds.yaml`.

### KaaS checks

Given a kubeconfig file `path/to/kubeconfig.yaml`, run

```shell
./scs-compliance-check.py -v -a kubeconfig=path/to/kubeconfig.yaml -s SUBJECT scs-compatible-kaas.yaml
```

Replace `SUBJECT` with an arbitrary, but meaningful subject name.
Also, please note that the check will always use the `current-context` of the kubeconfig and will
fail if it isn't set.

## Usage information (help output)

```text
Usage: scs-compliance-check.py [options] SPEC_YAML

Arguments:
  SPEC_YAML: yaml file specifying the certificate scope

Options:
  -v/--verbose: More verbose output
  -q/--quiet: Don't output anything but errors
     --debug: enables DEBUG logging channel
  -d/--date YYYY-MM-DD: Check standards valid on specified date instead of today
  -V/--version VERS: Force version VERS of the standard (instead of deriving from date)
  -s/--subject SUBJECT: Name of the subject (cloud) under test, for the report
  -S/--sections SECTION_LIST: comma-separated list of sections to test (default: all sections)
  -t/--tests REGEX: regular expression to select individual tests
  -o/--output REPORT_PATH: Generate yaml report of compliance check under given path
  -C/--critical-only: Only return critical errors in return code
  -a/--assign KEY=VALUE: assign variable to be used for the run (as required by yaml file)

With -C, the return code will be nonzero precisely when the tests couldn't be run to completion.
```

## Testing in docker containers

### Build a docker container

```shell
docker build --tag scs-compliance-check .
```

### Run tests in a docker container

You'll have to bind mount your respective config(s), pass required parameters and the specification file.

For IaaS:

```shell
docker run -v ~/.config/openstack:/root/.config/openstack:ro scs-compliance-check -a os_cloud=CLOUDNAME -s CLOUDNAME scs-compatible-iaas.yaml
```

For KaaS:

```shell
docker run -v /path/to/kubeconfig.yaml:/root/kubeconfig.yaml:ro scs-compliance-check -a kubeconfig=/root/kubeconfig.yaml -s SUBJECT scs-compatible-kaas.yaml
```

If you want to test against a cluster running on localhost (e.g., kind cluster), replace
`docker run` with `docker run --net=host` in the above invocation.

### Debugging

```shell
docker run -it -v ~/.config/openstack:/root/.config/openstack:ro --entrypoint /bin/bash scs-compliance-check
```

## Information for developers

### Unit and regression tests

Some of the conformance tests scripts are themselves tested with unit tests.

To run them, first ensure that you have installed the unit test dependencies
in addition to the main dependencies (inside your [virtualenv as described
above](#local-execution-linux-bsd-)):

```shell
pip install -r test-requirements.txt
```

Now you can run the unit tests with `pytest`:

```shell
# Option A: let pytest discover and run all unit tests (**/*_test.py)
pytest

# Option B: run only a subset of the tests
pytest kaas/k8s-version-policy/k8s_version_policy_test.py

# Option C: produce a HTML code coverage report and open it
pytest --cov --cov-report=html
xdg-open htmldoc/index.html
```

You are encouraged to cover new conformance tests with unit tests!
We run the tests on a regular basis in our GitHub workflows.

### Maintaining the Python dependencies

We list our main Python dependencies in `requirements.in`. Additionally, we list
[unit tests](#unit-and-regression-tests) dependencies in `test-requirements.in`.
The `*.in` files are fed to `pip-compile` to produce corresponding `*.txt` files
that contain an exact, version-pinned listing of *all* dependencies, including
transitive ones.

`pip-compile` can be installed via `pip install pip-tools`.
It needs to be run in two cases:

1. You modified an `*.in` file: run `pip-compile <INFILE>`. For example:

   ```shell
   pip-compile test-requirements.in
   ```

2. You want to bump the pinned dependencies: add the `--upgrade` flag to the
   `pip-compile` invocation. For example:

   ```shell
   pip-compile --upgrade requirements.in
   ```

Note: The Python version used for running `pip-compile` should be consistent. The currently
used version is documented in the header of the `requirements.txt`. It should match the
version used in the Docker image (see [Dockerfile](Dockerfile)) and in our GitHub
workflows (`lint-python.yml` and `test-python.yml` in `.github/workflows`).
