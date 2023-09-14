import openstack
import os
import yaml
import argparse
import keystoneauth1

TEST_RESOURCES_PREFIX = "scs-test-"


def connect(cloud_name: str,
            auth_overrides: dict = None) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.
    :param dict auth_overrides:
        A dict that overrides option of the auth section of the cloud
        configuration of the loaded clouds.yaml. Allows to authenticate
        as a different user based on the same general cloud settings.
        Example:

            {
                "username": "claudia",
                "password": "foobar123!%",
                "project_name": "customer1"
            }

    :returns: openstack.connnection.Connection
    """

    if auth_overrides:
        return openstack.connect(
            cloud=cloud_name,
            auth=auth_overrides
        )
    else:
        return openstack.connect(
            cloud=cloud_name,
        )


def connect_to_domain(cloud_name: str,
                      domain: str,
                      domain_definitions: list[dict]
                      ) -> openstack.connection.Connection:
    domain_def = next(d for d in domain_definitions if d.get("name") == domain)
    auth = {
        "username": domain_def.get("manager").get("username"),
        "password": domain_def.get("manager").get("password"),
        "project_name": "",
        "project_domain_name": "",
        "domain_name": domain_def.get("name"),
        "user_domain_name": domain_def.get("name"),
    }
    return connect(cloud_name, auth_overrides=auth)


def load_domain_definitions(yaml_path: str) -> list[dict]:
    assert os.path.exists(yaml_path), (
        f"Test definition YAML '{yaml_path}' does not exist"
    )
    # validate the schema of the file after loading it
    with open(yaml_path, 'r') as f:
        definitions = yaml.safe_load(f)
        assert "domains" in definitions, (
            f"Test definition YAML '{yaml_path}' "
            f"is missing a 'domains' section")

        assert len(definitions.get("domains")) > 1, (
            f"Test definition YAML '{yaml_path}' "
            f"has less than 2 entries in the 'domains' section; "
            f"at least 2 are required")

        for domain in definitions.get("domains"):
            assert "name" in domain, (
                f"At least one domain in the test definition YAML "
                f"'{yaml_path}' is missing the 'name' property")
            domain_name = domain.get("name")
            assert "manager" in domain, (
                f"Domain '{domain_name}' in the test definition YAML "
                f"'{yaml_path}' is missing the 'manager' subsection")
            manager = domain.get("manager")
            assert "username" in manager, (
                f"Domain '{domain_name}' in the test definition YAML "
                f"'{yaml_path}' is missing the 'manager.username' property")
            assert "password" in manager, (
                f"Domain '{domain_name}' in the test definition YAML "
                f"'{yaml_path}' is missing the 'manager.password' property")
        return definitions


def test_logins(cloud_name: str, domains: list[dict]):
    for domain in domains:
        domain_name = domain.get("name")
        domain_manager = domain["manager"]["username"]
        conn = connect_to_domain(cloud_name, domain_name, domains)
        try:
            conn.identity.find_user(domain_manager)
        except keystoneauth1.exceptions.http.Unauthorized:
            raise Exception(
                f"Login as '{domain_manager}' in domain '{domain_name}' "
                f"failed; make sure that user and domain membership are "
                f"properly configured"
            )
        try:
            assert conn.identity.find_domain(domain_name), (
                f"Lookup of domain '{domain_name}' returned None"
            )
        except Exception as e:
            print(str(e))
            raise Exception(
                f"User '{domain_manager}' cannot discover their own domain "
                f"'{domain_name}'; make sure that Keystone policies are "
                f"correctly applied"
            )


def cleanup(cloud_name: str, domains: list[dict]):
    """
    Uses the configured domain manager user to cleanup any Keystone resources
    that this test suite might have created in the corresponding domains
    during any previous or current execution.
    Resources are discovered within the domains configured for testing only
    and are also checked against a specific name prefix that all test resources
    have to avoid accidental deletion of non-test resources.
    """
    for domain in domains:
        domain_name = domain.get("name")
        print(f"Cleanup starting for domain {domain_name} ...")
        conn = connect_to_domain(cloud_name, domain_name, domains)
        domain_id = conn.identity.find_domain(domain_name).id

        groups = conn.identity.groups(domain_id=domain_id)
        for group in groups:
            if group.name.startswith(TEST_RESOURCES_PREFIX):
                print(f"↳ deleting group '{group.name}' ...")
                conn.identity.delete_group(group.id)

        projects = conn.identity.projects(domain_id=domain_id)
        for project in projects:
            if project.name.startswith(TEST_RESOURCES_PREFIX):
                print(f"↳ deleting project '{project.name}' ...")
                conn.identity.delete_project(project.id)

        users = conn.identity.users(domain_id=domain_id)
        for user in users:
            if user.name == domain["manager"]["username"]:
                # manager should not delete themselves
                print(f"↳ skipping user '{user.name}' (is domain manager) ...")
                continue
            if user.name.startswith(TEST_RESOURCES_PREFIX):
                print(f"↳ deleting user '{user.name}' ...")
                conn.identity.delete_user(user.id)


def test_groups(cloud_name: str, domains: list[dict]):

    # 1st domain
    domain_a = domains[0].get("name")
    conn_a = connect_to_domain(cloud_name, domain_a, domains)
    domain_a_id = conn_a.identity.find_domain(domain_a).id

    # 2nd domain
    domain_b = domains[1].get("name")
    conn_b = connect_to_domain(cloud_name, domain_b, domains)
    domain_b_id = conn_a.identity.find_domain(domain_a).id

    # group creation outside of domain (negative test)
    try:
        conn_a.identity.create_group(
            name="scs-test-group-outside-domain-a",
        )
    except openstack.exceptions.ForbiddenException:
        print("Domain manager cannot create group outside of domain 1: PASS")
    else:
        raise Exception(
            f"Policy error: domain manager can create group outside of domain "
            f"'{domain_a}'"
        )

    # group creation within domain
    domain_a_group = conn_a.identity.create_group(
        name="scs-test-group-outside-domain-a",
        domain_id=domain_a_id
    )
    assert domain_a_group, (
        f"Domain manager cannot create groups within domain '{domain_a}'"
    )
    print("Domain manager can create group within domain 1: PASS")


def main():
    openstack.enable_logging(debug=False)
    domain_yaml_path = "./domain-manager-test.yaml"
    parser = argparse.ArgumentParser(
        description="SCS Domain Manager Conformance Checker")
    parser.add_argument(
        "--os-cloud", type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable"
    )
    parser.add_argument(
        "--domain-config", type=str,
        help=f"Path to the YAML file containing the domain definitions and "
        f"domain manager credentials for testing (default: {domain_yaml_path})"
    )
    parser.add_argument(
        "--cleanup", action="store_true",
        help=f"Instead of executing tests, cleanup all resources within the "
        f"defined domains with the '{TEST_RESOURCES_PREFIX}' prefix"
    )
    args = parser.parse_args()
    if args.domain_config:
        domain_yaml_path = args.domain_config

    # parse cloud name for lookup in clouds.yaml
    cloud = os.environ.get("OS_CLOUD", None)
    if args.os_cloud:
        cloud = args.os_cloud
    assert cloud, (
        "You need to have the OS_CLOUD environment variable set to your cloud "
        "name or pass it via --os-cloud"
    )

    # load the domain test configuration
    domains = load_domain_definitions(domain_yaml_path).get("domains")

    if args.cleanup:
        cleanup(cloud, domains)
    else:
        test_logins(cloud, domains)
        test_groups(cloud, domains)


if __name__ == "__main__":
    main()
