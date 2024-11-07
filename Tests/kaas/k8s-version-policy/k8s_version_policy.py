#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""
K8s Version Policy Checker (scs-v0210-v2)
https://github.com/SovereignCloudStack/standards

Return code is 0 precisely when it could be verified that the standard is satisfied.
Otherwise the return code is the number of errors that occurred (up to 127 due to OS
restrictions); for further information, see the log messages on various channels:
    CRITICAL  for problems preventing the test to complete,
    ERROR     for violations of requirements,
    INFO      for violations of recommendations,
    DEBUG     for background information and problems that don't hinder the test.

This script only checks one given cluster, so it doesn't check whether multiple
k8s branches are being offered.
It is determined if the version on the cluster is still inside
the recency window, which is determined by the standard to be 4 months
for minor versions (for the stable cluster) and 1 week for patch versions.
An exception are versions with critical CVEs, which should be replaced on
a shorter notice.

(c) Hannes Baum <hannes.baum@cloudandheat.com>, 6/2023
(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 2/2024
(c) Matthias Büchse <matthias.buechse@cloudandheat.com>, 3/2024
(c) Piotr Bigos <piotr.bigos@dNation.com>
SPDX-License-Identifier: CC-BY-SA-4.0
"""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import asyncio
import contextlib
import getopt
import json
import kubernetes_asyncio
import logging
import logging.config
import re
import requests
import subprocess
import sys
import yaml


MINOR_VERSION_CADENCE = timedelta(days=120)
PATCH_VERSION_CADENCE = timedelta(weeks=2)
CVE_VERSION_CADENCE = timedelta(days=2)
CVE_SEVERITY = 8  # CRITICAL

HERE = Path(__file__).parent
EOLDATA_FILE = "k8s-eol-data.yml"

logging_config = {
    "level": "INFO",
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "k8s_version_policy": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "k8s_version_policy",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "handlers": ["console"]
    }
}

logger = logging.getLogger(__name__)


class CountingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        self.bylevel = Counter()

    def handle(self, record):
        self.bylevel[record.levelno] += 1


class ConfigException(BaseException):
    """Exception raised in a configuration error occurs"""


class HelpException(BaseException):
    """Exception raised if the help functionality is called"""


class CriticalException(BaseException):
    """Exception raised if the critical CVE are found"""


class Config:
    kubeconfig = None
    context = None
    logging = logging_config


def print_usage():
    print("""
K8s Version Policy Compliance Check

Usage: k8s_version_policy.py [-h] -k|--kubeconfig PATH/TO/KUBECONFIG [--context CONTEXT]

This tool checks whether the given cluster conforms to the SCS k8s version policy. It checks one
cluster only, so it doesn't check whether multiple k8s branches are offered. The return code
will be 0 precisely when all attempted checks are passed; otherwise check log messages.

    -k/--kubeconfig PATH/TO/KUBECONFIG - Path to the kubeconfig of the server we want to check
    -C/--context CONTEXT               - Optional: kubeconfig context to use
    -h                                 - Output help
""")


def parse_arguments(argv):
    """Parse cli arguments from the script call"""
    try:
        opts, args = getopt.gnu_getopt(argv, "C:k:h", ["context=", "kubeconfig=", "help"])
    except getopt.GetoptError:
        raise ConfigException

    config = Config()
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            raise HelpException
        if opt[0] == "-k" or opt[0] == "--kubeconfig":
            config.kubeconfig = opt[1]
        if opt[0] == "-C" or opt[0] == "--context":
            config.context = opt[1]
    return config


def setup_logging(config_log):
    logging.config.dictConfig(config_log)
    loggers = [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if not logging.getLogger(name).level
    ]
    for log in loggers:
        log.setLevel(config_log['level'])


def initialize_config(config):
    """Initialize the configuration for the test script"""
    setup_logging(config.logging)
    if config.kubeconfig is None:
        raise ConfigException("A kubeconfig needs to be set in order to test a k8s cluster version.")
    return config


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


def fetch_k8s_releases_data() -> list[dict]:
    github_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Request the latest 100 releases (the next are not needed, since these versions are too old)
    return requests.get(
        "https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=100",
        headers=github_headers,
    ).json()


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


async def run_trivy_scan(image: str) -> dict:
    """Run Trivy scan on the specified image and return the results as a dictionary.

    Args:
        image (str): The Docker image to scan.

    Returns:
        dict: Parsed JSON results from Trivy.
    """
    try:
        # Run the Trivy scan command
        result = await asyncio.create_subprocess_exec(
            'trivy',
            'image',
            '--format', 'json',
            '--no-progress',
            image,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            logger.error("Trivy scan failed: %s", stderr.decode().strip())
            return {}

        # Parse the JSON output from Trivy
        return json.loads(stdout.decode())

    except Exception as e:
        logger.error("Error running Trivy scan: %s", e)
        return {}


async def get_k8s_pod_images(kubeconfig, context=None) -> list[str]:
    """Get the list of container images used by all the pods in the Kubernetes cluster."""

    async with kubernetes_asyncio.client.ApiClient() as api:
        v1 = kubernetes_asyncio.client.CoreV1Api(api)
        pods = await v1.list_pod_for_all_namespaces(watch=False)

        images = set()
        for pod in pods.items:
            for container in pod.spec.containers:
                images.add(container.image)

            if pod.spec.init_containers:
                for container in pod.spec.init_containers:
                    images.add(container.image)

        return list(images)


async def scan_k8s_images(images_to_scan) -> None:
    """Scan the images used in the Kubernetes cluster for vulnerabilities."""

    for image in images_to_scan:
        logger.info(f"Scanning image: {image}")
        scan_results = await run_trivy_scan(image)

        if scan_results:
            for result in scan_results.get('Results', []):
                for vulnerability in result.get('Vulnerabilities', []):
                    logger.warning(
                        f"""Vulnerability found in image {image}:
                            {vulnerability['VulnerabilityID']} "
                            (Severity: {vulnerability['Severity']})"""
                    )


async def get_images_and_scan(kubeconfig, context=None) -> None:
    images_to_scan = await get_k8s_pod_images(kubeconfig, context)
    await scan_k8s_images(images_to_scan)


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
        if ranges and release.age > CVE_VERSION_CADENCE:
            # -- two FIXMEs:
            # (a) if the release still has the CVE, then there is no use if we updated to it?
            # (b) the standard says "time period MUST be even shorter ... it is RECOMMENDED that ...",
            #     so what is it now, a requirement or a recommendation?
            # shouldn't we check for CVEs of my_version and then check whether the new one still has them?
            # -- so, this has to be reworked in a major way, but for the time being, just emit an INFO
            # (unfortunately, the cluster name is not available here)
            logger.info(
                "Consider updating from %s to %s to avoid a CVE",
                my_version,
                release.version,
            )
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


async def main(argv):
    try:
        config = initialize_config(parse_arguments(argv))
    except (OSError, ConfigException, HelpException) as e:
        logger.critical("%s", e)
        print_usage()
        return 1

    counting_handler = CountingHandler(level=logging.INFO)
    logger.addHandler(counting_handler)

    branch_infos = read_supported_k8s_branches(Path(HERE, EOLDATA_FILE))
    supported_branches = {
        branch
        for branch, branch_info
        in branch_infos.items()
        if branch_info.is_supported()
    }
    if len(supported_branches) < 3:
        logger.warning("The EOL data in %s isn't up-to-date.", EOLDATA_FILE)
    if len(supported_branches) < 2:
        logger.critical("The EOL data in %s is outdated and we cannot reliably run this script.", EOLDATA_FILE)
        return 1

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        cve_affected_ranges = await collect_cve_versions(session)
    releases_data = fetch_k8s_releases_data()

    try:
        logger.info(
            f"""Initiating scan on the Kubernetes cluster specified by kubeconfig at {config.kubeconfig}
            with context {config.context if config.context else ''}.
            Fetching cluster information and verifying access.""")
        await get_k8s_cluster_info(config.kubeconfig, config.context)
        await get_images_and_scan(config.kubeconfig, config.context)

    except CriticalException as e:
        logger.critical(e)
        logger.debug("Exception info", exc_info=True)
        return 1

    try:
        context_desc = f"context '{config.context}'" if config.context else "default context"
        logger.info("Checking cluster specified by %s in %s.", context_desc, config.kubeconfig)
        cluster = await get_k8s_cluster_info(config.kubeconfig, config.context)
        cluster_branch = cluster.version.branch

        if cluster_branch not in supported_branches:
            logger.error("The K8s cluster version %s of cluster '%s' is already EOL.", cluster.version, cluster.name)
        elif check_k8s_version_recency(cluster.version, releases_data, cve_affected_ranges):
            logger.info(
                "The K8s cluster version %s of cluster '%s' is still in the recency time window.",
                cluster.version,
                cluster.name,
            )
        else:
            logger.error(
                "The K8s cluster version %s of cluster '%s' is outdated according to the standard.",
                cluster.version,
                cluster.name,
            )

        for affected_range in cve_affected_ranges:
            if cluster.version in affected_range:
                logger.error(
                    "The K8s cluster version %s of cluster '%s' is an outdated version with a possible CRITICAL CVE.",
                    cluster.version,
                    cluster.name,
                )
    except BaseException as e:
        logger.critical("%s", e)
        logger.debug("Exception info", exc_info=True)
        return 1

    c = counting_handler.bylevel
    logger.debug(
        "Total error / warning: "
        f"{c[logging.ERROR]} / {c[logging.WARNING]}"
    )
    if not c[logging.CRITICAL]:
        print("version-policy-check: " + ('PASS', 'FAIL')[min(1, c[logging.ERROR])])
    return min(127, c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
