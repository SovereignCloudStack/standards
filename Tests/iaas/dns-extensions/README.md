# DNS Extensions Test Suite

## Test Environment Setup

### Test Execution Environment

> **NOTE:** The test execution procedure does not require cloud admin rights.

To execute the test suite a valid cloud configuration for the OpenStack SDK in the shape of "`clouds.yaml`" is mandatory[^1].
**The file is expected to be located in the current working directory where the test script is executed unless configured otherwise.**

[^1]: [OpenStack Documentation: Configuring OpenStack SDK Applications](https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html)

The test execution environment can be located on any system outside of the cloud infrastructure that has OpenStack API access.
Make sure that the API access is configured properly in "`clouds.yaml`".

It is recommended to use a Python virtual environment[^2].
Next, install the OpenStack SDK required by the test suite:

```bash
pip3 install openstacksdk
```

Within this environment execute the test suite.

[^2]: [Python 3 Documentation: Virtual Environments and Packages](https://docs.python.org/3/tutorial/venv.html)

## Test Execution

The test suite is executed as follows:

```bash
python3 dns-extensions-check.py --os-cloud mycloud
```

As an alternative to "`--os-cloud`", the "`OS_CLOUD`" environment variable may be specified instead.
The parameter is used to look up the correct cloud configuration in "`clouds.yaml`".
For the example command above, this file should contain a `clouds.mycloud` section like this:

```yaml
---
clouds:
  mycloud:
    auth:
      auth_url: ...
      ...
    ...
```

For any further options consult the output of "`python3 dns-extensions-check.py --help`".

### Script Behavior & Test Results

The script will print all executed tests and their results to `stdout`.

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will abort, print the failed test to `stdout` and return with a non-zero exit code.
