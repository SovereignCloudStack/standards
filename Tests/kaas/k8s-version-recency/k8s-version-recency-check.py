#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""
K8s Version Recency Checker
https://github.com/SovereignCloudStack/standards

Return codes:
0: Version is inside the recency window
1: Error during script execution
2: Version isn't inside the recency windows anymore
3: Version used contains a critical CVE

One or more K8s clusters are checked by providing their kubeconfigs.
It is determined, if the version on these clusters is still inside
the recency window, which is determined by the Standard to be 4 months
for minor versions and 1 week for patch versions. An exception are
versions with critical CVEs, which should be replaced on a shorter notice.

(c) Hannes Baum <hannes.baum@cloudandheat.com>, 6/2023
License: CC-BY-SA 4.0
"""

import aiohttp
import asyncio
import datetime
from dateutil import relativedelta
import getopt
import kubernetes_asyncio
import logging
import logging.config
import re
import requests
import sys
import yaml


MAJOR_VERSION_CADENCE = None
MINOR_VERSION_CADENCE_MONTHS = 4
PATCH_VERSION_CADENCE_WEEKS = 1
CVE_VERSION_CADENCE_DAYS = 3
CVE_SEVERITY = 8  # CRITICAL

logging_config = {
    "level": "INFO",
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "k8s-version-recency-check": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "k8s-version-recency-check",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "handlers": ["console"]
    }
}

logger = logging.getLogger(__name__)


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
K8s Version Recency Compliance Check

Usage: k8s-version-recency-check.py [-h] [-c|--config PATH/TO/CONFIG] -k|--kubeconfig PATH/TO/KUBECONFIG

The K8s version recency check returns 0 if the version of the tested cluster is still acceptable, otherwise
it returns 2 for an out-of date version or 3 if the used version should be updated due to a highly critical CVE.

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


class K8sVersionInfo:
    """Class that contains a k8s version info.

    Attributes:
        major (int): Major version of the k8s version
        minor (int): Minor version of the k8s version
        patch (int): Patch version of the k8s version
        date (datetime): release date of the k8s version
    """
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

        self.date = None

    def __eq__(self, other):
        if not isinstance(other, K8sVersionInfo):
            raise TypeError
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __gt__(self, other):
        if not isinstance(other, K8sVersionInfo):
            raise TypeError
        patchcomp = self.minor == other.minor and self.patch > other.patch
        return self.major > other.major or (self.major == other.major and (self.minor > other.minor or patchcomp))

    def __ge__(self, other):
        if not isinstance(other, K8sVersionInfo):
            raise TypeError
        patchcomp = self.minor == other.minor and self.patch >= other.patch
        return self.major > other.major or (self.major == other.major and (self.minor > other.minor or patchcomp))

    def __lt__(self, other):
        if not isinstance(other, K8sVersionInfo):
            raise TypeError
        patchcomp = self.minor == other.minor and self.patch < other.patch
        return self.major < other.major or (self.major == other.major and (self.minor < other.minor or patchcomp))

    def __le__(self, other):
        if not isinstance(other, K8sVersionInfo):
            raise TypeError
        patchcomp = self.minor == other.minor and self.patch <= other.patch
        return self.major < other.major or (self.major == other.major and (self.minor < other.minor or patchcomp))

    @classmethod
    def extract_version(cls, string, separator=".", strip=None):
        if strip is None:
            strip = ["v"]
        for s in strip:
            string = string.strip(s)
        components = string.strip().split(separator)
        return cls(int(components[0]), int(components[1]), int(components[2]))

    def check_for_version(self, major=None, minor=None, patch=None):
        """Check if a version or part of the version is equal to the given version numbers"""
        return (major is None or self.major == major) and \
               (minor is None or self.minor == minor) and \
               (patch is None or self.patch == patch)

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


class CVEVersionInfo:
    """Class that contains a CVE version info.

    Attributes:
        upper_version (K8sVersionInfo): Last version with the CVE
        lower_version (K8sVersionInfo): First version with the CVE; this value will be set if either an affected version
            is directly set in a CVE dataset or if the CVE dataset is in a non-standard format.
            If the variable is set, `lower_version` and `upper_version` create a range of affected versions.
        equal (bool): check if the version is equal to the `upper_version`, (less than is always checked, since the
            format is build like this)
    """
    def __init__(self, lower_version, upper_version, equal=False):
        self.lower_version = lower_version
        self.upper_version = upper_version

        self.equal = equal

    def __eq__(self, other):
        if not isinstance(other, CVEVersionInfo):
            raise TypeError
        return self.lower_version == other.lower_version and \
            self.upper_version == other.upper_version and \
            self.equal == self.equal

    def is_version_affected(self, version_info):
        # See the following link for more information about the format
        # https://www.cve.org/AllResources/CveServices#cve-json-5

        # Check if an `upper version` exists
        if self.upper_version:
            # Check if a `lower version` exists and compare the version against it
            if self.lower_version:
                gt = self.lower_version <= version_info
            else:
                gt = True
            # Compare the version either with `less than` or `less than or equal` against the `upper version`
            if self.equal:
                return gt and self.upper_version >= version_info
            return gt and self.upper_version > version_info
        else:
            # If no upper version exists, we only need to check if the version is equal to the `lower version`
            return self.lower_version == version_info


def diff_months(date1, date2):
    r = relativedelta.relativedelta(date2, date1)
    return r.months + (12 * r.years)


def diff_weeks(date1, date2):
    delta = date1 - date2
    return abs(delta.days / 7)


def diff_days(date1, date2):
    delta = date1 - date2
    return abs(delta.days)


async def request_cve_data(session: aiohttp.ClientSession, cveid: str) -> dict:
    """Request for a single CVE data item."""
    async with session.get(
        f"https://cveawg.mitre.org/api/cve/{cveid}",
        headers={"Accept": "application/json"}
    ) as resp:
        return await resp.json()


def parse_cve_version_information(cve_version_info):
    """Parse the CVE version information according to their CVE JSON 5.0 schema"""
    vi_lower_version = None
    vi_upper_version = None
    equal = False

    # Extract the version if it is viable, but it's not a requirement
    try:
        vi_lower_version = K8sVersionInfo.extract_version(cve_version_info['version'])
    except ValueError:
        pass

    if 'lessThanOrEqual' in cve_version_info:
        vi_upper_version = K8sVersionInfo.extract_version(cve_version_info['lessThanOrEqual'])
        equal = True
    elif 'lessThan' in cve_version_info:
        vi_upper_version = K8sVersionInfo.extract_version(cve_version_info['lessThan'])

    # This shouldn't happen, but if it happens, we look for non-standard descriptions
    # According to this(https://www.cve.org/AllResources/CveServices#cve-json-5),
    # this isn't how the data should be described
    if vi_lower_version is None and vi_upper_version is None:
        if re.search(r'v?\d+.\d+.x', cve_version_info['version']):
            vdata = cve_version_info['version'].strip("v").split(".")
            vi_lower_version = K8sVersionInfo(vdata[0], vdata[1], 0)
            vi_upper_version = K8sVersionInfo(vdata[0], vdata[1], 0)

        if re.search(r'v?\d+.\d+.\d+\s+-\s+v?\d+.\d+.\d+', cve_version_info['version']):
            vdata = cve_version_info['version'].split("-")
            vi_lower_version = K8sVersionInfo.extract_version(vdata[0])
            vi_upper_version = K8sVersionInfo.extract_version(vdata[1])

    return CVEVersionInfo(vi_lower_version, vi_upper_version, equal)


async def collect_cve_versions(session: aiohttp.ClientSession):
    """Get all relevant CVE versions, that are relevant for the test according to the severity
    dictated by the Standard.
    """

    # CVE fix versions
    cfvs = list()

    # Request latest version
    async with session.get(
        "https://kubernetes.io/docs/reference/issues-security/official-cve-feed/index.json",
        headers={"Accept": "application/json"}
    ) as resp:
        cve_list = await resp.json()

    tasks = [request_cve_data(session=session, cveid=cve['external_url'].split("=")[-1])
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
        except KeyError as e:
            logger.debug(
                f"They key {e} couldn't be found in the CVE json data for CVE "
                f"{cve_data.get('cveMetadata', {}).get('cveId', '<ID NOT SET>')}."
            )
            continue

        is_high_severity = any(
            re.search(r'[cC][vV][sS]{1,2}V\d', metric_key) and metric_value['baseScore'] >= CVE_SEVERITY
            for cve_metric in cve_metrics
            for metric_key, metric_value in cve_metric.items()
        )

        if is_high_severity:
            affected_kubernetes_versions = [
                parse_cve_version_information(version_info)
                for aff in cve_affected
                if aff['product'] == "Kubernetes"
                for version_info in aff['versions']
                if version_info['status'] == "affected"
            ]
            for cvev in affected_kubernetes_versions:
                try:
                    if cvev not in cfvs:
                        cfvs.append(cvev)
                except TypeError:
                    pass

    return cfvs


async def get_k8s_cluster_version(kubeconfig):
    """Get the k8s version of the cluster under test."""
    cluster_config = await kubernetes_asyncio.config.load_kube_config(kubeconfig)

    async with kubernetes_asyncio.client.ApiClient() as api:
        version_api = kubernetes_asyncio.client.VersionApi(api)
        ret = await version_api.get_code()

        version = K8sVersionInfo.extract_version(ret.git_version)
        version.date = datetime.datetime.strptime(ret.build_date, '%Y-%m-%dT%H:%M:%SZ')

        return version, cluster_config.current_context['name']


def check_k8s_version_recency(version, cve_version_list=None):
    """Check a given K8s cluster version against the list of released versions in order to find out, if the version
    is an accepted recent version according to the standard."""
    if cve_version_list is None:
        cve_version_list = list()

    github_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Request the latest 100 version (the next are not needed, since these versions are too old)
    response = requests.get("https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=100",
                            headers=github_headers).json()

    for r in response:
        v = K8sVersionInfo.extract_version(r['tag_name'].split("-")[0])
        v.date = datetime.datetime.strptime(r['published_at'], '%Y-%m-%dT%H:%M:%SZ')

        if r['draft'] or r['prerelease']:
            continue

        # Check if the version is recent
        if v.minor >= version.minor:
            if diff_months(v.date, datetime.datetime.now()) >= MINOR_VERSION_CADENCE_MONTHS:
                return False

        if version.check_for_version(major=v.major, minor=v.minor) and version.patch < v.patch:
            if diff_weeks(datetime.datetime.now(), v.date) >= PATCH_VERSION_CADENCE_WEEKS:
                return False

            if v in cve_version_list and \
               diff_days(datetime.datetime.now(), v.date) >= CVE_VERSION_CADENCE_DAYS:
                return False

        if v.minor == (version.minor + 1) and v.patch == 0:
            break

    return True


async def main(argv):
    try:
        config = initialize_config(parse_arguments(argv))
    except (OSError, ConfigException, HelpException) as e:
        if hasattr(e, 'message'):
            logger.error(e.message)
        print_usage()
        return 1

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        cve_versions = await collect_cve_versions(session)
    cluster_version, cluster_name = await get_k8s_cluster_version(config.kubeconfig)

    if check_k8s_version_recency(cluster_version, cve_versions):
        logger.info("The K8s cluster version %s of cluster '%s' is still in the recency time window." %
                    (str(cluster_version), cluster_name))
        return 0

    for cvev in cve_versions:
        try:
            if cvev.is_version_affected(cluster_version):
                logger.error("The K8s cluster version %s of cluster '%s' is an outdated version "
                             "with a possible CRITICAL CVE." % (str(cluster_version), cluster_name))
                return 3
        except TypeError as e:
            logger.error(f"An error occurred during CVE check: {e}")

    logger.error("The K8s cluster version %s of cluster '%s' is outdated according to the Standard." %
                 (str(cluster_version), cluster_name))
    return 2


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
