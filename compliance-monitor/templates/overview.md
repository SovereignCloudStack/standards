{#
we could of course iterate over results etc., but hardcode the table (except the actual results, of course)
for the time being to have the highest degree of control
#}
| Name  | Description  | Operator  | SCS-compatible IaaS  | HealthMon  |
| ----- | ------------ | --------- | :------------------: | :--------: |
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/cloud-resources/plusserver-gx-scs.md) | Dev environment provided for SCS & GAIA-X context | plusserver GmbH | {{
    results['gx-scs']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://health.gx-scs.sovereignit.cloud:3000/) |
| [CNDS](https://cnds.io/) | Public cloud for customers | artcodix UG | {{
    results.artcodix['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://ohm.muc.cloud.cnds.io/) |
| [pluscloud open](https://www.plusserver.com/en/products/pluscloud-open)<br />- prod1</br>- prod2<br />- prod3<br />- prod4 | Public cloud for customers (4 regions)   | plusserver GmbH | &nbsp;<br /> | &nbsp;<br />{{
    results['pco-prod1']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}}<br />{{
    results['pco-prod2']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}}<br />{{
    results['pco-prod3']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}}<br />{{
    results['pco-prod4']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | &nbsp;<br /> [HM1](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-pco)<br />[HM2](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod2)<br />[HM3](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod3)<br />[HM4](https://health.prod1.plusserver.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?orgId=1&var-mycloud=plus-prod4) |
| PoC KDO | Cloud PoC for FITKO | KDO Service GmbH / OSISM GmbH | {{
    results['poc-kdo']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} |  (soon) |
| PoC WG-Cloud OSBA | Cloud PoC for FITKO | Cloud&amp;Heat Technologies GmbH | {{
    results['poc-wgcloud']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://health.poc-wgcloud.osba.sovereignit.cloud:3000/d/9ltTEmlnk/openstack-health-monitor2?var-mycloud=poc-wgcloud&orgId=1) |
| [REGIO.cloud](https://regio.digital) | Public cloud for customers | OSISM GmbH | {{
    results['regio-a']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://apimon.services.regio.digital/public-dashboards/17cf094a47404398a5b8e35a4a3968d4?orgId=1&refresh=5m) |
| [Wavestack](https://www.noris.de/wavestack-cloud/) | Public cloud for customers | noris network AG/Wavecon GmbH | {{
    results.wavestack['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://health.wavestack1.sovereignit.cloud:3000/) |
