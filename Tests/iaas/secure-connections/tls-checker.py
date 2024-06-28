"""SSL/TLS checker for OpenStack API endpoints

This script retrieves the endpoint catalog from Keystone using the OpenStack
SDK and connects to each to each public endpoint to check its SSL/TLS settings.
The script relies on an OpenStack SDK compatible clouds.yaml file for
authentication with Keystone.

For each endpoint, SSL/TLS protocol parameters supported by the server are
checked using the SSLyze Python library.
The script will fail with a non-zero exit code in case any standard violation
is discovered such as endpoints being non-conformant to the corresponding
Mozilla TLS recommendations.
Details about the conformance issues will be printed for each endpoint to
help with identifying and addressing the violations of the Mozilla TLS preset.
"""

import argparse
import getpass
import json
import os
import sys
import typing

import openstack
import sslyze
from sslyze.mozilla_tls_profile.mozilla_config_checker import (
    SCAN_COMMANDS_NEEDED_BY_MOZILLA_CHECKER, MozillaTlsConfigurationChecker,
    MozillaTlsConfigurationEnum, ServerNotCompliantWithMozillaTlsConfiguration,
    _MozillaTlsProfileAsJson)

# The Mozilla recommendation preset to use
MOZILLA_TLS_PRESET = MozillaTlsConfigurationEnum.INTERMEDIATE


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

    print("\nINFO: the following public endpoints have been retrieved from "
          "the service catalog:")
    for svc_name in ret["public"].keys():
        print(
            f"↳ {svc_name} @ {ret['public'][svc_name]}"
        )

    return ret


def verify_tls(service: str, host: str, port: int,
               mozilla_json_preset: typing.Optional[dict] = None) -> bool:
    """Use SSLyze library to scan the SSL/TLS interface of the server.

    Evaluates the SSL/TLS configurations the server reports as supported.
    Checks the scan results against the Mozilla TLS recommendation preset.
    Prints any issues found with details.

    If `mozilla_json_preset` is passed into this function, it is interpreted
    as the Mozilla TLS Profile JSON to be used. If this argument is None or
    not specified, the default JSON shipped with the respective SSLyze release
    is used instead. The format of this optional argument is expected to be
    the parsed JSON as dict.

    Returns True if no errors were encountered, False otherwise.
    """

    errors_encountered = 0
    server = sslyze.ServerNetworkLocation(host, port)
    scans = SCAN_COMMANDS_NEEDED_BY_MOZILLA_CHECKER
    request = sslyze.ServerScanRequest(server, scan_commands=scans)
    scanner = sslyze.Scanner()
    scanner.queue_scans([request])
    if mozilla_json_preset:
        # Load a specific Mozilla TLS Profile JSON file; this mimicks the
        # internal behavior of MozillaTlsConfigurationChecker.get_default()
        parsed_profile = _MozillaTlsProfileAsJson(**mozilla_json_preset)
        mozilla_checker = MozillaTlsConfigurationChecker(parsed_profile)
    else:
        mozilla_checker = MozillaTlsConfigurationChecker.get_default()
    for result in scanner.get_results():
        assert result.scan_result, (
            f"Service '{service}' at {host}:{port} did not respond to "
            f"TLS connection"
        )
        try:
            mozilla_checker.check_server(MOZILLA_TLS_PRESET, result)
            print(
                f"Service '{service}' at {host}:{port} complies to "
                f"TLS recommendations: PASS"
            )
        except ServerNotCompliantWithMozillaTlsConfiguration as e:
            print(
                f"Service '{service}' at {host}:{port} complies to "
                f"TLS recommendations: FAIL"
            )
            for criteria, error_description in e.issues.items():
                print(f"↳ {criteria}: {error_description}")
            errors_encountered += 1

    return errors_encountered == 0


def check_endpoints(endpoints: dict[str, str],
                    ignore: typing.Optional[str],
                    mozilla_json_preset: typing.Optional[dict]) -> None:
    ignore_list = ignore.split(',') if ignore else []
    error_count = 0
    for service in endpoints:
        url = endpoints[service]
        host_ref = url.split("://", 1)[-1].split("/", 1)[0]

        # Check if the endpoint matches any of the given ignore patterns.
        ignored = False
        for ignore_pattern in ignore_list:
            if ignore_pattern in host_ref:
                print(
                    f"INFO: Matching ignore rule for '{ignore_pattern}', "
                    f"ignoring endpoint: {url}"
                )
                ignored = True
                break
        if ignored:
            continue

        # Default to port 443 if no port is specified
        if ':' in host_ref:
            host, port = host_ref.split(':', 1)
        else:
            host = host_ref
            port = 443

        print(f"INFO: Checking public '{service}' endpoint {host}:{port} ...")
        # Collect errors instead of failing immediately; this makes the output
        # more useful since all endpoints are checked in one run and the
        # printed output will cover all of them, logging all issues at once
        error_count = error_count if verify_tls(
            service, host, int(port), mozilla_json_preset
        ) else error_count + 1

    print(
        f"INFO: Number of endpoints that failed compliance check: "
        f"{error_count} (out of {len(endpoints)})"
    )
    if error_count > 0:
        sys.exit(1)


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
    parser.add_argument(
        "--mozilla-json", type=str,
        help="Path to the Mozilla TLS Profile JSON to be used as the basis "
        "for the checks (optional)",
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
        "No public endpoints found in the service catalog"
    )
    endpoints = endpoints_catalog["public"]

    # load the Mozilla TLS Profile from JSON if specified
    mozilla_json = None
    if args.mozilla_json:
        print(f"INFO: Loading custom Mozilla TLS Profile JSON from "
              f"{args.mozilla_json}")
        with open(args.mozilla_json, 'r') as json_file:
            mozilla_json = json.load(json_file)

    check_endpoints(endpoints, args.ignore, mozilla_json)


if __name__ == "__main__":
    main()
