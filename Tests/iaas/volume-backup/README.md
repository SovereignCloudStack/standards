# Volume Backup API Test Suite

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
python3 volume-backup-tester.py --os-cloud mycloud
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

If the test suite fails and leaves test resources behind, the "`--cleanup-only`" flag may be used to delete those resources from the domains:

```bash
python3 volume-backup-tester.py --os-cloud mycloud --cleanup-only
```

For any further options consult the output of "`python3 volume-backup-tester.py --help`".

### Script Behavior & Test Results

> **NOTE:** Before any execution of test batches, the script will automatically perform a cleanup of volumes and volume backups matching a special prefix (see the "`--prefix`" flag).
> This cleanup behavior is identical to "`--cleanup-only`".

The script will print all cleanup actions and passed tests to `stdout`.

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will halt, print the exact error to `stderr` and return with a non-zero exit code.

In case of a failed test, cleanup is not performed automatically, allowing for manual inspection of the cloud state for debugging purposes.
Although unnecessary due to automatic cleanup upon next execution, you can manually trigger a cleanup using the "`--cleanup-only`" flag of this script.
