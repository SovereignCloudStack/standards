---
title: Status Page create decision
type: Decision Record
status: Draft
track: Ops
enhances: status-page-comparison.md
---

# Introduction

Creating and maintaining IT infrastructure is a complex task.
Any kind of consumer (e.g. operators, cutsomers) can
be supported by presenting the status of all possible parts of the
serving infrastructure. Whether a service is not reachable or
the used hardware is having an outage we want the consumers to be easily informed
by using a "Status Page" application. The need for a "Status Page"
came up early in the SCS project and the requirements a "Status Page" application
has to fulfill were defined and written down on 2022-06-02 as a 
[MVP-0 epic](https://github.com/SovereignCloudStack/issues/issues/123).
The upcoming research on existing solutions came to the conclusion that we want to
create a new "Status Page" application.

# Existing Applications

Since we want to use as much as possible from existing projects and contribute to
upstream projects to support the community with our efforts, it was a hard
decision to create a new "Status Page" application.

Before the decision was made some existing and known applications were tested
and analyzed if they would fit to our use case. An overview of this
comparsion can be found [here](https://github.com/SovereignCloudStack/Docs/blob/main/Decisions/status-page-comparison.md)
While this is not not a complete list of all existing applications it did
capture the most promising ones from the [awesome-status-page list](https://github.com/ivbeg/awesome-status-pages)
in order to have base to decide upon.

Work on an existing project only makes sense if the project is healthy OR can be
brought into a healthy state. If upstream does not accept patches a fork is needed.
The fork however only makes sense if the underlying technology is worth to be maintained.
The possible candidates did not fullfill these - in the cases where
contribution seemed possible the candidates looked abandoned and long existing CVEs weren't
worked on.

# Decision

Based on the results the decision was made, that the effort is likely to be the same if
we pick up an existing project and try to get it in shape for our use case. It was not
100% clear if this would even be possible or if we still would have to maintain our
own additional patches.

So there will be a reference implementation that will match the requirements we have.
In addition there will be an architecture design documentation. So if the reference
implementation may not fit to you, it will be possible to create your own application.

# Status Page Requirements

* The status page application should be simplistic in software design and should not depend on a large
variety of services
  * simplistic, yet existing user management for write access (oauth? OIDC?)
    * Simple RBAC (role based access control) is nice to have
  * support that components are only visible to a subset of users
    * implies that there is a role that is read-only
    * On-Prem use case might be handled by having an authenticating reverse proxy in front
* The status page applicaton should allow for simple and easy theming
  * Page = (Possibly simple) Web-UI

* As a CSP, I want to have a status page that allows to
  * define locations and similar grouping (AZs, ...)
  * define components globally or per location
    * to ease maintainence I want to define per component where it belongs so that I only have
to define a component once, but have it visible in several locations
    * status per component should be allowed to be toggeable per location or overall
    * a component should allow for several status, that are defined by me

* Status, Status Items should be easy to extract
  * REST(less)-API to interact with
    * API should be versioned
    * this allows for embedding status information in other applications, such as cloud
dashboards
    * this also allows for submitting items from other tooling
      * incoming webhooks (https POST) should be supported (e.g. for air-gapped setups) –
i.e. submitting a health beacon every x seconds
      * web-UI wanted for posting updates as well
        * Token based Auth

* Configuration should be manageable with YAML files (imho this annoys me using Uptime Kuma)

* As a consumer of the status page, I'd like to subscribe to events on the status page via e-mail
  * for everything
  * for specific components

* As a consumer of the status page, I'd like to subscribe to a RSS or atom feed

* Allow for the ability to trigger webhooks upon certain events (to submit info to other systems via
webhooks, e.g. chat/messenger)

* As a CSP Operator, I want to be able to flag a component with a new status quick and easy
  * updating the status of a component should not be hard brainwork and minimize the possibilty
  * updates can be both machine generated status changes (triggered e.g. by health monitoring)
as well as updates from human operators
  * updating a status should allow the CSP Operator to do that in a fashion that either pushes
infos to the subscribers or just updates the status on the status page
  * updating the status can either be toggling the status of the component or can be
accompanied by additional textual information.
  * When updating a status with textual information the status page application should make it
easy for me as the CSP Operator to do in a way that if different people submit infos over time
they are presented in a similar way (eg. the status page application should guide so that the
resulting infos are presented in a identical way. Example: when updating infos of an incident
over time the timeline should automatically be sorted by the status page application so that it
does not depend on the Operator whether the newest info is on top or at the bottom. This is
typical thing that varies if several people update items

* Allow for templates for certain types of incidents

* User-specific monitoring (how are MY instances, load-balancers, ... doing?) is OUT OF SCOPE for
the status page.
  * But having it would be useful and if we have something like this, link it from the status page
(and a link to horizon might be the default)
* Sidenote: External hosting is desired to avoid status page going down with infra

With those requirements in mind the projects that initially were found, were evaluated.

#### Comparison matrix

|                                          | CachetHQ  | ClearStatus | ciao | cState | Gatus | Issue Status | statusfy |
|------------------------------------------|-----------|-------------|------|--------|-------|--------------|----------|
| CSP VIEW                                 |           |             |      |        |       |              |          |
| small dependency tree                    | ❌ Composer | ✅ | ❌ ruby gems | ✅ | ⁇ helm chart | ❌ npm/github/zapier | ❌ npm dependencies very huge |
| easy themable                            | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| grouping (by location...)                | ✅ | ❌ | ❌ | ❌ | ✅ | ⁇ | ✅ |
| components definition ...
| ... local or global                      | ✅ | ❌ | ❌ | ✅ | ⁇ | ✅ | ❌ |
| ... easy flagging with new status        | ✅ | ✅ | ❌ | ✅ | ⁇ | ✅ | ❌ |
| ... push notification on update          | ✅ | ❌ | ✅ | ❌ | ✅ | ⁇ | ✅ |
| ... updates with additional information  | ✅ | ✅ | ❌ | ✅ | ⁇ | ⁇ | ⁇ |
| API Support ...                          | ✅ | ✅ | ✅ | ❌ read only | ❌ | ✅ GitHub API | ❌ | ❌ read only |
| ... versioned                            | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ⁇ |
| ... web ui for posting updates           | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| ... token based auth                     | ✅ | ✅ Auth managed by git provider | ❌ only basic auth | ❌ | ❌ BUT OIDC! | ✅ | ❌ |
| manageable configuration                 | ❌ config depends on web server and initial install relies on env variables | ❌ based on hugo CMS | ❌ config by env variables | ❌ based on hugo CMS | ✅ | ❌ | ❌ no real config needed |
| templating support                       | ✅ twig | ❌ Hugo itself uses GO template libraries | ❌ | ❌ | ❌ | ❌ | ❌ |
| CUSTOMER VIEW                            |   |   |   |   |   |   |
| subscription support ...                 | ✅ | ❌ only by git provider | ✅ | ❌ | ❌ | ✅ | ✅ |
| ... send by eMail                        | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| watchdog for status page support         | ⁇ | ⁇ | ✅ | ❌ | ✅ | ⁇ | ❌ |
| trigger webhook support                  | ❌ needs cachet-monitor | ⁇ | ✅ | ⁇ | ✅ | ⁇ | ❌ |
| additional infos                         | - | basically a theme for hugo cms, depends on netlify cms | - | basically a theme for hugo cms, depends on netlify cms | - | It's highly optimized for github pages  | SPA created with netlify |
| hidden components                        | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| user management                          | ✅ | ❌ | ❌ | ❌ | ✅ by OIDC | ⁇ through github? | ❌ |
| different output format on notification  | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| external hosting                         | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ looks like you are limited to github | ✅ |
| project healthy                          | ❌ last commit 17 months | ❌ last commit 3 years | ❌ last commit 5 months | ✅ last commit 2 months | ✅ recent activities | ✅ recent activities | ❌ archived and abondend by the owner |
| documentation                            | ✅ API ❌ User Documentation | ❌ | ❌ | ❌ | ✅ | ⁇u | ❌ not reachable anymore |
| git based                                | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ⁇ a netlify based installation is able to communicate with github |
| project page                             | https://cachethq.io/ | https://github.com/weeblrpress/clearstatus | https://www.brotandgames.com/ciao/ | https://cstate.netlify.app/ | https://gatus.io/ | https://github.com/tadhglewis/issue-status | https://marquez.co/statusfy |

# Related Documents

[Status Page comparison](https://github.com/SovereignCloudStack/Docs/blob/main/Decisions/status-page-comparison.md)

[Architecture design documentation](https://github.com/joshmue/scs-docs/tree/statuspage-design/Design-Docs/statuspage)

