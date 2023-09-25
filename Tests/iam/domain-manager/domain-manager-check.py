import openstack
import os
import yaml
import argparse
import keystoneauth1

"""Domain Manager policy configuration validation script

This script uses the OpenStack SDK to validate the proper implementation
of the Domain Manager standard via the OpenStack Keystone API.

Please make sure to run this script with the "--cleanup" flag before and after
each execution. This will remove all IAM resources (projects, users, groups -
except for the domain managers themselves) within the configured test domains
that have the TEST_RESOURCES_PREFIX in front of their name.
The script expects the configured test domains to be empty!
"""

# prefix to be included in the names of any Keystone resources created
# used by the "--cleanup" flag do identify resources that can be safely deleted
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
    print("\nExecuting tests for basic logins ...")
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
        print(f"Domain manager login for domain '{domain_name}' works: PASS")


def cleanup(cloud_name: str, domains: list[dict]):
    """
    Uses the configured domain manager users to cleanup any Keystone resources
    that this test suite might have created in the corresponding domains
    during any previous or current execution.
    Resources are discovered within the domains configured for testing only
    and are also checked against a specific name prefix that all test resources
    have to avoid accidental deletion of non-test resources.
    """
    print(f"\nPerforming cleanup for resources with the "
          f"'{TEST_RESOURCES_PREFIX}' prefix ...")
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


def _raisesException(exception, func, *args, **kwargs):
    """
    Mimics the functionality of `assertRaises()` for plain `assert`.
    Calls the function passed as `func` and observes the exception behavior.
    If it raises the exception passed as `exception`, returns True.
    If it raises any other exception, the exception is re-raised.
    In any other case returns False.

    To be used in `assert` statements.
    """
    try:
        func(*args, **kwargs)
    except exception:
        return True
    except Exception as e:
        raise e
    else:
        return False


