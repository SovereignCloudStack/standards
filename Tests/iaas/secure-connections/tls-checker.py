import openstack

import socket
import ssl


def connect(cloud_name: str) -> openstack.connection.Connection:
    """Create a connection to an OpenStack cloud

    :param string cloud_name:
        The name of the configuration to load from clouds.yaml.

    :returns: openstack.connnection.Connection
    """

    return openstack.connect(
        cloud=cloud_name,
    )


def enumerate_endpoints(conn: openstack.connection.Connection) \
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

    return ret


conn = connect("devstack")
endpoints_catalog = enumerate_endpoints(conn)
assert "public" in endpoints_catalog, (
    "ERR: No public endpoints returned in the service catalog"
)
endpoints = endpoints_catalog["public"]

for service in endpoints:

    url = endpoints[service]
    assert url.startswith("https://"), (
        f"ERR: Public endpoint URL of '{service}' "
        f"does not start with 'https://'"
    )
    url = url.replace("https://", '')
    url = url.replace("http://", '')  # DELETEME, unreachable
    if ':' in url:
        host, appendix = url.split(':', 1)
        port = int(appendix.split('/', 1)[0])
    else:
        host, _ = url.split('/', 1)
        port = 443
    print(host, port)

    context = ssl.create_default_context()

    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssl_socket:
                ssl_version = ssl_socket.version()
                assert ssl_version not in ["TLSv1.0", "TLSv1.1"], (
                    "ERR: Service endpoint for '{service}' uses invalid TLS "
                    "version '{ssl_version}'"
                )

    # TODO: catch all possible SSL exceptions
    except ssl.SSLEOFError as e:
        raise Exception(
            f"ERR: Service '{service}' violated SSL protocol, "
            f"{str(e)}"
        )
