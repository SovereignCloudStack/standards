# Secure Connections Standard Test Suite

## Test Environment Setup

> **NOTE:** The test execution procedure does not require cloud admin rights.

A valid cloud configuration for the OpenStack SDK in the shape of "`clouds.yaml`" is mandatory[^1].
**This file is expected to be located in the current working directory where the test script is executed unless configured otherwise.**

[^1]: [OpenStack Documentation: Configuring OpenStack SDK Applications](https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html)

The test execution environment can be located on any system outside of the cloud infrastructure that has OpenStack API access.
Make sure that the API access is configured properly in "`clouds.yaml`".

It is recommended to use a Python virtual environment[^2].
Next, install the libraries required by the test suite:

```bash
pip3 install openstacksdk sslyze
```

> Note: the version of the sslyze library determines the [version of the Mozilla TLS recommendation JSON](https://wiki.mozilla.org/Security/Server_Side_TLS#JSON_version_of_the_recommendations) that it checks against.

Within this environment execute the test suite.

[^2]: [Python 3 Documentation: Virtual Environments and Packages](https://docs.python.org/3/tutorial/venv.html)

## Test Execution

The test suite is executed as follows:

```bash
python3 tls-checker.py --os-cloud mycloud
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

For any further options consult the output of "`python3 tls-checker.py --help`".

### Script Behavior & Test Results

The script will print all actions and passed tests to `stdout`.

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will halt, print the exact error to `stderr` and return with a non-zero exit code.

Any tests that indicate a recommendation of the standard is not met, will print a warning message under the corresponding endpoint output.
However, unmet recommendations will not count as errors.
