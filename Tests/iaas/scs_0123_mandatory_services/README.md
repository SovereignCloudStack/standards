# Mandatory IaaS Service APIs Test Suite

## Test Environment Setup

### Test Execution Environment

> **NOTE:** The test execution procedure does not require cloud admin rights.

To execute the test suite a valid cloud configuration for the OpenStack SDK in the shape of "`clouds.yaml`" is mandatory[^1].
**The file is expected to be located in the current working directory where the test script is executed unless configured otherwise.**

[^1]: [OpenStack Documentation: Configuring OpenStack SDK Applications](https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html)

The test execution environment can be located on any system outside of the cloud infrastructure that has OpenStack API access.
Make sure that the API access is configured properly in "`clouds.yaml`".

It is recommended to use a Python virtual environment[^2].
Next, install the OpenStack SDK and boto3 required by the test suite:

```bash
pip3 install openstacksdk
pip3 install boto3
```

Within this environment execute the test suite.

[^2]: [Python 3 Documentation: Virtual Environments and Packages](https://docs.python.org/3/tutorial/venv.html)

## Test Execution

The test suite is executed as follows:

```bash
python3 mandatory-iaas-services.py --os-cloud mycloud
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

If the deployment uses s3 only and does not have the object store endpoint specified in the service catalog, the "`--s3-endpoint`" flag may be used to specify the s3 endpoint.
In that case the "`--s3-access`" and "`--s3-access-secret`" flags must also be set, to give all necessery credentials to the test suite:

```bash
python3 mandatory-iaas-services3.py --os-cloud mycloud2 --s3-endpoint "http://s3-endpoint:9000" --s3-access test-user --s3-access-secret test-user-secret
```

For any further options consult the output of "`python3 volume-backup-tester.py --help`".

### Script Behavior & Test Results

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will halt, print the exact error to `stderr` and return with a non-zero exit code.

There is no cleanup done by this test as it mainly only inspect the service catalog and only for the object store creates a bucket, which is then promptly deleted.
