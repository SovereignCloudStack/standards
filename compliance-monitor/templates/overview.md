{#
we could of course iterate over results etc., but hardcode the table (except the actual results, of course)
for the time being to have the highest degree of control
#}
| Name  | Description  | Operator  | SCS-compatible IaaS  | HealthMon  |
| ----- | ------------ | --------- | :------------------: | :--------: |
| [gx-scs](https://github.com/SovereignCloudStack/docs/blob/main/community/cloud-resources/plusserver-gx-scs.md) | Dev environment provided for SCS & GAIA-X context | plusserver GmbH | {{
    results.gxscs['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://health.gx-scs.sovereignit.cloud:3000/) |
| [REGIO.cloud](https://regio.digital) | Public cloud for customers | OSISM GmbH | {{
    results['regio-a']['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://apimon.services.regio.digital/public-dashboards/17cf094a47404398a5b8e35a4a3968d4?orgId=1&refresh=5m) |
| [Wavestack](https://www.noris.de/wavestack-cloud/) | Public cloud for customers | noris network AG/Wavecon GmbH | {{
    results.wavestack['50393e6f-2ae1-4c5c-a62c-3b75f2abef3f'] | passed or '–'
}} | [HM](https://health.wavestack1.sovereignit.cloud:3000/) |
