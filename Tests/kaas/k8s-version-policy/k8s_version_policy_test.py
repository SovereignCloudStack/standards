"""
Pytest based unit tests for k8s_version_policy.

(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 3/2024
License: CC-BY-SA 4.0
"""

from datetime import datetime

from k8s_version_policy import (
    is_high_severity,
    parse_branch_info,
    parse_github_release_data,
    parse_version,
    K8sBranch,
    K8sVersion,
    VersionRange,
)


def test_is_high_severity():
    high31 = {"cvssV3_1": {"baseScore": 8.0}}
    high30 = {"cvssV3_0": {"baseScore": 8.0}}
    low31 = {"cvssV3_1": {"baseScore": 7.9}}
    low30 = {"cvssV3_0": {"baseScore": 7.9}}
    assert is_high_severity([high31])
    assert is_high_severity([high30])
    assert is_high_severity([low31, high30])
    assert not is_high_severity([low31])
    assert not is_high_severity([low30, low31])


def test_parse_version():
    version = parse_version("  v2.4.99   ")
    assert version.major == 2
    assert version.minor == 4
    assert version.patch == 99


def test_parse_branch_info():
    branch_info = parse_branch_info({
        "branch": "1.29",
        "end-of-life": "2025-02-28",
    })
    assert branch_info.branch.major == 1
    assert branch_info.branch.minor == 29
    assert branch_info.eol == datetime(year=2025, month=2, day=28)


def test_parse_release_data1():
    release = parse_github_release_data({
        "tag_name": "v1.29.3-dev0",
        "published_at": "2024-02-03T13:37:42Z",
    })
    assert release.version == K8sVersion(1, 29, 3)
    assert release.released_at == datetime(2024, 2, 3, 13, 37, 42)


def test_parse_release_data2():
    release = parse_github_release_data({
        "tag_name": "1.24.0",
        "published_at": "2023-01-03T13:37:42Z",
    })
    assert release.version == K8sVersion(1, 24, 0)
    assert release.released_at == datetime(2023, 1, 3, 13, 37, 42)


def test_k8s_version_operators():
    assert K8sVersion(1, 2, 3) == K8sVersion(1, 2, 3)
    assert K8sVersion(1, 2, 0) == K8sVersion(1, 2)
    assert K8sVersion(1, 2, 3) < K8sVersion(1, 2, 4)
    assert K8sVersion(1, 2, 3) < K8sVersion(1, 3, 0)
    assert K8sVersion(1, 2, 3) < K8sVersion(2, 0, 0)


def test_k8s_branch_basics():
    assert K8sBranch(1, 29) == K8sBranch(1, 29)
    assert K8sBranch(1, 28) < K8sBranch(1, 29)
    assert K8sVersion(1, 28, 5).branch == K8sBranch(1, 28)
    assert K8sBranch(1, 29).previous() == K8sBranch(1, 28)


def test_version_range_contains_with_no_upper_limit():
    single_version_range = VersionRange(K8sVersion(3, 4, 5))
    assert K8sVersion(3, 4, 4) not in single_version_range
    assert K8sVersion(3, 4, 5) in single_version_range
    assert K8sVersion(3, 4, 6) not in single_version_range


def test_version_range_contains_inclusive():
    version_range = VersionRange(K8sVersion(1, 2, 1), K8sVersion(1, 3, 4), inclusive=True)
    assert K8sVersion(1, 2, 0) not in version_range
    assert K8sVersion(1, 2, 1) in version_range
    assert K8sVersion(1, 3, 4) in version_range
    assert K8sVersion(1, 3, 5) not in version_range


def test_version_range_contains_exclusive():
    version_range = VersionRange(K8sVersion(1, 2, 1), K8sVersion(1, 3, 4))
    assert not version_range.inclusive
    assert K8sVersion(1, 2, 0) not in version_range
    assert K8sVersion(1, 2, 1) in version_range
    assert K8sVersion(1, 3, 3) in version_range
    assert K8sVersion(1, 3, 4) not in version_range
