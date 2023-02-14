---
title: LoadBalancer As Service
type: Architecture Decision Record
status: Draft
track: _Global | IaaS | Ops | KaaS
---

## 1. The Loadbalancer User story

The Terminology of Loadbalancing is a bundle of different types of
Loadbalancing, which is explained in the Section 2.

From an operator perspective it is today possible to use LBaaS,
the SCS Stack shipped Octavia as LBaaS. but there are some open
questions. For some application use cases, audit trail or geolocating
protection it is helpful to be able to get origin source ip
in.

## 2. Terms of Loadbalancing

### 2.1 Definition of typical loadbalancer parts

![Loadbalancer Overview](LoadbalancerShema1.png)

### 2.1.1 Listener

A listener or a virtual server is a Socket, an interface or an
ip address with a port definition to accept traffic.

### 2.1.2 Backend

A backend or a pool is a collective of member servers.
The listener represents the client-side and the backend the
server side.

### 2.1.3 Member server

A member server or real server is by definition an ip and
a port, which represents a real, virtual instance or container.
It could be a local socket too.

### 2.1.4 Monitor

A monitor in loadbalancers scope means this a healtscheck which is
proof the service of the responsibility of each member server.

### 2.2  Types of Loadbalancing

### 2.2.1  DNS Based Loadbalancing

DNS Based Loadbalancing means to resolve a DNS name to more than to one A
or AAAA Record. The client will likely cache this entry. if is answer is fault,
it will to next.

```console
www.example.org       A         1.2.3.4
www.example.org       A         4.3.2.1
```

But DNS servers do not know the backend state, as such DNS-based loadbalancing
is a very simplistic way of loadbalancing.

### 2.2.2 Reverse Proxy Loadbalancing

![Loadbalancer proxy](reverse-proxy.png)

Reverse proxy is a form of loadbalancing, which terminates connections
and recreates a new client-server connection form the listener to 
its own backend. For HTTP this solution is working in a good manner,
the HTTP Protocol contains mechanisms, which are able to forward origin ip
and origin port forwarding. This is specified in [RFC7239](https://www.rfc-editor.org/rfc/rfc7239.html).

For the TCP connection it is a workaround with flaw. TCP itself has no
mechanism to forwarded the origin source ip. TLS Termination works
even to for HTTP and TCP.

the expected performance footprint is minimal.

examples for this are:

* [haproxy.org](https://haproxy.org)
* [nginx.org](https://nginx.org)
* [traefik.io](https://traefik.io/)

### 2.2.3  Direct Routing (NAT Based) Loadbalancing

![Loadbalancer Nat](natbased.png)

Direct Routing or Network Address Translation Loadbalancing,
is a form of Loadbalancing provided, where loadbalancing 
component works directly on a network gateway. This network
gateway is present to the member server as the default gateway.

The NAT provided origin source ip packages which is a way to balance
L3 Traffic. There is no header modification needed protocol.

TLS Termination for TCP should handle by backend application directly.

Another benefit is use a masquerade ip network cidr to connect from
server to client network to use multiple nat addresses to public
internet.

the expected performance footprint is medium, so for software defined
it could be a bottleneck.

example for this are:

* Linux Virtual Server (IPVS) kernel module
 - which is adapted by [keepalived](https://github.com/acassen/keepalived)

### 2.2.4  Direct Server Return Loadbalancing

![DSR](dsr.png)

Direct Server Return is from the architecture layer beside of the 
gateway as own instance and is from the definition a "flat based" 
form of loadbalancing. In the Direction of Trafficflow, from the
public origin source ip to listener. From Listener as client side,
rewrite the client side ip with the origin source ip to the server side,
the responsive member response to origin source ip.

### 2.2.5  ECMP Loadbalancing

For this form of Loadbalancing, it will use the function of Routers to 
forwarding traffic. In Wide Area Network there is often the possibility
to have multiple datapathes to the dedicate network hops. The idea 
behind is to have network redundancy, where are some of this datapathes
are standby. it is handled by routing protocols to it own metrics or 
"costs" where datapathes take place. With ECMP or in long form 
Equal Path Multi Path will realized by insert the route in forward 
table of a router  to use the same "costs" to a single destination hop. 
This means you will have an addition form of scheduling  mechanism 
to manipulate the chosen route. ECMP is expressed in [RFC2992](https://www.rfc-editor.org/rfc/rfc2992)
the most chosen routing protocol is BGP with Support for scaling
virtual services.

there two forms of Loadbalancing

Round robin which is known under packet based Loadbalancing

session loadbalancing which will decided with every new session,
with routes the flow by the first session decision, with schedulers
round robin, hashed or least recently using.

## 2.3.  LBaaS in SCS Clouds

With OpenStack octavia as project is shipped as Loadbalancer as
Service in SCS stacks. It works in two scenarios. 

### 2.3.1 Amphora Provider

![amphora](Amphora-diagram.png)

The amphora provider with ha-instances of amphora's Amphora works in
typical OpenStack Projects as instance as single or as HA-Pair.
An amphora is instance with interface for management  by octavia
control plane and an amphora-namespace to handle the loadbalancing and
the HA-VIP things itself. In the amphora-namespace itself work haproxy
as reverse-proxy for http, tcp and TLS termination + keepalived as VRRP
and ipvsadm for UDP.

### 2.3.2 OVN Provider
  
the Second Provider in Octavia work with the SDN integration
Open Virtual Network. The Design it much easier from the architecture
perspective. the listener is just another router port in the
OpenStack Project Router. Logical it works as DSR based Loadbalancing,
which controlled by the Openflow definition of OVN.

OVN in a small showcase

```console
  openstack loadbalancer create --provider ovn --vip-subnet-id=subnet-test
  openstack loadbalancer set --name lb1 13f4ff79-0e58-4bf2-8ad6-c2dc0e1d15a3

  openstack loadbalancer pool create --name p1 --loadbalancer lb1 --protocol TCP --lb-algorithm SOURCE_IP_PORT

  openstack loadbalancer member create --address 192.168.112.122 --subnet-id 6816715b-53db-4322-a56a-31b5c537c1b8 --protocol-port 22 p1

  openstack loadbalancer listener create --name l1 --protocol TCP  --protocol-port 2222 --default-pool p1 lb1
```
