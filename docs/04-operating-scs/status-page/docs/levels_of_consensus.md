# "Levels of consensus"

When implementing any system to be used by a group of potential users, there will be varying use cases and opinions about API's, programming languages, persistence models, authentication, authorization, deployment options and so on.
Hence, building a complete one-fits-all solution is difficult, but (while offering a pretty un-opinionated reference implementation) even finding consensus on a few basic concepts may make adaptation and integration of different solutions possible.

The "levels" of consensus could be split into:

**Consensus on...**

1. **Resource Definition**
   - "What is an incident?"
   - Core REST API Spec
1. **General Architecture**
   - "Monolithic Web App or multiple components?"
   - "Use static password file or rely on OIDC provider?"
   - (If any:) Interfaces between components:
     - AuthN mechanisms
     - AuthZ decisions
1. **Implementation of core component(s)**
   - "Use reference implementation components?"
   - "Go vs. JavaScript?"
   - "Postgres vs. MySQL?"
1. **Choice of all used components**
   - "Policy: Istio vs. traefik?"
   - "Deployment: Helm vs. ansible?"
   - "dex vs. keycloak vs. zitadel?"

Every user of the Status Page (API) should be able to either make full use of the full reference implementation, building little to none on their own; Or just pick core concepts/API's/automation and build partial compatibility.

E.g. while the value on agreeing on every aspect would bring the most value, this most likely is not likely to happen, but adopting only the "Resource Definition", should ideally bring value already.
