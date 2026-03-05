# Testsuite for SCS standards

The tool `scs-compliance-check.py` parses a
[certificate scope specification](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0003-v1-sovereign-cloud-standards-yaml.md)
and executes the test executables referenced in there.

## Local execution (Linux, BSD, ...)

Please ensure you have installed the testsuite dependencies from `requirements.txt`
on your machine. We recommended using Python >= 3.10 and to install the
requirements into a virtualenv as follows:

```shell
cd Tests
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

At the moment, there are two cloud layers that can be checked: IaaS and KaaS.
For both types of checks, the exit code indicates success (0) or failure (!= 0).
You can also request a YAML report using the option `-o OUTPUT.yaml`

### IaaS checks

Install IaaS-specific requirements:

```shell
pip install -r iaas/requirements.txt
```

Make sure that you have Sonobuoy (diagnostic tool that makes it easier to understand the state of a K8s cluster) installed.
You can find install instructions [here](https://sonobuoy.io/docs/main/).

With a cloud environment configured in your `~/.config/openstack/clouds.yaml`
and `secure.yaml`, then run

```shell
./scs-compliance-check.py -s CLOUDNAME -a os_cloud=CLOUDNAME scs-compatible-iaas.yaml
```

Replace `CLOUDNAME` with the name of your cloud environment as
specified in `clouds.yaml`.

### KaaS checks

Install KaaS-specific requirements:

```shell
pip install -r kaas/requirements.txt
```

Additionally, Sonobuoy must be installed and in your PATH environment variable.

Given a kubeconfig file `path/to/kubeconfig.yaml`, run

```shell
./scs-compliance-check.py -v -a kubeconfig=path/to/kubeconfig.yaml -a subject_root=. -s SUBJECT -o report.yaml scs-compatible-kaas.yaml
```

Replace `SUBJECT` with an arbitrary, but meaningful subject name. Also, please note that the check
will always use the `current-context` of the kubeconfig and will fail if it isn't set.

Note: Sonobuoy checks (such as CNCF k8s conformance) are known to run for multiple hours (during which
you won't see feedback). If you want to save wall-time by running the sonobuoy checks in parallel,
simply add `-a execution_mode=parallel` to the command-line.

A report in YAML format will be created.

Additionally, the directory `sono-results` will be generated. It contains a JUnit XML file:
`plugins/e2e/results/global/junit_01.xml`. You can render it to HTML with a tool like junit2html.
This might give you hints as to why a test failed.

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
  -t/--tests REGEX: regular expression to select individual testcases based on their ids
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
docker run -v /path/to/kubeconfig.yaml:/root/kubeconfig.yaml:ro scs-compliance-check -a kubeconfig=/root/kubeconfig.yaml -a subject_root=. -s SUBJECT scs-compatible-kaas.yaml
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

We use **pip-compile** to pin and upgrade our dependencies in a controlled manner.

With `pip-compile`, you list your dependencies with as few version constraints as
possible in a dedicated file, and then you have pip-compile generate the conventional
`requirements.txt` with fully pinned dependencies.

The tool `pip-compile` can be installed via `pip install pip-tools`.
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

We use a **layered approach** to allow for selective installation:

- the most basic layer is `requirements.in`,
- above that we have `iaas/requirements.in` and `kaas/requirements.in`, and
- at the very top we have `test-requirements.in`.

Whenever you change or recompile one of these layers,
*all layers above that layer have to be recompiled as well*.

Note: The Python version used for running `pip-compile` should be consistent. The currently
used version is documented in the header of the `requirements.txt`. It should match the
version used in the Docker image (see [Dockerfile](Dockerfile)) and in our GitHub
workflows (`lint-python.yml` and `test-python.yml` in `.github/workflows`).