def test_users(cloud_name: str, domains: list[dict]):
    """
    Test correct domain scoping for domain managers relating to the users
    feature of Keystone.
    """
    print("\nExecuting tests for Keystone users ...")

    # 1st domain = D1
    domain_a_name = domains[0].get("name")
    conn_a = connect_to_domain(cloud_name, domain_a_name, domains)
    domain_a = conn_a.identity.find_domain(domain_a_name)
    domain_a_role = conn_a.identity.find_role(domains[0].get("member_role"))

    # 2nd domain = D2
    domain_b_name = domains[1].get("name")
    conn_b = connect_to_domain(cloud_name, domain_b_name, domains)
    domain_b = conn_b.identity.find_domain(domain_b_name)
    domain_b_role = conn_b.identity.find_role(domains[1].get("member_role"))

    domain_a_user_name = f"{TEST_RESOURCES_PREFIX}domain-a-user"
    domain_b_user_name = f"{TEST_RESOURCES_PREFIX}domain-b-user"

    # [D1] domain manager can create user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_user,
        name=domain_a_user_name,
        domain_id=domain_a.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"create user within domain"
    )
    print("Domain manager can create user within domain: PASS")

    # [D1] domain manager can find user by id or name within domain
    domain_a_user = conn_a.identity.find_user(domain_a_user_name)
    assert domain_a_user is not None, (
        f"Policy error: domain manager of '{domain_a.name}' cannot find user "
        f"'{domain_a_user_name}' by name within domain"
    )
    assert conn_a.identity.find_user(domain_a_user.id) is not None, (
        f"Policy error: domain manager of '{domain_a.name}' cannot find user "
        f"'{domain_a_user_name}' by id within domain"
    )
    print("Domain manager can find user within domain: PASS")

    # D1 domain manager can update user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.update_user,
        domain_a_user.id, email="CHANGED-MAIL"
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"update user '{domain_a_user.name}' within domain"
    )
    # refresh the user object
    domain_a_user = conn_a.identity.find_user(domain_a_user_name)
    assert domain_a_user is not None and \
        domain_a_user.email == "CHANGED-MAIL", (
            f"Policy error: domain manager of domain '{domain_a.name}' cannot "
            f"successfully update user '{domain_a_user.name}'s email address "
            f"within domain"
        )
    print("Domain manager can update user metadata within domain: PASS")

    # prepare a user in D2 for all subsequent tests
    domain_b_user = conn_b.identity.create_user(
        name=domain_b_user_name, domain_id=domain_b.id
    )

    # [D1] domain manager can only find users within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.users
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"list users"
    )
    # the user of D2 should not appear in the list
    for found_user in list(conn_a.identity.users()):
        assert found_user.domain_id == domain_a.id, (
            f"Policy error: domain manager of domain '{domain_a.name}' is "
            f"able to list users outside of domain"
        )
    print("Domain manager can only list users within domain: PASS")

    # [D1] domain manager can assign domain-level role to user within domain
    # note that assign_domain_role_to_user() and
    # unassign_domain_role_from_user() do not raise any exception if they fail
    # the result must be checked by querying resulting assignments
    conn_a.identity.assign_domain_role_to_user(
        domain_a.id, domain_a_user.id, domain_a_role.id
    )
    assert conn_a.identity.validate_user_has_domain_role(
        domain_a.id, domain_a_user.id, domain_a_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"assign domain-level role to user '{domain_a_user.name}' within "
        f"domain"
    )
    print("Domain manager can assign domain-level role to user within domain: "
          "PASS")
    conn_a.identity.unassign_domain_role_from_user(
        domain_a.id, domain_a_user.id, domain_a_role.id
    )
    assert not conn_a.identity.validate_user_has_domain_role(
        domain_a.id, domain_a_user.id, domain_a_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"unassign domain-level role to user '{domain_a_user.name}' within "
        f"domain"
    )
    print("Domain manager can unassign domain-level role from user within "
          "domain: PASS")

    # [D1] domain manager can delete user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.delete_user,
        domain_a_user.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"delete user '{domain_a_user.name}' within domain"
    )
    print("Domain manager can delete user within domain: PASS")

    # [D1] domain manager cannot create user without domain scope (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_user,
        name=f"{domain_a_user_name}-outside-of-a"
    ), (
        f"Policy error: domain manager of dofmain '{domain_a.name}' is able to "
        f"create user outside of domain scope"
    )
    print("Domain manager cannot create user outside of domain scope: PASS")

    # [D1] domain manager cannot create user in D2 (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_user,
        name=f"{domain_a_user_name}-in-domain-2",
        domain_id=domain_b.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"create user in foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot create user in foreign domain: PASS")

    # [D1] cannot find user in D2 (negative test)
    user = conn_a.identity.find_user(domain_b_user.id)
    assert user is None, (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"find user '{domain_b_user.name}' of foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot find user in foreign domain: PASS")

    # [D1] domain manager cannot update user in D2 (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.update_user,
        domain_b_user.id,
        email="CHANGED-MAIL"
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"update user '{domain_b_user.name}' of foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot update user in foreign domain: PASS")

    # [D1] domain manager cannot delete user in D2 (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.delete_user,
        domain_b_user.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"delete user '{domain_b_user.name}' of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot delete user in foreign domain: PASS")

    # [D1] domain manager cannot assign domain-level role to user in D2
    # there are two cases: assigning a role within domain D2 to:
    # 1) user is part of domain D1
    conn_a.identity.assign_domain_role_to_user(
        domain_b.id, domain_a_user.id, domain_b_role.id
    )
    assert not conn_a.identity.validate_user_has_domain_role(
        domain_b.id, domain_a_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"assign domain-level role to user '{domain_a_user.name}' within "
        f"foreign domain '{domain_b.name}'"
    )
    # 2) user is part of domain D2
    conn_a.identity.assign_domain_role_to_user(
        domain_b.id, domain_b_user.id, domain_b_role.id
    )
    assert not conn_b.identity.validate_user_has_domain_role(
        domain_b.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"assign domain-level role to user '{domain_b_user.name}' within "
        f"foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot assign domain-level role to user in foreign "
          "domain: PASS")

    # [D1] domain manager cannot unassign domain-level role from user in D2
    # first prepare the assignment as domain manager of D2 via conn_b
    conn_b.identity.assign_domain_role_to_user(
        domain_b.id, domain_b_user.id, domain_b_role.id
    )
    assert conn_b.identity.validate_user_has_domain_role(
        domain_b.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Test setup error: assigning domain-level to user "
        f"'{domain_b_user.name}' within domain '{domain_b.name}' "
        f"as domain manager of domain '{domain_b.name}' failed but is "
        f"required by the testing process; please check "
        f"the test implementation and domain configuration"
    )
    # next, attempt to unassign as domain manager of D1 via conn_a
    conn_a.identity.unassign_domain_role_from_user(
        domain_b.id, domain_b_user.id, domain_b_role.id
    )
    assert conn_b.identity.validate_user_has_domain_role(
        domain_b.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"unassign domain-level role from user '{domain_b_user.name}' within "
        f"foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot unassign domain-level role from user in "
          "foreign domain: PASS")


