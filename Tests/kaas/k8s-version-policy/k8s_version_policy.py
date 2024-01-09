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

The K8s clusters provided in a kubeconfig are checked. The kubeconfig
must provide connection details for the clusters to be tested via
the contexts "stable", "oldstable", "oldoldstable" and "oldoldoldstable",
depending on how many upstream K8s releases are currently supported.
It is determined if the version on these clusters is still inside
the recency window, which is determined by the standard to be 4 months
for minor versions (for the stable cluster) and 1 week for patch versions.
An exception are versions with critical CVEs, which should be replaced on
a shorter notice.

(c) Hannes Baum <hannes.baum@cloudandheat.com>, 6/2023
(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 2/2024
License: CC-BY-SA 4.0
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import asyncio
import contextlib
import getopt
import kubernetes_asyncio
import logging
import logging.config
import re
import requests
import sys
import yaml


MINOR_VERSION_CADENCE = timedelta(days=120)
PATCH_VERSION_CADENCE = timedelta(weeks=1)
CVE_VERSION_CADENCE = timedelta(days=3)
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


class Config:
    config_path = "./config.yaml"
    kubeconfig = None
    logging = None


def print_usage():
    print("""
K8s Version Policy Compliance Check

Usage: k8s_version_policy.py [-h] [-c|--config PATH/TO/CONFIG] -k|--kubeconfig PATH/TO/KUBECONFIG

The K8s version policy check returns 0 if the versions of the tested clusters are still acceptable, otherwise
it returns 2 for an out-of date version or 3 if the used version should be updated due to a highly critical CVE.
It returns 4 if a supported upstream K8s release is missing.

    -c/--config PATH/TO/CONFIG         - Path to the config file of the test script
    -k/--kubeconfig PATH/TO/KUBECONFIG - Path to the kubeconfig of the server we want to check
    -h                                 - Output help
""")


def parse_arguments(argv):
    """Parse cli arguments from the script call"""
    config = Config()

    try:
        opts, args = getopt.gnu_getopt(argv, "c:k:h", ["config=", "kubeconfig=", "help"])
    except getopt.GetoptError:
        raise ConfigException

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            raise HelpException
        if opt[0] == "-c" or opt[0] == "--config":
            config.config_path = opt[1]
        if opt[0] == "-k" or opt[0] == "--kubeconfig":
            config.kubeconfig = opt[1]

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

    try:
        with open(config.config_path, "r") as f:
            config.logging = yaml.safe_load(f)['logging']
    except OSError:
        logger.warning(f"The config file under {config.config_path} couldn't be found, "
                       f"falling back to the default config.")
    finally:
        # Setup logging if the config file with the relevant information could be loaded before
        # Otherwise, we initialize logging with the included literal
        setup_logging(config.logging or logging_config)

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


def parse_version(version_str: str) -> K8sVersion:
    cleansed = version_str.removeprefix("v").strip()
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


def parse_github_release_data(release_data: dict) -> K8sRelease:
    version = parse_version(release_data["tag_name"].split("-")[0])
    released_at = datetime.strptime(release_data["published_at"], "%Y-%m-%dT%H:%M:%SZ")
    return K8sRelease(version, released_at)


@dataclass(frozen=True, eq=True)
class VersionRange:
    """Version range with a lower and upper bound."""

    # First version with the CVE; this value will be set if either an affected
    # version is directly set in a CVE dataset or if the CVE dataset is in a
    # non-standard format.  If the variable is set, `lower_version` and
    # `upper_version` create a range of affected versions.
    lower_version: K8sVersion

    # Last version with the CVE
    upper_version: K8sVersion

    # True if upper_version is included in the range of affected versions
    inclusive: bool = False

    def __contains__(self, version: K8sVersion) -> bool:
        # See the following link for more information about the format
        # https://www.cve.org/AllResources/CveServices#cve-json-5

        # Check if an `upper version` exists
        if self.upper_version:
            # Check if a `lower version` exists and compare the version against it
            if self.lower_version:
                gt = self.lower_version <= version
            else:
                gt = True
            # Compare the version either with `less than` or `less than or equal` against the `upper version`
            if self.inclusive:
                return gt and self.upper_version >= version
            return gt and self.upper_version > version
        else:
            # If no upper version exists, we only need to check if the version is equal to the `lower version`
            return self.lower_version == version


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


def check_k8s_version_recency(my_version: K8sVersion, cve_version_list=None, allow_older=False) -> bool:
    """Check a given K8s cluster version against the list of released versions in order to find out, if the version
    is an accepted recent version according to the standard."""
    if cve_version_list is None:
        cve_version_list = list()

    github_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Request the latest 100 releases (the next are not needed, since these versions are too old)
    releases_data = requests.get(
        "https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=100",
        headers=github_headers,
    ).json()

    for release_data in releases_data:
        if release_data['draft'] or release_data['prerelease']:
            continue

        release = parse_github_release_data(release_data)

        # Check if the minor version is recent, but allow older versions if requested
        # FIXME: this assumes k8s stays in 1.x version schema :(
        if release.version.minor >= my_version.minor and not allow_older:
            if release.age > MINOR_VERSION_CADENCE:
                return False

        if my_version.branch == release.version.branch and my_version.patch < release.version.patch:
            if release.age > PATCH_VERSION_CADENCE:
                return False

            if release.version in cve_version_list and release.age > CVE_VERSION_CADENCE:
                return False

        if release.version.minor == (my_version.minor + 1) and release.version.patch == 0:
            break

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

    contexts = ["stable", "oldstable", "oldoldstable", "oldoldoldstable"]
    seen_branches = set()

    try:
        for context in contexts:
            logger.info("Checking cluster of kubeconfig context '%s'.", context)
            cluster = await get_k8s_cluster_info(config.kubeconfig, context)
            cluster_branch = cluster.version.branch
            seen_branches.add(cluster_branch)

            # allow older k8s branches, but not for the first context (stable)
            allow_older = context != contexts[0]

            if check_k8s_version_recency(cluster.version, cve_affected_ranges, allow_older):
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

            if branch_infos[cluster_branch.previous()].is_eol():
                logger.info("Skipping the next context because the cluster it should reference is already EOL.")
                break
    except BaseException as e:
        logger.critical("%s", e)
        logger.debug("Exception info", exc_info=True)
        return 1

    # Now check if we saw all upstream supported K8s branches. Keep in mind
    # that providers have a cadence time to update the "stable" context to the
    # newest K8s release branch. The corresponding window was already checked
    # above.
    expected_branches = set(supported_branches)
    newest_branch = max(supported_branches)
    newest_branch_seen = max(seen_branches)
    if newest_branch != newest_branch_seen:
        expected_branches.remove(newest_branch)

    missing = expected_branches - seen_branches
    if missing:
        listing = " ".join(f"{branch}" for branch in missing)
        logger.error("The following upstream branches should be supported but were missing: %s", listing)

    c = counting_handler.bylevel
    logger.debug(
        "Total error / warning: "
        f"{c[logging.ERROR]} / {c[logging.WARNING]}"
    )
    return min(127, c[logging.ERROR])  # cap at 127 due to OS restrictions


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)