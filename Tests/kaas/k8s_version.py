#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""
Print the Kubernetes version (major.minor.patch) of the cluster behind a kubeconfig.

Usage: k8s_version.py [-k/--kubeconfig KUBECONFIG_PATH] [-s/--subject SUBJECT]

The kubeconfig defaults to SUBJECT/kubeconfig.yaml (relative to the working directory),
mirroring k8s_test.py. The version is the one reported by the API server, so it is
the control plane version, not the kubelet versions.

Output (stdout): a single line such as `1.35.2`. Nonzero exit code if it can't be determined.
"""
import asyncio
import getopt
import os.path
import sys

from scs_0210_version_policy.k8s_version_policy import get_k8s_cluster_info


def main(argv):
    try:
        opts, _ = getopt.gnu_getopt(argv, "k:s:", ("kubeconfig=", "subject="))
    except getopt.GetoptError as exc:
        print(f"{exc}\n{__doc__}", file=sys.stderr)
        return 2
    kubeconfig, subject = None, None
    for key, value in opts:
        if key in ("-k", "--kubeconfig"):
            kubeconfig = value
        elif key in ("-s", "--subject"):
            subject = value
    if kubeconfig is None:
        if subject is None:
            print(f"need either -k or -s\n{__doc__}", file=sys.stderr)
            return 2
        kubeconfig = os.path.join('.', subject, 'kubeconfig.yaml')
    try:
        info = asyncio.run(get_k8s_cluster_info(kubeconfig))
    except Exception as exc:
        # one line instead of a traceback: callers (the test runner) log this verbatim
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(info.version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
