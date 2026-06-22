#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""
K8s Version Policy Checker (scs-v0210-v2)
https://github.com/SovereignCloudStack/standards

Run testcase version-policy-check and output result to stdout.
Return code will be non-zero precisely when the testcase could not
be run.

(c) Hannes Baum <hannes.baum@cloudandheat.com>, 6/2023
(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 2/2024
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 3/2024
(c) Matthias Büchse <matthias.buechse@alasca.cloud>, 6/2026
SPDX-License-Identifier: CC-BY-SA-4.0
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import contextlib
import getopt
import logging
import re
import sys

import aiohttp
import asyncio
import kubernetes_asyncio
import yaml


MINOR_VERSION_CADENCE = timedelta(days=120)
PATCH_VERSION_CADENCE = timedelta(days=31)
CVE_VERSION_CADENCE = timedelta(weeks=2)
CVE_VERSION_CADENCE_WARN = timedelta(days=2)
CVE_SEVERITY = 8  # CRITICAL

HERE = Path(__file__).parent
EOLDATA_PATH = Path(HERE, "k8s-eol-data.yml")

logger = logging.getLogger(__name__)


class ConfigException(BaseException):
    """Exception raised in a configuration error occurs"""


class HelpException(BaseException):
    """Exception raised if the help functionality is called"""


def print_usage():
    print("""
K8s Version Policy Compliance Check

Usage: k8s_version_policy.py [-h] -k|--kubeconfig PATH/TO/KUBECONFIG

This tool checks whether the given cluster conforms to the SCS k8s version policy. It checks one
cluster only, so it doesn't check whether multiple k8s branches are offered. The return code
will be 0 precisely when all attempted checks are passed; otherwise check log messages.

    -k/--kubeconfig PATH/TO/KUBECONFIG - Path to the kubeconfig of the server we want to check
    -h                                 - Output help
""")


class Config:
    def __init__(self, log_level=logging.INFO):
        self.kubeconfig = None
        self.log_level = log_level

    def apply_argv(self, argv):
        """Parse cli arguments from the script call"""
        try:
            opts, args = getopt.gnu_getopt(argv, "k:h", ["kubeconfig=", "help"])
        except getopt.GetoptError:
            raise ConfigException

        for opt in opts:
            if opt[0] == "-h" or opt[0] == "--help":
                raise HelpException
            if opt[0] == "-k" or opt[0] == "--kubeconfig":
                self.kubeconfig = opt[1]

    def setup(self):
        """Initialize the configuration for the test script"""
        logging.basicConfig(format='%(levelname)s: %(message)s', level=self.log_level)
        for name in logging.root.manager.loggerDict:
            logger = logging.getLogger(name)
            if not logger.level:
                logger.setLevel(self.log_level)
        if self.kubeconfig is None:
            raise ConfigException("A kubeconfig needs to be set in order to test a k8s cluster version.")


@dataclass(frozen=True, eq=True, order=True)
class K8sVersion:
    major: int
    minor: int
    patch: int = 0

    @property
    def branch(self):
        """Get the branch of this version, i.e., the version w/o patch level."""
        return K8sBranch(self.major, self.minor)

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


K8sVersion.MINIMUM = K8sVersion(0, 0)


def parse_version(version_str: str) -> K8sVersion:
    cleansed = version_str.strip().removeprefix("v").split("+")[0]  # remove leading v as well as build info
    try:
        major, minor, patch = cleansed.split(".")
        return K8sVersion(int(major), int(minor), int(patch))
    except ValueError:
        raise ValueError(f"Unrecognized version format: {version_str}")


@dataclass(frozen=True, eq=True, order=True)
class K8sBranch:
    """Identifies a release branch of K8s just by major and minor version."""

    major: int
    minor: int

    def previous(self):
        if self.minor == 0:
            # FIXME: this is ugly
            return self
        return K8sBranch(self.major, self.minor - 1)

    def __str__(self):
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True)
class K8sBranchInfo:
    branch: K8sBranch
    eol: datetime

    def is_supported(self) -> bool:
        return datetime.now() < self.eol

    def is_eol(self) -> bool:
        return not self.is_supported()


@dataclass(frozen=True)
class K8sRelease:
    version: K8sVersion
    released_at: datetime

    def __str__(self):
        return f"{self.version} ({self.released_at.isoformat()})"

    @property
    def age(self):
        return datetime.now() - self.released_at


async def fetch_k8s_releases_data(session: aiohttp.ClientSession) -> list[dict]:
    github_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Request the latest 100 releases (the next are not needed, since these versions are too old)
    response = await session.get(
        "https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=100",
        headers=github_headers,
    )
    return await response.json()


def parse_github_release_data(release_data: dict) -> K8sRelease:
    version = parse_version(release_data["tag_name"].split("-")[0])
    released_at = datetime.strptime(release_data["published_at"], "%Y-%m-%dT%H:%M:%SZ")
    return K8sRelease(version, released_at)


