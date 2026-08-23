---
title: Kubernetes cluster hardening - Bare-metal K3s Implementation Notes
type: Standard Supplement
status: Draft
track: KaaS
---

> **Note:** **[graphwiz.AI generated content]**
>
> This document was generated with AI assistance. It is
> currently in **draft** status: while it reflects a verified reference
> deployment, it has not yet been fully tested/reviewed by the SCS
> project. Please validate all commands against your own environment
> before using them in production.

## Overview

This document provides implementation notes for deploying SCS-compliant Kubernetes clusters using **bare-metal K3s**. These notes supplement the [SCS-0217-v1 Cluster Hardening](scs-0217-v1-cluster-hardening.md) standard with K3s-specific considerations.

**Target Audience:** Operators deploying SCS-compliant KaaS on bare-metal infrastructure using K3s.

**Reference Implementation:** 3-node bare-metal K3s cluster (k3s-master-01, k3s-worker-01, k3s-worker-02) with Ceph storage, HAProxy ingress, and Flannel CNI.

---

## K3s-Specific Considerations

### Embedded etcd (dqlite/sqlite)

**Standard Requirement (SCS-0217-v1):**
> The etcd database should be isolated from the rest of a Kubernetes cluster. Access should only be granted to components that need it.

**K3s Implementation:**
K3s embeds etcd (or dqlite/sqlite for single-server mode) directly into the K3s binary. This differs from standard Kubernetes deployments where etcd runs as separate pods or on dedicated machines.

**Security Implications:**

| Aspect | Standard Kubernetes | K3s Embedded |
|--------|---------------------|--------------|
| Network Exposure | etcd typically on 2379/2380 | **No network exposure** (local socket only) |
| ACL Configuration | Separate etcd ACL system | Uses K3s single CA for all components |
| Isolation | Can be on separate machines | Runs on control-plane node |
| Attack Surface | External network access possible | **Inherently more secure** (no network) |

**Compliance Assessment:**
- ✅ **etcd isolation:** K3s embedded etcd is **more secure** than separate etcd cluster because it has no network exposure
- ⚠️ **etcd ACL:** K3s uses single CA for all components; separate etcd ACL not available
- ✅ **Strong authentication:** K3s uses TLS client certificates for all component communication

**Recommendation:**
For bare-metal K3s deployments, the embedded etcd architecture should be considered **compliant** with SCS-0217 etcd isolation requirements, as it provides stronger isolation than network-isolated etcd clusters. The trade-off is accepting K3s's unified CA model instead of separate etcd ACLs.

---

### NetworkPolicy Enforcement

**Standard Requirement (SCS-0219-v1):**
> NetworkPolicy API must be enforced.

**K3s Implementation:**
K3s includes a built-in NetworkPolicy controller (`kube-network-policy`) that enforces NetworkPolicy objects without requiring external CNI plugins like Calico or Cilium.

**Verification:**
```bash
# Check NetworkPolicy enforcement
kubectl get networkpolicy --all-namespaces
# Should show policies in opendesk-edu, opendesk, backup, etc.

# Verify K3s network policy controller
k3s --help | grep network
# Output: --disable-network-policy (Disable K3s network policy)
```

**Compliance Assessment:**
- ✅ **NetworkPolicy API:** Available and enforced
- ✅ **Default deny:** Can be implemented via NetworkPolicy objects
- ✅ **CNI:** Flannel with K3s built-in controller supports NetworkPolicy

---

### Pod Security Standards

**Standard Requirement (SCS-0217-v1):**
> Pod Security Standards should be enforced.

**K3s Implementation:**
K3s fully supports Kubernetes Pod Security Admission (PSA) via namespace labels.

**Recommended Namespace Labels:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: example-namespace
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: baseline
    pod-security.kubernetes.io/warn: baseline
```

**System Namespace Exceptions:**
Some system components require privileged access and should be excluded from baseline enforcement:

| Namespace | Reason | Recommended Level |
|-----------|--------|-------------------|
| `kube-system` | Core K8s components | `privileged` |
| `metallb-system` | Layer 2 load balancer | `privileged` (host networking) |
| `monitoring` | Prometheus, node-exporter | `privileged` (hostPath, hostPort) |
| `cert-manager` | Certificate management | `privileged` (webhooks) |

**Compliance Assessment:**
- ✅ **Pod Security API:** Fully supported
- ✅ **Baseline enforcement:** Recommended for all tenant namespaces
- ⚠️ **System namespaces:** Require `privileged` level (acceptable for system components)

---

### Node Topology Labels

**Standard Requirement (SCS-0214-v2):**
> Nodes should have topology labels for failure zone awareness.

**K3s Implementation:**
K3s does not automatically add topology labels. They must be applied manually or via automation (Ansible, Terraform, etc.).

**Recommended Labels:**
```bash
kubectl label nodes k3s-master-01 \
  topology.kubernetes.io/region=dc1 \
  topology.kubernetes.io/zone=dc1-a \
  --overwrite

