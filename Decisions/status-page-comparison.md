# Status Page Comparison

|                           | CachetHQ    | ClearStatus | ciao         | cState | Gatus        | Issue Status         | statusfy                      |
| ------------------------- | ----------- | ----------- | ------------ | ------ | ------------ | -------------------- | ----------------------------- |
| CSP VIEW                  |             |             |              |        |              |                      |                               |
| small dependency tree     | ❌ Composer | ✅          | ❌ ruby gems | ✅     | ⁇ helm chart | ❌ npm/github/zapier | ❌ npm dependencies very huge |
| easy themable             | ✅          | ❌          | ❌           | ❌     | ❌           | ❌                   | ✅                            |
| grouping (by location...) | ✅          | ❌          | ❌           | ❌     | ✅           | ⁇                    | ✅                            |

| components definition ...
| ... local or global | ✅ | ❌ | ❌ | ✅ | ⁇ | ✅ | ❌ |
| ... easy flagging with new status | ✅ | ✅ | ❌ | ✅ | ⁇ | ✅ | ❌ |
| ... push notification on update | ✅ | ❌ | ✅ | ❌ | ✅ | ⁇ | ✅ |
| ... updates with additional information | ✅ | ✅ | ❌ | ✅ | ⁇ | ⁇ | ⁇ |
| API Support ... | ✅ | ✅ | ✅ | ❌ read only | ❌ | ✅ GitHub API | ❌ | ❌ read only |
| ... versioned | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ⁇ |
| ... web ui for posting updates | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| ... token based auth | ✅ | ✅ Auth managed by git provider | ❌ only basic auth | ❌ | ❌ BUT OIDC! | ✅ | ❌ |
| manageable configuration | ❌ config depends on web server and initial install relies on env variables | ❌ based on hugo CMS | ❌ config by env variables | ❌ based on hugo CMS | ✅ | ❌ | ❌ no real config needed |
| templating support | ✅ twig | ❌ Hugo itself uses GO template libraries | ❌ | ❌ | ❌ | ❌ | ❌ |
| CUSTOMER VIEW | | | | | | |
| subscription support ... | ✅ | ❌ only by git provider | ✅ | ❌ | ❌ | ✅ | ✅ |
| ... send by eMail | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| watchdog for status page support | ⁇ | ⁇ | ✅ | ❌ | ✅ | ⁇ | ❌ |
| trigger webhook support | ❌ needs cachet-monitor | ⁇ | ✅ | ⁇ | ✅ | ⁇ | ❌ |
| ADDITIONAL INFORMATION | - | basically a theme for hugo cms, depends on netlify cms | - | basically a theme for hugo cms, depends on netlify cms | - | It's highly optimized for github pages | SPA created with netlify |
| hidden components | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| user management | ✅ | ❌ | ❌ | ❌ | ✅ by OIDC | ⁇ through github? | ❌ |
| different output format on notification | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| external hosting | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ looks like you are limited to github | ✅ |
| project healthy | ❌ last commit 17 months | ❌ last commit 3 years | ❌ last commit 5 months | ✅ last commit 2 months | ✅ recent activities | ✅ recent activities | ❌ archived and abondend by the owner |
| documentation | ✅ API ❌ User Documentation | ❌ | ❌ | ❌ | ✅ | ⁇u | ❌ not reachable anymore |
| git based | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ⁇ a netlify based installation is able to communicate with github |
| project URL | <https://cachethq.io/> | <https://github.com/weeblrpress/clearstatus> | <https://www.brotandgames.com/ciao/> | <https://cstate.netlify.app/> | <https://gatus.io/> | <https://github.com/tadhglewis/issue-status> | <https://marquez.co/statusfy> |