def test_projects(cloud_name: str, domains: list[dict]):
    """
    Test correct domain scoping for domain managers relating to the projects
    feature of Keystone.
    """
    print("\nExecuting tests for Keystone projects ...")

    # 1st domain = D1
    domain_a_name = domains[0].get("name")
    conn_a = connect_to_domain(cloud_name, domain_a_name, domains)
    domain_a = conn_a.identity.find_domain(domain_a_name)
    domain_a_role = conn_a.identity.find_role(domains[0].get("member_role"))
    domain_a_user = conn_a.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-user", domain_id=domain_a.id
    )

    # 2nd domain = D2
    domain_b_name = domains[1].get("name")
    conn_b = connect_to_domain(cloud_name, domain_b_name, domains)
    domain_b = conn_b.identity.find_domain(domain_b_name)
    domain_b_role = conn_b.identity.find_role(domains[1].get("member_role"))
    domain_b_user = conn_b.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-b-user", domain_id=domain_b.id
    )

    domain_a_project_name = f"{TEST_RESOURCES_PREFIX}domain-a-project"
    domain_b_project_name = f"{TEST_RESOURCES_PREFIX}domain-b-project"

    # [D1] domain manager can project user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_project,
        name=domain_a_project_name,
        domain_id=domain_a.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"create project within domain"
    )
    print("Domain manager can create project within domain: PASS")

    # [D1] domain manager can find project by id or name within domain
    domain_a_project = conn_a.identity.find_project(domain_a_project_name)
    assert domain_a_project is not None, (
        f"Policy error: domain manager of '{domain_a.name}' cannot find "
        f"project '{domain_a_project_name}' by name within domain"
    )
    assert conn_a.identity.find_project(domain_a_project.id) is not None, (
        f"Policy error: domain manager of '{domain_a.name}' cannot find "
        f"project '{domain_a_project_name}' by id within domain"
    )
    print("Domain manager can find project within domain: PASS")

    # D1 domain manager can update project within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.update_project,
        domain_a_project.id, description="CHANGED-DESCRIPTION"
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"update project '{domain_a_project.name}' within domain"
    )
    # refresh the project object
    domain_a_project = conn_a.identity.find_project(domain_a_project_name)
    assert domain_a_project is not None and \
        domain_a_project.description == "CHANGED-DESCRIPTION", (
            f"Policy error: domain manager of domain '{domain_a.name}' cannot "
            f"successfully update project '{domain_a_project.name}'s "
            f"description within domain"
        )
    print("Domain manager can update project metadata within domain: PASS")

    # [D1] domain manager can assign project-level role to user within domain
    # note that assign_domain_role_to_user() does not raise exceptions; results
    # have to be checked explicitly
    conn_a.identity.assign_project_role_to_user(
        domain_a_project.id, domain_a_user.id, domain_a_role.id
    )
    assert conn_a.identity.validate_user_has_project_role(
        domain_a_project.id, domain_a_user.id, domain_a_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"assign project-level role to user '{domain_a_user.name}' for "
        f"project '{domain_a_project.name}' within domain"
    )
    print("Domain manager can assign project-level role to user within domain: "
          "PASS")

    # [D1] domain manager can list projects for user in domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.user_projects,
        domain_a_user.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"list projects for user '{domain_a_user.name}' within domain"
    )
    projects = list(conn_a.identity.user_projects(domain_a_user.id))
    assert len(projects) == 1 and projects[0].id == domain_a_project.id, (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"successfully list projects for user '{domain_a_user.name}' within "
        f"domain"
    )
    print("Domain manager can list projects for user within domain: PASS")

    # [D1] domain manager can unassign project-level role from user within
    # domain
    # note that unassign_project_role_from_user() does not raise exceptions;
    # results have to be checked explicitly
    conn_a.identity.unassign_project_role_from_user(
        domain_a_project.id, domain_a_user.id, domain_a_role.id
    )
    assert not conn_a.identity.validate_user_has_project_role(
        domain_a_project.id, domain_a_user.id, domain_a_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"successfully unassign project-level role from user "
        f"'{domain_a_user.name}' for project '{domain_a_project.name}' within "
        f"domain"
    )
    print("Domain manager can unassign project-level role from user within "
          "domain: PASS")

    # [D1] domain manager can list projects for user in domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.delete_project,
        domain_a_project.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot "
        f"delete project '{domain_a_project.name}' within domain"
    )
    print("Domain manager can delete project within domain: PASS")

    # [D1] domain manager cannot create project without domain scope (negative
    # test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_project,
        name=f"{domain_a_project_name}-outside-of-a",
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"create project without domain scope"
    )
    print("Domain manager cannot create project outside of domain scope: PASS")

    # [D1] domain manager cannot create project in domain D2 (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_project,
        name=f"{domain_a_project_name}-in-b",
        domain_id=domain_b.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"create project in foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot create project in foreign domain: PASS")

    # create a project in D2 for further tests
    domain_b_project = conn_b.identity.create_project(
        name=domain_b_project_name,
        domain_id=domain_b.id
    )

    # [D1] domain manager cannot discover project in foreign domain D2
    # (negative test)
    assert conn_a.identity.find_project(domain_b_project_name) is None, (
        f"Policy error: domain manager of '{domain_a.name}' is able to find "
        f"project '{domain_b_project_name}' by name in foreign domain "
        f"'{domain_b.name}'"
    )
    assert conn_a.identity.find_project(domain_b_project.id) is None, (
        f"Policy error: domain manager of '{domain_a.name}' is able to find "
        f"project '{domain_b_project_name}' by id in foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot find project in foreign domain: PASS")

    # [D1] domain manager cannot update project in foreign domain D2 (negative
    # test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.update_project,
        domain_b_project.id,
        description="CHANGED-DESCRIPTION"
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"update project '{domain_b_project.name}' of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot update project in foreign domain: PASS")

    # [D1] domain manager cannot delete project in foreign domain D2 (negative
    # test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.delete_project,
        domain_b_project.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"delete project '{domain_b_project.name}' of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot delete project in foreign domain: PASS")

    # [D1] domain manager cannot assign project-level role to user within
    # foreign domain D2 (negative test)
    # 1) user in D2 + project in D2
    conn_a.identity.assign_project_role_to_user(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    )
    # as conn_b check the assignment
    assert not conn_b.identity.validate_user_has_project_role(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"assign project-level role to user '{domain_b_user.name}' "
        f"for project '{domain_b_project.name}' within foreign domain "
        f"'{domain_b.name}'"
    )
    # 2) user in D2 + project in D1
    conn_a.identity.assign_project_role_to_user(
        domain_a_project.id, domain_b_user.id, domain_a_role.id
    )
    # as conn_b check the assignment
    assert not conn_b.identity.validate_user_has_project_role(
        domain_a_project.id, domain_b_user.id, domain_a_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"assign project-level role to user '{domain_b_user.name}' of foreign domain "
        f"'{domain_b.name}' "
        f"for project '{domain_a_project.name}'"
    )
    # 3) user in D1 + project in D2
    conn_a.identity.assign_project_role_to_user(
        domain_b_project.id, domain_a_user.id, domain_b_role.id
    )
    # as conn_b check the assignment
    assert not conn_b.identity.validate_user_has_project_role(
        domain_b_project.id, domain_a_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"assign project-level role to user '{domain_a_user.name}' for "
        f"project '{domain_b_project.name}' of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot assign project-level role to user within "
          "foreign domain: PASS")

    # [D1] domain manager cannot unassign project-level role from user in
    # foreign domain (negative test)
    #
    # first, prepare a valid role assignment in the forein project using conn_b
    conn_b.identity.assign_project_role_to_user(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    )
    assert conn_b.identity.validate_user_has_project_role(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Test setup error: assigning project-level to user "
        f"'{domain_b_user.name}' for project '{domain_b_project.name}' "
        f"as domain manager of domain '{domain_b.name}' failed but is "
        f"required by the testing process; please check "
        f"the test implementation and domain configuration"
    )
    # note that unassign_project_role_from_user() does not raise an exception
    # if it fails; the result has to be checked explicitly
    conn_a.identity.unassign_project_role_from_user(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    )
    assert conn_b.identity.validate_user_has_project_role(
        domain_b_project.id, domain_b_user.id, domain_b_role.id
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"unassign project-level role from user '{domain_b_user.name}' for "
        f"project '{domain_b_project.name}' within foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot unassign project-level role from user within "
          "foreign domain: PASS")

    # [D1] domain manager cannot list projects for a user of foreign domain D2
    #
    # quirk: user_projects() returns a generator and only raises a
    # ForbiddenException once the generator is iterated over the first time,
    # hence calling next() on the return value of user_projects() will trigger
    # the exception, not the user_projects() call itself
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        next,  # the function to be called
        conn_a.identity.user_projects(domain_b_user.id)  # the argument
    ), (
        f"Policy error: domain manager of domain '{domain_a.name}' is able to "
        f"list projects for user '{domain_b_user.name}' of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot list projects for user of foreign domain: "
          "PASS")