kubectl label nodes k3s-worker-01 \
  topology.kubernetes.io/region=dc1 \
  topology.kubernetes.io/zone=dc1-b \
  --overwrite

kubectl label nodes k3s-worker-02 \
  topology.kubernetes.io/region=dc1 \
  topology.kubernetes.io/zone=dc1-c \
  --overwrite
```

**Compliance Assessment:**
- ✅ **Topology labels:** Can be applied manually or via automation
- ✅ **Failure zone awareness:** Achieved with zone labels
- ⚠️ **Single master:** K3s single-master with embedded etcd (acceptable for bare-metal)

---

### Default Storage Class

**Standard Requirement (SCS-0211-v2):**
> A failure-safe default storage class must be configured.

**K3s Implementation:**
K3s ships with `local-path` as the default storage class, which is **not failure-safe** (node-local storage).

**Recommended Configuration:**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: rbd.csi.ceph.com
# ... Ceph RBD parameters ...
```

**Compliance Assessment:**
- ⚠️ **Default SC:** `local-path` is default but NOT failure-safe
- ✅ **Failure-safe SC:** Ceph RBD available, must be set as default
- ✅ **Action required:** Patch default SC annotation

---

## Implementation Checklist

### Prerequisites
- [ ] K3s v1.36.3+ installed on all nodes
- [ ] Ceph cluster accessible from K3s nodes
- [ ] HAProxy ingress configured
- [ ] NetworkPolicy objects defined

### SCS Compliance Steps

1. **Set Default Storage Class**
   ```bash
   kubectl patch storageclass ceph-rbd -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
   kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
   ```

2. **Apply Topology Labels**
   ```bash
   # Apply to all nodes with appropriate region/zone labels
   kubectl label nodes <node-name> topology.kubernetes.io/region=<region> topology.kubernetes.io/zone=<zone> --overwrite
   ```

3. **Enforce Pod Security Standards**
   ```bash
   # Apply to all tenant namespaces
   for ns in argocd backup cert-manager nix-builder opendesk-edu opendesk-predictive-agent opendesk-staff opendesk-students; do
     kubectl label ns "$ns" \
       pod-security.kubernetes.io/enforce=baseline \
       pod-security.kubernetes.io/audit=baseline \
       pod-security.kubernetes.io/warn=baseline \
       --overwrite
   done
   ```

4. **Verify NetworkPolicy Enforcement**
   ```bash
   kubectl get networkpolicy --all-namespaces
   ```

5. **Run SCS Compliance Tests**
   ```bash
   cd vendor/standards/Tests
   ./scs-compliance-check.py -s <subject> -S kaas \
     -a subject_root=$(pwd) -a kubeconfig=~/.kube/config \
     scs-compatible-kaas.yaml
   ```

---

## Known Limitations

### 1. Single Master Node

K3s single-master deployment with embedded etcd is **acceptable for bare-metal** but does not provide HA for the control plane.

**Recommendation:** For production HA, use K3s server replication (3+ servers) with embedded etcd clustering.

### 2. Embedded etcd ACL

K3s does not support separate etcd ACL configuration. All components use the same CA.

**Assessment:** Acceptable trade-off for bare-metal K3s. Embedded etcd with no network exposure is more secure than network-isolated etcd with ACL.

### 3. Monitoring Stack Privileges

System monitoring components (Prometheus, node-exporter, promtail) require privileged access (hostPath, hostPort, host namespaces).

**Recommendation:** Keep `monitoring` namespace at `privileged` level. This is acceptable for system infrastructure.

---

## References

- [SCS-0217-v1: Cluster Hardening](scs-0217-v1-cluster-hardening.md)
- [SCS-0214-v2: Node Distribution](scs-0214-v2-k8s-node-distribution.md)
- [SCS-0211-v2: Default Storage Class](scs-0211-v2-kaas-default-storage-class.md)
- [SCS-0219-v1: KaaS Networking](scs-0219-v1-kaas-networking.md)
- [K3s Documentation](https://docs.k3s.io/)
- [Kubernetes Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-08-22 | v1-draft | Initial draft with bare-metal K3s implementation notes |
