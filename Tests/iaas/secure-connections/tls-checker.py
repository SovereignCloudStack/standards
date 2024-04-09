"""SSL/TLS checker for OpenStack API endpoints

This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and connects to each to each public endpoint to check its SSL/TLS settings.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.

For each endpoint, SSL/TLS protocol versions and ciphers supported by the
server are checked using the SSLyze Python library.
The script will fail with a non-zero exit code in case any standard violation
is discovered such as deprecated/insecure TLS versions or weak ciphers as
determined by the standard.

For guidelines marked as OPTIONAL, SHOULD or SHOULD NOT in the standard,
appropriate warnings are printed in the log output for each endpoint.
"""

import argparse
import getpass
import os
import typing

import openstack
import sslyze


def connect(cloud_name: str, password: typing.Optional[str] = None
            ) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :param string password:
        Optional password override for the connection.

    :returns: openstack.connnection.Connection
    """

    if password:
        return openstack.connect(
            cloud=cloud_name,
            password=password
        )
    else:
        return openstack.connect(
            cloud=cloud_name,
        )


def retrieve_endpoints(conn: openstack.connection.Connection) \
        -> dict[str, dict[str, str]]:
    """Enumerate all endpoints of the service catalog returned by the
    current connection categorized by interface type and service.

    Resulting structure:
    {
        <interface-type>: {
            <service-name>: <endpoint-url>
        }
    }

    where <interface-type> is public, internal or admin.
    """

    ret = {}

    for svc in conn.service_catalog:
        svc_name = svc['name']
        for endpoint in svc.get('endpoints'):
            enp_type = endpoint['interface']
            enp_url = endpoint['url']
            subdict = ret.setdefault(enp_type, {})
            subdict[svc_name] = enp_url

    print(f"\nINFO: the following public endpoints have been retrieved from "
          f"the service catalog:")
    for svc_name in ret["public"].keys():
        print(
            f"↳ {svc_name} @ {ret['public'][svc_name]}"
        )

    return ret


def verify_tls(service: str, host: str, port: int) -> None:
    """Use SSLyze library to scan the SSL/TLS interface of the server.

    Evaluates the SSL/TLS versions the server reports to support as well as
    the cipher suites it accepts.
    Checks the protocol versions and cipher suites against the rules
    established by the standard to assure conformance.
    """

    # The following are sslyze.ServerScanResult.scan_result class attrs
    # mapped to a boolean value that indicates whether the SSL/TLS version
    # is permitted (True) or deprecated/insecure/disallowed (False).
    # In case of the latter, the server is expectedf *not* to offer this
    # protocol version at all.
    cipher_suite_categories = {
        "ssl_2_0_cipher_suites": False,
        "ssl_3_0_cipher_suites": False,
        "tls_1_0_cipher_suites": False,
        "tls_1_1_cipher_suites": False,
        "tls_1_2_cipher_suites": True,
        "tls_1_3_cipher_suites": True,
    }

    # The following string patterns will be matched against to identify
    # algorithms, modes or key lengths which are considered insecure by
    # the standard and will throw errors if found.
    # Note: for an exhaustive list of available ciphers, see
    # https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
    insecure_cipher_patterns = {
        "RC4",  # RC4 encryption
        "MD5",  # MD5 hashing
        "DES",  # DES encryption
        "_56",  # algorithms with 56-bit keys
        "_64",  # algorithms with 64-bit keys
    }

    server = sslyze.ServerNetworkLocation(host, port)
    scans = {
        sslyze.ScanCommand.SSL_2_0_CIPHER_SUITES,
        sslyze.ScanCommand.SSL_3_0_CIPHER_SUITES,
        sslyze.ScanCommand.TLS_1_0_CIPHER_SUITES,
        sslyze.ScanCommand.TLS_1_1_CIPHER_SUITES,
        sslyze.ScanCommand.TLS_1_2_CIPHER_SUITES,
        sslyze.ScanCommand.TLS_1_3_CIPHER_SUITES
    }
    req = sslyze.ServerScanRequest(server, scan_commands=scans)
    scanner = sslyze.Scanner()
    scanner.queue_scans([req])
    for result in scanner.get_results():
        assert result.scan_result, (
            f"Service '{service}' at {host}:{port} did not respond to "
            f"TLS connection"
        )
        for suite_cat in cipher_suite_categories.keys():
            protocol = suite_cat.replace("_cipher_suites", "")
            attempt = getattr(result.scan_result, suite_cat)
            assert (
                attempt.status == sslyze.ScanCommandAttemptStatusEnum.COMPLETED
            ), (
                f"'{service}' at {host}:{port} failed to respond to "
                f"{protocol} scan"
            )

            # If the cipher suite was marked as disallowed, assert that the
            # server does not accept it.
            server_cipher_suites = attempt.result.accepted_cipher_suites
            if not cipher_suite_categories[suite_cat]:
                assert (
                    len(server_cipher_suites) == 0
                ), (
                    f"'{service}' at {host}:{port} accepts cipher "
                    f"suites for prohibited SSL/TLS version: {protocol}"
                )
                print(
                    f"↳ Checking denial of deprecated or insecure "
                    f"protocol version {protocol}: PASS")
            else:
                # else inspect the cipher suites that the server is claiming
                # to accept for cipher suites prohibited by the standard
                for suite in server_cipher_suites:
                    name = suite.cipher_suite.name
                    for pat in insecure_cipher_patterns:
                        assert pat not in str(name), (
                            f"'{service}' at {host}:{port} accepts "
                            f"insecure cipher suite including the algorithm, "
                            f"mode or key length '{pat}' for "
                            f"{protocol}: {name}"
                        )

                    # Check some OPTIONAL guidelines of the standard and print
                    # a warning if any is found.
                    if "CBC" in name:
                        print(
                            f"↳ WARN: Server accepts cipher in 'CBC' mode, "
                            f"which SHOULD NOT be used: {name}"
                        )
                    if "_DH" in name and "_DHE" not in name:
                        print(
                            f"↳ WARN: Server accepts cipher with 'DH' "
                            f"algorithm but 'DHE' SHOULD be used: {name}"
                        )
                    if "_ECDH" in name and "_ECDHE" not in name:
                        print(
                            f"↳ WARN: Server accepts cipher with 'ECDH' "
                            f"algorithm but 'ECDHE' SHOULD be used: {name}"
                        )
                print(
                    f"↳ Checking denial of weak or deprecated ciphers "
                    f"on protocol version {protocol}: PASS"
                )


def check_endpoints(endpoints: dict[str, str],
                    ignore: typing.Optional[str]) -> None:
    ignore_list = ignore.split(',') if ignore else []
    for service in endpoints:
        url = endpoints[service]
        host_ref = url.split("://", 1)[-1].split("/", 1)[0]

        # Check if the endpoint matches any of the given ignore patterns.
        ignored = False
        for ignore_pattern in ignore_list:
            if ignore_pattern in host_ref:
                print(
                    f"WARN: matching ignore rule for '{ignore_pattern}', "
                    f"ignoring endpoint: {url}"
                )
                ignored = True
                break
        if ignored:
            continue

        if ':' in host_ref:
            host, port = host_ref.split(':', 1)
        else:
            host = host_ref
            port = 443

        print(f"\nINFO: Checking public endpoint {host}:{port} ...")
        verify_tls(service, host, int(port))


def main():
    parser = argparse.ArgumentParser(
        description="SCS Domain Manager Conformance Checker")
    parser.add_argument(
        "--os-cloud", type=str,
        help="Name of the cloud from clouds.yaml, alternative "
        "to the OS_CLOUD environment variable"
    )
    parser.add_argument(
        "--ask",
        help="Ask for password interactively instead of reading it from the "
        "clouds.yaml",
        action="store_true"
    )
    parser.add_argument(
        "--ignore", type=str,
        help="Comma-separated list of host names or host:port combinations "
        "to exclude from testing",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable OpenStack SDK debug logging"
    )
    args = parser.parse_args()
    openstack.enable_logging(debug=args.debug)

    # parse cloud name for lookup in clouds.yaml
    cloud = os.environ.get("OS_CLOUD", None)
    if args.os_cloud:
        cloud = args.os_cloud
    assert cloud, (
        "You need to have the OS_CLOUD environment variable set to your "
        "cloud name or pass it via --os-cloud"
    )
    conn = connect(
        cloud,
        password=getpass.getpass("Enter password: ") if args.ask else None
    )
    endpoints_catalog = retrieve_endpoints(conn)
    assert "public" in endpoints_catalog, (
        "No public endpoints returned in the service catalog"
    )
    endpoints = endpoints_catalog["public"]
    check_endpoints(endpoints, args.ignore)


if __name__ == "__main__":
    main()