def test_groups(cloud_name: str, domains: list[dict]):
    """
    Test correct domain scoping for domain managers relating to the groups
    feature of Keystone.
    """
    print("\nExecuting tests for Keystone groups ...")

    # 1st domain = D1
    domain_a_name = domains[0].get("name")
    conn_a = connect_to_domain(cloud_name, domain_a_name, domains)
    domain_a = conn_a.identity.find_domain(domain_a_name)
    domain_a_user = conn_a.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-user-1",
        domain_id=domain_a.id
    )
    domain_a_project = conn_a.identity.create_project(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-project-1",
        domain_id=domain_a.id
    )
    domain_a_role = conn_a.identity.find_role(domains[0].get("member_role"))

    # 2nd domain = D2
    domain_b_name = domains[1].get("name")
    conn_b = connect_to_domain(cloud_name, domain_b_name, domains)
    domain_b = conn_b.identity.find_domain(domain_b_name)
    domain_b_user = conn_b.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-b-user-1",
        domain_id=domain_b.id
    )

    # [D1] group creation without specifying domain (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_group,
        name=f"{TEST_RESOURCES_PREFIX}group-outside-domain-a"
    ), (
        f"Policy error: domain manager is able to create group without "
        f"specifying domain '{domain_a.name}'"
    )
    print("Domain manager cannot create group without specifying domain: PASS")

    # [D1] group creation in a foreign domain (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_group,
        name=f"{TEST_RESOURCES_PREFIX}group-in-wrong-domain",
        domain_id=domain_b.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to create "
        f"group in foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot create group in foreign domain: PASS")

    # [D1] group creation within domain
    domain_a_group = conn_a.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}group-inside-domain-a",
        domain_id=domain_a.id
    )
    assert domain_a_group, (
        f"Domain manager cannot create groups within domain '{domain_a.name}'"
    )
    print("Domain manager can create group within domain: PASS")

    # [D2] domain manager does not see group of foreign domain D1
    domain_a_groups = conn_b.identity.groups()
    assert next(domain_a_groups, None) is None, (
        f"Policy error: domain manager of '{domain_b.name}' is able to see "
        f"groups of foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot see groups of foreign domain: PASS")

    # [D2] domain manager cannot update group of foreign domain D1
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.update_group,
        domain_a_group.id,
        name=f"{TEST_RESOURCES_PREFIX}group-RENAMED"
    ), (
        f"Policy error: domain manager of '{domain_b.name}' is able to update "
        f"group in foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot update group in foreign domain: PASS")

    # [D2] domain manager cannot delete group of foreign domain D1
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.delete_group,
        domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b.name}' is able to delete "
        f"group in foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot delete group in foreign domain: PASS")

    # [D2] group creation within domain (prerequisite for subsequent tests)
    domain_b_group = conn_b.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}group-inside-domain-b",
        domain_id=domain_b.id
    )
    assert domain_b_group, (
        f"Domain manager cannot create groups within domain '{domain_b.name}'"
    )

    # [D1] domain manager can query group relationship of user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_a_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' cannot use "
        f"check_user_in_group within domain"
    )
    print("Domain manager can use check_user_in_group within domain: PASS")

    # [D1] domain manager cannot query group relationship of user when
    # group or user are in foreign domain D2 (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_b_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to use "
        f"check_user_in_group for user of foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot use check_user_in_group "
          "for user of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_a_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to use "
        f"check_user_in_group for group of foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot use check_user_in_group "
          "for group of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_b_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to use "
        f"check_user_in_group for user and group, both of foreign domain "
        f"'{domain_b.name}'"
    )
    print("Domain manager cannot use check_user_in_group "
          "for user and group of foreign domain: PASS")

    # [D1] domain manager can add user to group within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_a_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager cannot add user to group within domain "
        f"'{domain_a.name}'"
    )
    assert conn_a.identity.check_user_in_group(
        domain_a_user.id, domain_a_group.id
    ), (
        f"User '{domain_a_user.name}' was not successfully added to group "
        f"'{domain_a_group.name}' in domain '{domain_a.name}'"
    )
    print("Domain manager can add user to group within domain: PASS")

    # [D1] domain manager cannot add user to group across domain boundaries
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_a_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to add "
        f"user to group belonging to foreign domain '{domain_b.name}'"
    )
    print("Domain manager cannot add user to group of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_b_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to add "
        f"user belonging to foreign domain '{domain_b.name}' to group"
    )
    print("Domain manager cannot add user of foreign domain to group: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_b_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a.name}' is able to add "
        f"user belonging to foreign domain '{domain_b.name}' to group of foreign "
        f" domain '{domain_b.name}'"
    )
    print("Domain manager cannot add user to group in foreign domain: PASS")

    # [D1] domain manager can list users for group
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.group_users,
        domain_a_group.id
    ), (
        f"Policy error: domain manager cannot list users for group within "
        f"domain '{domain_a.name}'"
    )
    users = list(conn_a.identity.group_users(domain_a_group.id))
    assert len(users) == 1, (
        f"Listing users of group '{domain_a_group.name}' within domain "
        f"'{domain_a.name}' returned wrong amount of users"
    )
    assert users[0].name == domain_a_user.name, (
        f"Listing users of group '{domain_a_group.name}' within domain "
        f"'{domain_a.name}' returned wrong user"
    )
    print("Domain manager can list users for group in domain: PASS")

    # [D1] domain manager cannot assign admin role to groups
    # (do these tests before any other role assignment tests that might succeed
    # because we expect assignment lists to be empty for the negative tests)
    domain_a_project_2 = conn_a.identity.create_project(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-project-2",
        domain_id=domain_a.id
    )
    admin_role = conn_a.identity.find_role("admin")
    assert admin_role is not None, (
        f"Domain Manager of domain '{domain_a.name}' cannot discover the 'admin' "
        f"role (which is used for negative testing)"
    )
    conn_a.identity.assign_project_role_to_group(
        domain_a_project_2.id, domain_a_group.id, admin_role.id
    )
    # the assign_project_role_to_group() does not raise an exception but should
    # not result in an active role assignment for the admin role
    assigns = list(conn_a.identity.role_assignments(
        scope_project_id=domain_a_project_2.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_a.name}' is able to assign 'admin' "
        f"role to group '{domain_a_group.name}' in project "
        f"'{domain_a_project_2.name}'"
    )
    print("Domain manager cannot assign admin role to group on project level: "
          "PASS")
    conn_a.identity.assign_domain_role_to_group(
        domain_a.id, domain_a_group.id, admin_role.id
    )
    # the assign_domain_role_to_group() does not raise an exception but should
    # not result in an active role assignment for the admin role
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_a.name}' is able to assign 'admin' "
        f"role to group '{domain_a_group.name}' in domain"
    )
    print("Domain manager cannot assign admin role to group on domain level in "
          "domain: PASS")

    # [D1] domain manager can assign role to group within domain
    # note that assign_domain_role_to_group() does not raise any exception if
    # it fails; the result must be checked by querying resulting assignments
    conn_a.identity.assign_domain_role_to_group(
        domain_a.id, domain_a_group.id, domain_a_role.id
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a.id,
        group_id=domain_a_group.id,
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"The domain role assignment for role '{domain_a_role.name}', domain "
        f"'{domain_a.name}' and group '{domain_a_group.name}' was not successful"
    )
    print("Domain manager can assign domain-level role to group in domain: "
          "PASS")

    conn_a.identity.assign_project_role_to_group(
        domain_a_project.id, domain_a_group.id, domain_a_role.id
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_project_id=domain_a_project.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"The project role assignment for role '{domain_a_role.name}', "
        f"project '{domain_a_project.name}' and group '{domain_a_group.name}' "
        f"in domain '{domain_a.name}' was not successful"
    )
    print("Domain manager can assign project-level role to group in domain: "
          "PASS")

    # [D2] domain manager cannot unassign project-level role from group in
    # foreign domain
    # note that unassign_project_role_from_group() does not raise exceptions
    # upon request failure, thus the result has to be verified through active
    # role assignment checking
    conn_b.identity.unassign_project_role_from_group(
        domain_a_project.id, domain_a_group.id, domain_a_role
    )
    # use connection for D1 to check that the role assignment was not removed
    assigns = list(conn_a.identity.role_assignments(
        scope_project_id=domain_a_project.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"Policy error: domain manager of domain '{domain_b.name}' is able to "
        f"unassign project-level role from group within foreign domain "
        f"'{domain_a.name}'"
    )
    print("Domain manager cannot unassign project-level role from group in "
          "foreign domain: PASS")

    # [D2] domain manager cannot unassign domain-level role from group in
    # foreign domain
    # note that unassign_domain_role_from_group() does not raise exceptions
    # upon request failure, thus the result has to be verified through active
    # role assignment checking
    conn_b.identity.unassign_domain_role_from_group(
        domain_a.id, domain_a_group.id, domain_a_role
    )
    # use connection for D1 to check that the role assignment was not removed
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"Policy error: domain manager of domain '{domain_b.name}' is able to "
        f"unassign domain-level role from group within foreign domain "
        f"'{domain_a.name}'"
    )
    print("Domain manager cannot unassign domain-level role from group in "
          "foreign domain: PASS")

    # [D1] domain manager can revoke domain-level role from group within domain
    conn_a.identity.unassign_domain_role_from_group(
        domain_a.id, domain_a_group.id, domain_a_role
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot unassign "
        f"domain-level role from group '{domain_a_group.name}' within domain"
    )
    print("Domain manager can unassign domain-level role from group in "
          "domain: PASS")

    # [D1] domain manager can revoke project-level role from group within domain
    conn_a.identity.unassign_project_role_from_group(
        domain_a_project.id, domain_a_group.id, domain_a_role
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_project_id=domain_a_project.id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Policy error: domain manager of domain '{domain_a.name}' cannot unassign "
        f"project-level role from group '{domain_a_group.name}' within domain"
    )
    print("Domain manager can unassign project-level role from group in "
          "domain: PASS")

    # [D2] domain manager cannot query user lists of groups of foreign domains
    users_seen_by_a = list(conn_a.identity.group_users(domain_a_group.id))
    assert len(users_seen_by_a) > 0, (
        f"Test setup error: group '{domain_a_group.name}' of domain "
        f"'{domain_a.name}' should have at least one user assigned, please check "
        f"the test implementation order and domain configuration"
    )
    # quirk: group_users() returns a generator and only raises a
    # ForbiddenException once the generator is iterated over the first time,
    # hence calling next() on the return value of group_users() will trigger
    # the exception, not the group_users() call itself
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        next,  # the function to be called
        conn_b.identity.group_users(domain_a_group.id)  # the argument
    ), (
        f"Policy error: domain manager of '{domain_b.name}' is able to list "
        f"users for group '{domain_a_group.name}' of foreign domain "
        f"'{domain_a.name}'"
    )
    print("Domain manager cannot list users for group in foreign domain: PASS")

    # [D2] domain manager cannot remove user from group in foreign domain
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.remove_user_from_group,
        domain_a_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b.name}' is able to remove "
        f"user '{domain_a_user.name}' from group '{domain_a_group.name}' "
        f"within foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot remove user from group in foreign domain: "
          "PASS")

    # [D2] domain manager cannot delete group in foreign domain
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.delete_group,
        domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b.name}' is able to delete "
        f"group '{domain_a_group.name}' of foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot delete group in foreign domain: PASS")

    # [D2] domain manager cannot assign role to group in foreign domain D1
    #
    # as conn_a create a dedicated group in D1 for this test without any roles
    domain_a_group_2 = conn_a.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}secondary-group-inside-domain-a",
        domain_id=domain_a.id
    )
    # as conn_b attempt to add project-level role
    conn_b.identity.assign_project_role_to_group(
        domain_a_project.id, domain_a_group_2.id, domain_a_role.id
    )
    # as conn_a verify that no role assignment was added
    assigns = list(conn_a.identity.role_assignments(
        scope_project_id=domain_a_project.id,
        group_id=domain_a_group_2.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_b.name}' is able to assign "
        f"project-level role to group '{domain_a_group_2.name}' in project "
        f"'{domain_a_project.name}' of foreign domain '{domain_a.name}'"
    )
    print("Domain manager cannot assign project-level role to group in "
          "foreign domain: PASS")
    # as conn_b attempt to add domain-level role
    conn_b.identity.assign_domain_role_to_group(
        domain_a.id, domain_a_group_2.id, domain_a_role.id
    )
    # as conn_a verify that no role assignment was added
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a.id,
        group_id=domain_a_group_2.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_b.name}' is able to assign "
        f"domain-level role to group '{domain_a_group_2.name}' within foreign "
        f"domain '{domain_a.name}'"
    )
    print("Domain manager cannot assign domain-level role to group in "
          "foreign domain: PASS")

    # [D1] domain manager can delete group within domain
    assert conn_a.identity.find_group(domain_a_group.id), (
        f"Test setup error: group '{domain_a_group.name}' of domain "
        f"'{domain_a.name}' should exist at this point, please check "
        f"the test implementation order and domain configuration"
    )
    conn_a.identity.delete_group(domain_a_group.id)
    assert conn_a.identity.find_group(domain_a_group.id) is None, (
        f"Policy error: domain manager of '{domain_a.name}' cannot successfully "
        f"delete group '{domain_a_group.name}' within domain"
    )
    print("Domain manager can delete group within domain: PASS")


def main():
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
        "--cleanup-only", action="store_true",
        help=f"Instead of executing tests, cleanup all resources within the "
        f"defined domains with the '{TEST_RESOURCES_PREFIX}' prefix"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable OpenStack SDK debug logging"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=args.debug)
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

    if args.cleanup_only:
        cleanup(cloud, domains)
    else:
        test_logins(cloud, domains)
        cleanup(cloud, domains)
        test_users(cloud, domains)
        cleanup(cloud, domains)
        test_projects(cloud, domains)
        cleanup(cloud, domains)
        test_groups(cloud, domains)
        cleanup(cloud, domains)


if __name__ == "__main__":
    main()
