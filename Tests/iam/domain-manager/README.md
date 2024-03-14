# Domain Manager Standard Test Suite

## Test Environment Setup

### OpenStack Domains and Accounts

The test suite requires a specific domain setup to exist in the OpenStack cloud.
This setup must be prepared before starting test execution.
The following things are required:

- two domains for testing
- a user in each domain with the `manager` role assigned on domain-level
- a properly configured "`domain-manager-test.yaml`"

The creation of these resources is described below.

**NOTE:** The following steps require cloud admin rights.

**WARNING:** Replace the `<REPLACEME>` password placeholders by securely generated passwords in the code blocks below.

As a preliminary step, create the "`manager`" role if it does not exist:

```bash
openstack role create manager
```

First, create two testing domains and a domain manager for each domain:

```bash
openstack domain create scs-test-domain-a
openstack domain create scs-test-domain-b

openstack user create --domain scs-test-domain-b \
    --password "<REPLACEME>" scs-test-domain-b-manager
openstack user create --domain scs-test-domain-a \
    --password "<REPLACEME>" scs-test-domain-a-manager

openstack role add --user scs-test-domain-a-manager \
    --domain scs-test-domain-a manager
openstack role add --user scs-test-domain-b-manager \
    --domain scs-test-domain-b manager
```

Next create a file "`domain-manager-test.yaml`" with the following content:

```yaml
domains:
  - name: "scs-test-domain-a"
    manager:
      username: "scs-test-domain-a-manager"
      password: "<REPLACEME>"
    member_role: "member"
  - name: "scs-test-domain-b"
    manager:
      username: "scs-test-domain-b-manager"
      password: "<REPLACEME>"
    member_role: "member"
```

The YAML file should contain two domains.
A sample file is included in this repository.
The content of the file is structured as follows:

| Setting | Purpose |
|---|---|
| `domains.*.name` | Name of the domain |
| `domains.*.manager` | Login credentials for a user with the `manager` role within the respective domain |
| `domains.*.member_role` | Role that a domain manager is permitted to assign users within the respective domain (default: `member`) |

### Test Execution Environment

> **NOTE:** The test execution procedure does not require cloud admin rights.

To execute the test suite, the "`domain-manager-test.yaml`" configuration file as created above is required as input.
Furthermore, a valid cloud configuration for the OpenStack SDK in the shape of "`clouds.yaml`" is mandatory[^1].
**Both files are expected to be located in the current working directory where the test script is executed unless configured otherwise.**

[^1]: [OpenStack Documentation: Configuring OpenStack SDK Applications](https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html)

The test execution environment can be located on any system outside of the cloud infrastructure that has OpenStack API access.
Make sure that the API access is configured properly in "`clouds.yaml`".
The test suite will start with some basic login tests to verify the API connection for both domains and domain manager accounts.

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
python3 domain-manager-check.py --os-cloud mycloud
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
python3 domain-manager-check.py --os-cloud mycloud --cleanup-only
```

For any further options consult the output of "`python3 domain-manager-check.py --help`".

### Script Behavior & Test Results

> **NOTE:** Before any execution of test batches, the script will automatically perform a cleanup of the configured domains, deleting all users, projects and groups matching a special prefix (see the "`--prefix`" flag).
> This cleanup behavior is identical to "`--cleanup-only`".

The script will print all cleanup actions and passed tests to `stdout`.

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will halt, print the exact error to `stderr` and return with a non-zero exit code.

In case of a failed test, cleanup is not performed automatically, allowing for manual inspection of the cloud state for debugging purposes.
Although unnecessary due to automatic cleanup upon next execution, you can manually trigger a cleanup using the "`--cleanup-only`" flag of this script.
