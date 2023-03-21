# Neutron traditional OVS vs Neutron OVN plugin

## 1. OVN is since OpenStack Ussuri Release the preferential default in OpenStack Clouds

Feature Matrix Between Neutron ML2 OVN and OVS

| Project | Feature         | Neutron OVS | Neutron OVN |
| ------- | --------------- | ----------- | ----------- |
| Neutron | DHCP            | [x]         | [x]         |
| Neutron | DNS resolve     | [x]         | [x]         |
| Neutron | forwarded DNS   | [x]         | [-]         |
| Neutron | VPNaaS          | [x]         | [?]         |
| Neutron | DVR             | [x]         | [x]         |
| Neutron | FWaaS           | [?]         | [-]         |
| Neutron | QoS             | [x]         | [-]         |
| Neutron | BGP             | [x]         | [-]         |
| Neutron | delegated ipv6  | [x]         | [-]         |
| Octavia | LBaaS           | [x]         | [x]         |
| Octavia | LbaaS HA        | [x]         | [x]         |
| Octavia | LbaaS TLS       | [x]         | [-]         |
| Octavia | LbaaS Dualstack | [x]         | [-]         |
| Manila  | NFS             | [x]         | [x]         |

[ovn-gaps](https://docs.openstack.org/neutron/latest/ovn/gaps.html)

the missing key features are:

- DNS resolution for instances

that this option currently only works for IPv4 nameservers

- DNS forwarded resolution

With ML2/OVN, there is no dnsmasq instance. In this case, the request is "over-commit" by OVN, and if there is a static record that matches,
it will respond with the static entry. If there is no matching static record, instances without connectivity to the "8.8.8.8" DNS server
that is default in the OVN DHCP packet cannot resolve DNS. This means that these instances cannot utilize DNS records published by Designate.

- BGP support

Neutron-dynamic-routing supports making a tenant subnet routable via BGP,
and can announce host routes for both floating and fixed IP addresses. These functions are not supported in OVN.
which makes native dynamic IPv6 delegation insides OVN based Clouds not possible.

[forwarded DNS resolution](https://bugs.launchpad.net/neutron/+bug/1902950)

[ovs-dvr](https://docs.openstack.org/neutron/latest/admin/deploy-ovs-ha-dvr.html)
