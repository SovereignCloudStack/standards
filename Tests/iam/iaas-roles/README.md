# Standard Roles Test Suite

## Test Environment Setup

### API User Account

The test suite strictly requires an OpenStack user that possesses the following access rights:

1. the "`member`" role in the project referenced as authentication target
2. access permissions to the "`list_roles`" in the Identity API

The second requirement (access to "`list_roles`") is usually not granted to users with the "`member`" role in default configurations and only works for user accounts also possessing the "`manager`" role in the domain.
So the test would require an user account possessing both the "`member`" role in a project as well as the "`manager`" role in the domain.

Note that the "`manager`" role only works this way starting with OpenStack Keystone 2024.2.
If an older Keystone release is used, see the alternative instructions below.

#### Alternative using a dedicated role

One alternative way to address this is for older Keystone releases is to create a dedicated role in the cloud environment which only has access to the role list endpoint and assign it to the user account intended for testing (in addition to the "`member`" role).

To achieve this, first the role has to be created and assigned:

```sh
openstack role create scs-conformance-tester
openstack role add --user ... --project ... member
openstack role add --user ... --project ... scs-conformance-tester
```

Finally, the Keystone API policy definition for the role list endpoint has to be extended to allow this role.
The following is an example entry for `/etc/keystone/policy.yaml` of the Keystone service:

```yaml
"identity:list_roles": "... or role:scs-conformance-tester"
```

("`...`" is a placeholder and must be replaced by the current content of the `"identity:list_roles"` rule!)

The credentials of the resulting user must be specified in the "`clouds.yaml`" accordingly (see below).

### Test Execution Environment

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
python3 standard-roles-check.py --os-cloud mycloud
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

For any further options consult the output of "`python3 standard-roles-check.py --help`".

### Script Behavior & Test Results

The script will print all executed tests and their results to `stdout`.

If all tests pass, the script will return with an exit code of `0`.

If any test fails, the script will abort, print the failed test to `stdout` and return with a non-zero exit code.
