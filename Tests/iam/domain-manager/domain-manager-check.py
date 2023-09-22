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
    Uses the configured domain manager users to cleanup any Keystone resources
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


def _raisesException(exception, func, *args, **kwargs):
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
    # TODO:
    # - domain manager can create user in domain
    # - domain manager can find user in domain
    # - domain manager can update user in domain
    # - domain manager can delete user in domain
    # - domain manager can assign domain-level role to user
    # - domain manager cannot create user in foreign domain
    # - domain manager cannot find user in foreign domain
    # - domain manager cannot update user in foreign domain
    # - domain manager cannot delete user in foreign domain
    # - domain manager cannot assign domain-level role to user in foreign domain


def test_projects(cloud_name: str, domains: list[dict]):
    """
    Test correct domain scoping for domain managers relating to the projects
    feature of Keystone.
    """
    # TODO:
    # - domain manager can create project in domain
    # - domain manager can find project in domain
    # - domain manager can update project in domain
    # - domain manager can delete project in domain
    # - domain manager can assign project-level role to user for project within domain
    # - domain manager can list projects of users in domain (user_projects())
    # - domain manager cannot create project in foreign domain
    # - domain manager cannot find project in foreign domain
    # - domain manager cannot update project in foreign domain
    # - domain manager cannot delete project in foreign domain
    # - domain manager cannot assign project-level role to user for project within foreign domain
    #   - as D1: user_a + project_b, user_b + project_a, user_b + project_b
    # - domain manager cannot list projects of users in foreign domain (user_projects())