@dataclass(frozen=True, eq=True)
class VersionRange:
    """
    Version range with a lower and upper bound.

    Supports checking if a K8sVersion is in the range using the `in`
    operator.
    If `inclusive` is True, `upper_version` is inside the range (i.e.,
    it is a closed interval), otherwise `upper_version` is outside.
    If `upper_version` is not set, the range just represents a single
    version, namely `lower_version`.
    """

    lower_version: K8sVersion
    upper_version: K8sVersion = None
    inclusive: bool = False

    def __post_init__(self):
        if self.lower_version is None:
            raise ValueError("lower_version must not be None")
        if self.upper_version and self.upper_version < self.lower_version:
            raise ValueError("lower_version must be lower than upper_version")

    def __contains__(self, version: K8sVersion) -> bool:
        if self.upper_version is None:
            return self.lower_version == version
        if self.inclusive:
            return self.lower_version <= version <= self.upper_version
        return self.lower_version <= version < self.upper_version


@dataclass
class ClusterInfo:
    version: K8sVersion
    name: str


async def request_cve_data(session: aiohttp.ClientSession, cveid: str) -> dict:
    """Request for a single CVE data item."""
    async with session.get(
        f"https://cveawg.mitre.org/api/cve/{cveid}",
        headers={"Accept": "application/json"}
    ) as resp:
        return await resp.json()


def parse_cve_version_information(cve_version_info: dict) -> VersionRange:
    """Parse the CVE version information according to their CVE JSON 5.0 schema"""
    vi_lower_version = None
    vi_upper_version = None
    inclusive = False

    # Extract the version if it is viable, but it's not a requirement
    with contextlib.suppress(ValueError):
        vi_lower_version = parse_version(cve_version_info['version'])

    if 'lessThanOrEqual' in cve_version_info:
        vi_upper_version = parse_version(cve_version_info['lessThanOrEqual'])
        inclusive = True
    elif 'lessThan' in cve_version_info:
        vi_upper_version = parse_version(cve_version_info['lessThan'])

    # This shouldn't happen, but if it happens, we look for non-standard descriptions
    # According to this(https://www.cve.org/AllResources/CveServices#cve-json-5),
    # this isn't how the data should be described
    if vi_lower_version is None and vi_upper_version is None:
        if re.search(r'v?\d+\.\d+\.x', cve_version_info['version']):
            vdata = cve_version_info['version'].strip("v").split(".")
            vi_lower_version = K8sVersion(int(vdata[0]), int(vdata[1]), 0)
            vi_upper_version = K8sVersion(int(vdata[0]), int(vdata[1]), 0)

        if re.search(r'v?\d+\.\d+\.\d+\s+-\s+v?\d+\.\d+\.\d+', cve_version_info['version']):
            vdata = cve_version_info['version'].split("-")
            vi_lower_version = parse_version(vdata[0])
            vi_upper_version = parse_version(vdata[1])

    if vi_lower_version is None:
        vi_lower_version = K8sVersion.MINIMUM

    return VersionRange(vi_lower_version, vi_upper_version, inclusive)


def is_high_severity(cve_metrics: list) -> bool:
    return any(
        re.search(r'[cC][vV][sS]{1,2}V\d', metric_key) and metric_value['baseScore'] >= CVE_SEVERITY
        for cve_metric in cve_metrics
        for metric_key, metric_value in cve_metric.items()
    )


async def collect_cve_versions(session: aiohttp.ClientSession) -> set:
    """Get all relevant CVE versions, that are relevant for the test according to the severity
    dictated by the Standard.
    """

    # CVE fix versions
    cfvs = set()

    # Request latest version
    async with session.get(
        "https://kubernetes.io/docs/reference/issues-security/official-cve-feed/index.json",
        headers={"Accept": "application/json"}
    ) as resp:
        cve_list = await resp.json()

    tasks = [request_cve_data(session=session, cveid=cve['id'])
             for cve in cve_list['items']]

    cve_data_list = await asyncio.gather(*tasks, return_exceptions=True)

    for cve_data in cve_data_list:
        try:
            cve_cna = cve_data['containers']['cna']
            cve_metrics = cve_cna['metrics']
            cve_affected = cve_cna['affected']
            # This data is extracted like this due to the location of the relevant information in the schema.
            # mitre.org uses CVE schema 5.0, which is described in the link below
            # https://github.com/CVEProject/cve-schema/tree/master/schema/v5.0
            # The containers -> cna path contains vulnerability information like severity, which is documented
            # under the metrics list.
            # https://cveproject.github.io/cve-schema/schema/v5.0/docs/
        except KeyError as e:
            logger.debug(
                f"They key {e} couldn't be found in the CVE json data for CVE "
                f"{cve_data.get('cveMetadata', {}).get('cveId', '<ID NOT SET>')}."
            )
            continue

        if is_high_severity(cve_metrics):
            affected_kubernetes_versions = [
                parse_cve_version_information(version_info)
                for aff in cve_affected
                if aff['product'] == "Kubernetes"
                for version_info in aff['versions']
                if version_info['status'] == "affected"
            ]
            cfvs.update(affected_kubernetes_versions)

    return cfvs


