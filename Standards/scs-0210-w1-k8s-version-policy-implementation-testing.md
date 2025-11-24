---
title: "SCS K8S Version Policy: Implementation and Testing Notes"
type: Supplement
track: KaaS
supplements:
  - scs-0210-v2-k8s-version-policy.md
---

## Implementation notes

The standard is quite concise about [the regulations](https://docs.scs.community/standards/scs-0210-v2-k8s-version-policy#decision),
so they are not restated here. Suffice it to say that a
CSP must make new versions for their KaaS offering available in a timely fashion, so that
new versions are available in a short window of time.
Older versions need to be supported until the end of their support window.

Concrete implementation details can't be given here, since not every CSP does provide
their versions the same way. The best advice to give is to monitor the
[Kubernetes releases page](https://kubernetes.io/releases/) closely.

## Automated tests

### Implementation

The script [`k8s_version_policy.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-version-policy/k8s_version_policy.py)
connects to an existing K8s cluster and checks the version against a list of versions, that
are calculated to be inside a recency window.

Note that this implementation is subject to change, because testing an existing cluster is not
sufficient to guarantee that all active k8s branches are supported and kept up to date.

## Manual tests

None.
