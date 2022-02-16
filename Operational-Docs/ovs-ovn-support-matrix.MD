

## Neutron traditional OVS vs  Neutron OVN plugin


#### 1. OVN is since OpenStack Ussuri Release the preferential default in OpenStack Clouds

 [ovn-gaps] (https://docs.openstack.org/neutron/latest/ovn/gaps.html)

 list feature's

  | Project |      Feature     | Neutron OVS | Neutron OVN |
  | ------- | ---------------- | ----------- | ----------- |
  | Neutron |      DHCP        |     [x]     |    [x]      |
  | Neutron |  DNS resolve     |     [x]     |    [x]      |
  | Neutron |   "real" DNS     |     [x]     |    [-]      |
  | Neutron |     VPNaaS       |     [x]     |    [?]      |
  | Neutron |      DVR         |     [-]     |    [x]      |
  | Neutron |     FWaaS        |     [?]     |    [-]      |
  | Neutron |      QoS         |     [x]     |    [-]      |
  | Neutron |      BGP         |     [x]     |    [-]      |
  | Neutron |     ipv6         |     [x]     |    [-]      |
  | Octavia |     LBaaS        |     [x]     |    [x]      |
  | Octavia |     LbaaS HA     |     [x]     |    [x]      |
  | Octavia |     LbaaS TLS    |     [x]     |    [-]      |
  | Octavia | LbaaS Dualstack  |     [x]     |    [-]      |
  | Manila  |     NFS          |     [x]     |    [x]      |