async def get_k8s_cluster_info(kubeconfig, context=None) -> ClusterInfo:
    """Get the k8s version of the cluster under test."""
    cluster_config = await kubernetes_asyncio.config.load_kube_config(kubeconfig, context)

    async with kubernetes_asyncio.client.ApiClient() as api:
        version_api = kubernetes_asyncio.client.VersionApi(api)
        response = await version_api.get_code()
        version = parse_version(response.git_version)
        return ClusterInfo(version, cluster_config.current_context['name'])


def check_k8s_version_recency(
    my_version: K8sVersion,
    releases_data: list[dict],
    cve_affected_ranges: set[VersionRange],
) -> bool:
    """
    Check a given K8s cluster version against the list of released versions
    in order to find out if the version is an accepted recent version according
    to the standard.
    """

    # iterate over all releases in the list, but only look at those whose branch matches
    # we might break early assuming that the list is sorted somehow, but it is usually
    # of bounded length (100), and the loop body not very expensive either
    for release_data in releases_data:
        if release_data['draft'] or release_data['prerelease']:
            continue

        release = parse_github_release_data(release_data)
        if my_version.branch != release.version.branch:
            continue
        if my_version.patch >= release.version.patch:
            continue
        # at this point `release` has the same major.minor, but higher patch than `my_version`
        if release.age > PATCH_VERSION_CADENCE:
            # whoops, the cluster should have been updated to this (or a higher version) already!
            return False
        ranges = [_range for _range in cve_affected_ranges if my_version in _range]
        if ranges and release.age > CVE_VERSION_CADENCE_WARN:
            # -- FIXME:
            # if the release still has the CVE, then there is no use if we updated to it?
            # shouldn't we check for CVEs of my_version and then check whether the new one still has them?
            # -- so, this has to be reworked in a major way, but for the time being, just emit an INFO
            # (unfortunately, the cluster name is not available here)
            logger.warning(
                "Consider updating from %s to %s to avoid a CVE",
                my_version,
                release.version,
            )
            if release.age > CVE_VERSION_CADENCE:
                return False
    return True


def parse_branch_info(data: dict) -> K8sBranchInfo:
    major, minor = data["branch"].split(".")
    branch = K8sBranch(int(major), int(minor))
    eol_date = datetime.strptime(data["end-of-life"], "%Y-%m-%d")
    return K8sBranchInfo(branch, eol_date)


def read_supported_k8s_branches(eol_data_path: Path) -> dict[K8sBranch, K8sBranchInfo]:
    with open(eol_data_path) as stream:
        data = yaml.load(stream, Loader=yaml.FullLoader)
    infos = [parse_branch_info(item) for item in data]
    return {info.branch: info for info in infos}


def determine_supported_branches(eoldata_path=EOLDATA_PATH):
    branch_infos = read_supported_k8s_branches(eoldata_path)
    supported_branches = {
        branch
        for branch, branch_info
        in branch_infos.items()
        if branch_info.is_supported()
    }
    if len(supported_branches) < 3:
        logger.warning("The EOL data in %s isn't up-to-date.", eoldata_path.name)
    if len(supported_branches) < 2:
        raise RuntimeError(f"The EOL data in {eoldata_path.name} is critically outdated!")
    return supported_branches


def compute_version_policy_check(supported_branches, cve_affected_ranges, releases_data, cluster):
    if cluster.version.branch not in supported_branches:
        logger.error("The K8s cluster version %s of cluster '%s' is already EOL.", cluster.version, cluster.name)
        return False
    if check_k8s_version_recency(cluster.version, releases_data, cve_affected_ranges):
        logger.info(
            "The K8s cluster version %s of cluster '%s' is still in the recency time window.",
            cluster.version,
            cluster.name,
        )
        return True
    for affected_range in cve_affected_ranges:
        if cluster.version in affected_range:
            logger.error(
                "The K8s cluster version %s of cluster '%s' is an outdated version with a possible CRITICAL CVE.",
                cluster.version,
                cluster.name,
            )
    logger.error(
        "The K8s cluster version %s of cluster '%s' is outdated according to the standard.",
        cluster.version,
        cluster.name,
    )
    return False


async def main(argv):
    config = Config()
    try:
        config.apply_argv(argv)
        config.setup()
    except HelpException:
        print_usage()
        return 0
    except BaseException as e:
        logger.critical("%s", e)
        return 1

    try:
        supported_branches = determine_supported_branches()
        connector = aiohttp.TCPConnector(limit=5)
        logger.info("Checking cluster specified in %s.", config.kubeconfig)
        async with aiohttp.ClientSession(connector=connector) as session:
            cve_affected_ranges, releases_data, cluster = await asyncio.gather(
                collect_cve_versions(session),
                fetch_k8s_releases_data(session),
                get_k8s_cluster_info(config.kubeconfig),
            )
        result = compute_version_policy_check(
            supported_branches, cve_affected_ranges, releases_data, cluster)
        print("version-policy-check: " + ('FAIL', 'PASS')[bool(result)])
    except BaseException:
        print("version-policy-check: ABORT")
        logger.critical("Could not complete version-policy-check", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