def test_groups(cloud_name: str, domains: list[dict]):
    """
    Test correct domain scoping for domain managers relating to the groups
    feature of Keystone.
    """

    # 1st domain = D1
    domain_a = domains[0].get("name")
    conn_a = connect_to_domain(cloud_name, domain_a, domains)
    domain_a_id = conn_a.identity.find_domain(domain_a).id
    domain_a_user = conn_a.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-user-1",
        domain_id=domain_a_id
    )
    domain_a_project = conn_a.identity.create_project(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-project-1",
        domain_id=domain_a_id
    )
    domain_a_role = conn_a.identity.find_role(domains[0].get("member_role"))

    # 2nd domain = D2
    domain_b = domains[1].get("name")
    conn_b = connect_to_domain(cloud_name, domain_b, domains)
    domain_b_id = conn_b.identity.find_domain(domain_b).id
    domain_b_user = conn_b.identity.create_user(
        name=f"{TEST_RESOURCES_PREFIX}domain-b-user-1",
        domain_id=domain_b_id
    )

    # [D1] group creation without specifying domain (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_group,
        name=f"{TEST_RESOURCES_PREFIX}group-outside-domain-a"
    ), (
        f"Policy error: domain manager can create group without "
        f"specifying domain '{domain_a}'"
    )
    print("Domain manager cannot create group without specifying domain: PASS")

    # [D1] group creation in a foreign domain (negative test)
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.create_group,
        name=f"{TEST_RESOURCES_PREFIX}group-in-wrong-domain",
        domain_id=domain_b_id
    ), (
        f"Policy error: domain manager of '{domain_a}' can create group "
        f"in foreign domain '{domain_b}'"
    )
    print("Domain manager cannot create group in foreign domain: PASS")

    # [D1] group creation within domain
    domain_a_group = conn_a.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}group-inside-domain-a",
        domain_id=domain_a_id
    )
    assert domain_a_group, (
        f"Domain manager cannot create groups within domain '{domain_a}'"
    )
    print("Domain manager can create group within domain: PASS")

    # [D2] domain manager does not see group of foreign domain D1
    domain_a_groups = conn_b.identity.groups()
    assert next(domain_a_groups, None) is None, (
        f"Policy error: domain manager of '{domain_b}' can see groups of "
        f"domain '{domain_a}'"
    )
    print("Domain manager cannot see groups of foreign domain: PASS")

    # [D2] domain manager cannot update group of foreign domain D1
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.update_group,
        domain_a_group.id,
        name=f"{TEST_RESOURCES_PREFIX}group-RENAMED"
    ), (
        f"Policy error: domain manager of '{domain_b}' can update group in "
        f"foreign domain '{domain_a}'"
    )
    print("Domain manager cannot update group in foreign domain: PASS")

    # [D2] domain manager cannot delete group of foreign domain D1
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.delete_group,
        domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b}' can delete group in "
        f"foreign domain '{domain_a}'"
    )
    print("Domain manager cannot delete group in foreign domain: PASS")

    # [D2] group creation within domain (prerequisite for subsequent tests)
    domain_b_group = conn_b.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}group-inside-domain-b",
        domain_id=domain_b_id
    )
    assert domain_b_group, (
        f"Domain manager cannot create groups within domain '{domain_b}'"
    )

    # [D1] domain manager can query group relationship of user within domain
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_a_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' cannot use "
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
        f"Policy error: domain manager of '{domain_a}' can use "
        f"check_user_in_group for user of foreign domain '{domain_b}'"
    )
    print("Domain manager cannot use check_user_in_group "
          "for user of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_a_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' can use "
        f"check_user_in_group for group of foreign domain '{domain_b}'"
    )
    print("Domain manager cannot use check_user_in_group "
          "for group of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.check_user_in_group,
        domain_b_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' can use "
        f"check_user_in_group for user and group, both of foreign domain "
        f"'{domain_b}'"
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
        f"'{domain_a}'"
    )
    assert conn_a.identity.check_user_in_group(
        domain_a_user.id, domain_a_group.id
    ), (
        f"User '{domain_a_user.name}' was not successfully added to group "
        f"'{domain_a_group.name}' in domain '{domain_a}'"
    )
    print("Domain manager can add user to group within domain: PASS")

    # [D1] domain manager cannot add user to group across domain boundaries
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_a_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' can add "
        f"user to group belonging to foreign domain '{domain_b}'"
    )
    print("Domain manager cannot add user to group of foreign domain: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_b_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' can add "
        f"user belonging to foreign domain '{domain_b}' to group"
    )
    print("Domain manager cannot add user of foreign domain to group: PASS")
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.add_user_to_group,
        domain_b_user.id, domain_b_group.id
    ), (
        f"Policy error: domain manager of '{domain_a}' can add "
        f"user belonging to foreign domain '{domain_b}' to group of foreign "
        f" domain '{domain_b}'"
    )
    print("Domain manager cannot add user to group in foreign domain: PASS")

    # [D1] domain manager can list users for group
    assert not _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_a.identity.group_users,
        domain_a_group.id
    ), (
        f"Policy error: domain manager cannot list users for group within "
        f"domain '{domain_a}'"
    )
    users = list(conn_a.identity.group_users(domain_a_group.id))
    assert len(users) == 1, (
        f"Listing users of group '{domain_a_group.name}' within domain "
        f"'{domain_a}' returned wrong amount of users"
    )
    assert users[0].name == domain_a_user.name, (
        f"Listing users of group '{domain_a_group.name}' within domain "
        f"'{domain_a}' returned wrong user"
    )
    print("Domain manager can list users for group in domain: PASS")

    # [D1] domain manager cannot assign admin role to groups
    # (do these tests before any other role assignment tests that might succeed
    # because we expect assignment lists to be empty for the negative tests)
    domain_a_project_2 = conn_a.identity.create_project(
        name=f"{TEST_RESOURCES_PREFIX}domain-a-project-2",
        domain_id=domain_a_id
    )
    admin_role = conn_a.identity.find_role("admin")
    assert admin_role is not None, (
        f"Domain Manager of domain '{domain_a}' cannot discover the 'admin' "
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
        f"Domain Manager of domain '{domain_a}' is able to assign 'admin' "
        f"role to group '{domain_a_group.name}' in project "
        f"'{domain_a_project_2.name}'"
    )
    print("Domain manager cannot assign admin role to group on project level: "
          "PASS")
    conn_a.identity.assign_domain_role_to_group(
        domain_a_id, domain_a_group.id, admin_role.id
    )
    # the assign_domain_role_to_group() does not raise an exception but should
    # not result in an active role assignment for the admin role
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a_id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_a}' is able to assign 'admin' "
        f"role to group '{domain_a_group.name}' in domain"
    )
    print("Domain manager cannot assign admin role to group on domain level in "
          "domain: PASS")

    # [D1] domain manager can assign role to group within domain
    # note that assign_domain_role_to_group() does not raise any exception if
    # it fails; the result must be checked by querying resulting assignments
    conn_a.identity.assign_domain_role_to_group(
        domain_a_id, domain_a_group.id, domain_a_role.id
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a_id,
        group_id=domain_a_group.id,
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"The domain role assignment for role '{domain_a_role.name}', domain "
        f"'{domain_a}' and group '{domain_a_group.name}' was not successful"
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
        f"in domain '{domain_a}' was not successful"
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
        f"Policy error: domain manager of domain '{domain_b}' can unassign "
        f"project-level role from group within foreign domain '{domain_a}'"
    )
    print("Domain manager cannot unassign project-level role from group in "
          "foreign domain: PASS")

    # [D2] domain manager cannot unassign domain-level role from group in
    # foreign domain
    # note that unassign_domain_role_from_group() does not raise exceptions
    # upon request failure, thus the result has to be verified through active
    # role assignment checking
    conn_b.identity.unassign_domain_role_from_group(
        domain_a_id, domain_a_group.id, domain_a_role
    )
    # use connection for D1 to check that the role assignment was not removed
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a_id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 1 and assigns[0].role["id"] == domain_a_role.id, (
        f"Policy error: domain manager of domain '{domain_b}' can unassign "
        f"domain-level role from group within foreign domain '{domain_a}'"
    )
    print("Domain manager cannot unassign domain-level role from group in "
          "foreign domain: PASS")

    # [D1] domain manager can revoke domain-level role from group within domain
    conn_a.identity.unassign_domain_role_from_group(
        domain_a_id, domain_a_group.id, domain_a_role
    )
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a_id,
        group_id=domain_a_group.id
    ))
    assert len(assigns) == 0, (
        f"Policy error: domain manager of domain '{domain_a}' cannot unassign "
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
        f"Policy error: domain manager of domain '{domain_a}' cannot unassign "
        f"project-level role from group '{domain_a_group.name}' within domain"
    )
    print("Domain manager can unassign project-level role from group in "
          "domain: PASS")

    # [D2] domain manager cannot query user lists of groups of foreign domains
    users_seen_by_a = list(conn_a.identity.group_users(domain_a_group.id))
    assert len(users_seen_by_a) > 0, (
        f"Test setup error: group '{domain_a_group.name}' of domain "
        f"'{domain_a}' should have at least one user assigned, please check "
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
        f"Policy error: domain manager of '{domain_b}' can list "
        f"users for group '{domain_a_group.name}' of foreign domain "
        f"'{domain_a}'"
    )
    print("Domain manager cannot list users for group in foreign domain: PASS")

    # [D2] domain manager cannot remove user from group in foreign domain
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.remove_user_from_group,
        domain_a_user.id, domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b}' can remove "
        f"user '{domain_a_user.name}' from group '{domain_a_group.name}' "
        f"within foreign domain '{domain_a}'"
    )
    print("Domain manager cannot remove user from group in foreign domain: "
          "PASS")

    # [D2] domain manager cannot delete group in foreign domain
    assert _raisesException(
        openstack.exceptions.ForbiddenException,
        conn_b.identity.delete_group,
        domain_a_group.id
    ), (
        f"Policy error: domain manager of '{domain_b}' can delete "
        f"group '{domain_a_group.name}' of foreign domain '{domain_a}'"
    )
    print("Domain manager cannot delete group in foreign domain: PASS")

    # [D2] domain manager cannot assign role to group in foreign domain D1
    #
    # as conn_a create a dedicated group in D1 for this test without any roles
    domain_a_group_2 = conn_a.identity.create_group(
        name=f"{TEST_RESOURCES_PREFIX}secondary-group-inside-domain-a",
        domain_id=domain_a_id
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
        f"Domain Manager of domain '{domain_b}' is able to assign "
        f"project-level role to group '{domain_a_group_2.name}' in project "
        f"'{domain_a_project.name}' of foreign domain '{domain_a}'"
    )
    print("Domain manager cannot assign project-level role to group in "
          "foreign domain: PASS")
    # as conn_b attempt to add domain-level role
    conn_b.identity.assign_domain_role_to_group(
        domain_a_id, domain_a_group_2.id, domain_a_role.id
    )
    # as conn_a verify that no role assignment was added
    assigns = list(conn_a.identity.role_assignments(
        scope_domain_id=domain_a_id,
        group_id=domain_a_group_2.id
    ))
    assert len(assigns) == 0, (
        f"Domain Manager of domain '{domain_b}' is able to assign "
        f"domain-level role to group '{domain_a_group_2.name}' within foreign "
        f"domain '{domain_a}'"
    )
    print("Domain manager cannot assign domain-level role to group in "
          "foreign domain: PASS")

    # [D1] domain manager can delete group within domain
    assert conn_a.identity.find_group(domain_a_group.id), (
        f"Test setup error: group '{domain_a_group.name}' of domain "
        f"'{domain_a}' should exist at this point, please check "
        f"the test implementation order and domain configuration"
    )
    conn_a.identity.delete_group(domain_a_group.id)
    assert conn_a.identity.find_group(domain_a_group.id) is None, (
        f"Policy error: domain manager of '{domain_a}' cannot successfully "
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
        "--cleanup", action="store_true",
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

    if args.cleanup:
        cleanup(cloud, domains)
    else:
        test_logins(cloud, domains)
        test_groups(cloud, domains)


if __name__ == "__main__":
    main()
