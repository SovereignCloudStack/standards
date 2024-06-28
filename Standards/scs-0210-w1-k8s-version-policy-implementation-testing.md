---
title: "SCS K8S Version Policy: Implementation and Testing Notes"
type: Supplement
track: KaaS
status: Proposal
supplements:
  - scs-0210-v1-k8s-new-version-policy.md
  - scs-0210-v2-k8s-version-policy.md
---

## Implementation notes

A CSP must make new versions for their KaaS offering available in a timely fashion, so that
new versions are available in a short window of time.
Older versions need to be supported until the end of their support window.

Concrete implementation details can't be give here, since not every CSP does provide
their versions the same way. The best advice to give is to monitor the
[Kubernetes releases page](https://kubernetes.io/releases/) closely.

## Automated tests

### Notes

The test for the [K8s Version Policy Standard](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0210-v2-k8s-version-policy.md)
can't be used like most other tests provided in the SCS standards repository.
It aims on testing a KaaS offering of a CSP with the creation of the most recent
Kubernetes version provided by the CSP. Since only this part is tested,
the test doesn't have any validity for a single cluster, since the updating and
versioning should be decided by the user, which could want to leave a server
on a version just for stability reasons.

### Implementation

The script [`k8s_version_policy.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/kaas/k8s-version-policy/k8s_version_policy.py)
connects to an existing K8s cluster and checks the version against a list of versions, that
are calculated to be inside a recency window.

## Manual tests

None.
