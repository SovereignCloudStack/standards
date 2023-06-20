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
import getopt
import kubernetes_asyncio
import logging
import logging.config
import math
import re
import requests
import sys
import yaml


MAJOR_VERSION_CADENCE = None
MINOR_VERSION_CADENCE = 4  # months
PATCH_VERSION_CADENCE = 1  # week
CVE_VERSION_CADENCE = 3  # days
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

logger = logging.getLogger("k8s-version-recency-check")


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

Usage: k8s-version-recency-check.py [-h] [-k|--kubeconfig PATH/TO/KUBECONFIG]

The K8s version recency check returns 0 if the version of the tested cluster is still acceptable, otherwise
it returns 1 for an out-of-date minor version, 2 for an out-of-date patch level version or 3 if the currently
used version should be updated due to a highly critical CVE.

    -c/--config PATH/TOCONFIG          - Path to the config file of the test script
    -k/--kubeconfig PATH/TO/KUBECONFIG - Path to the kubeconfig of the server we want to check
    -h                                 - Output help
    """)


def parse_arguments(argv):
    """Parse cli arguments from the script call"""
    config = Config()

    try:
        opts, args = getopt.gnu_getopt(argv, "c:k:h", ["config", "kubeconfig", "help"])
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

    if not config.kubeconfig:
        print("A kubeconfig needs to be set in order to test a k8s cluster version.")
        raise ConfigException

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
            return False
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __gt__(self, other):
        if not isinstance(other, K8sVersionInfo):
            return False
        patchcomp = self.minor == other.minor and self.patch > other.patch
        return self.major > other.major or (self.major == other.major and (self.minor > other.minor or patchcomp))

    def __ge__(self, other):
        if not isinstance(other, K8sVersionInfo):
            return False
        patchcomp = self.minor == other.minor and self.patch >= other.patch
        return self.major > other.major or (self.major == other.major and (self.minor > other.minor or patchcomp))

    def __lt__(self, other):
        if not isinstance(other, K8sVersionInfo):
            return False
        patchcomp = self.minor == other.minor and self.patch < other.patch
        return self.major < other.major or (self.major == other.major and (self.minor < other.minor or patchcomp))

    def __le__(self, other):
        if not isinstance(other, K8sVersionInfo):
            return False
        patchcomp = self.minor == other.minor and self.patch <= other.patch
        return self.major < other.major or (self.major == other.major and (self.minor < other.minor or patchcomp))

    @classmethod
    def extract_version(cls, string, separator="."):
        components = string.strip().split(separator)
        return cls(int(components[0]), int(components[1]), int(components[2]))

    def check_for_version(self, major=None, minor=None, patch=None):
        return (major is None or self.major == major) and \
               (minor is None or self.minor == minor) and \
               (patch is None or self.patch == patch)

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


class CVEVersionInfo:
    def __init__(self, lower_version, upper_version, less_than=False, equal=False):
        self.lower_version = lower_version
        self.upper_version = upper_version

        self.less_than = less_than
        self.equal = equal

    def __eq__(self, other):
        if not isinstance(other, CVEVersionInfo):
            return False
        return self.lower_version == other.lower_version and self.upper_version == other.upper_version and \
            self.less_than == other.less_than and self.equal == self.equal

    def is_version_affected(self, version_info):
        if self.upper_version:
            if self.lower_version:
                gt = self.lower_version <= version_info
            else:
                gt = True
            if self.less_than:
                if self.equal:
                    return gt and self.upper_version >= version_info
                return gt and self.upper_version > version_info
        else:
            return self.lower_version == version_info


def diff_months(date1, date2):
    return abs((date1.year - date2.year) * 12 + date1.month - date2.month)


def diff_weeks(date1, date2):
    day1 = (date1 - datetime.timedelta(days=date1.weekday()))
    day2 = (date2 - datetime.timedelta(days=date2.weekday()))
    diff = day2 - day1
    return abs((diff.days / 7) + math.ceil(diff.seconds / 86400))


def diff_days(date1, date2):
    delta = date1 - date2
    return abs(delta.days)


async def request_cve_data(session: aiohttp.ClientSession, cveid: str) -> dict:
    """Request for a single CVE data item."""
    resp = await session.request('GET', f"https://cveawg.mitre.org/api/cve/{cveid}",
                                 headers={"Accept": "application/json"})
    return await resp.json()


def parse_cve_version_information(cve_version_info):
    """Parse the CVE version information according to their CVE JSON 5.0 schema"""
    vi_lower_version = None
    vi_upper_version = None
    less_than = False
    equal = False

    # Extract the version if it is viable, but it's not a requirement
    try:
        vi_lower_version = K8sVersionInfo().extract_version(cve_version_info['version'].strip("v"))
    except ValueError:
        pass

    if 'lessThanOrEqual' in cve_version_info:
        vi_upper_version = K8sVersionInfo().extract_version(cve_version_info['lessThanOrEqual'].strip("v"))
        vi_upper_version.patch += 1
        less_than = True
        equal = True
    elif 'lessThan' in cve_version_info:
        vi_upper_version = K8sVersionInfo().extract_version(cve_version_info['lessThan'].strip("v"))
        less_than = True

    # This shouldn't happen, but if it happens, we look for non-standard descriptions
    # According to this(https://www.cve.org/AllResources/CveServices#cve-json-5),
    # this isn't how the data should be described
    if not vi_lower_version and not vi_upper_version:
        if re.search(r'v?\d+.\d+.x', cve_version_info['version']):
            vdata = cve_version_info['version'].strip("v").split(".")
            vi_lower_version = K8sVersionInfo(vdata[0], vdata[1], 0)
            vi_upper_version = K8sVersionInfo(vdata[0], int(vdata[1])+1, 0)

        if re.search(r'v?\d+.\d+.\d+\s+-\s+v?\d+.\d+.\d+', cve_version_info['version']):
            vdata = cve_version_info['version'].split("-")
            vi_lower_version = K8sVersionInfo().extract_version(vdata[0].strip("v"))
            vi_upper_version = K8sVersionInfo().extract_version(vdata[1].strip("v"))

    return CVEVersionInfo(vi_lower_version, vi_upper_version, less_than, equal)


async def collect_cve_versions():
    """Get all relevant CVE versions, that are relevant for the test according to the severity
    dictated by the Standard.
    """

    # CVE fix versions
    cfvs = list()

    # Request latest version
    cve_list = requests.get("https://kubernetes.io/docs/reference/issues-security/official-cve-feed/index.json",
                            headers={"Accept": "application/json"}).json()

    async with aiohttp.ClientSession() as session:
        tasks = []
        for cve in cve_list['items']:
            cveid = cve['external_url'].split("=")[-1]
            tasks.append(request_cve_data(session=session, cveid=cveid))
        # asyncio.gather() will wait on the entire task set to be
        # completed.  If you want to process results greedily as they come in,
        # loop over asyncio.as_completed()
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
            logger.debug(f"They key {e} couldn't be found in the CVE json data for CVE {cveid}.")
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
                if cvev not in cfvs:
                    cfvs.append(cvev)

    return cfvs


async def get_k8s_cluster_version(kubeconfig):
    """Get the k8s version of the cluster under test."""
    cluster_config = await kubernetes_asyncio.config.load_kube_config(kubeconfig)

    async with kubernetes_asyncio.client.ApiClient() as api:
        version_api = kubernetes_asyncio.client.VersionApi(api)
        ret = await version_api.get_code()

        version = K8sVersionInfo.extract_version(ret.git_version.strip("v"))
        version.date = datetime.datetime.strptime(ret.build_date, '%Y-%m-%dT%H:%M:%SZ')

        return version, cluster_config.current_context['name']


def is_current_version(version, k8s_version_list, cve_version_list=[]):
    """Filter the versions depending on the usage times set by the Standard and
    the times set for CVE versions.
    """
    try:
        if diff_months(version.date, datetime.datetime.now()) >= MINOR_VERSION_CADENCE:
            return False

        for kv in k8s_version_list:
            if version.check_for_version(major=kv.major, minor=kv.minor) and \
               version.patch < kv.patch:

                if diff_weeks(datetime.datetime.now(), kv.date) >= PATCH_VERSION_CADENCE:
                    return False

                if kv in cve_version_list and \
                   diff_days(datetime.datetime.now(), kv.date) >= CVE_VERSION_CADENCE:
                    return False
    except (KeyError, IndexError, TypeError) as e:
        logger.debug(f"An error occurred during version filtering: {e}")
        return False
    else:
        return True


def collect_accepted_k8s_versions(cve_version_list=[]):
    """Collect a list of k8s versions that comply to the cadence time set by the standard"""

    k8s_versions = []

    github_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Request latest version
    resp = requests.get("https://api.github.com/repos/kubernetes/kubernetes/releases/latest",
                        headers=github_headers).json()

    # Latest version
    lv = K8sVersionInfo.extract_version(resp['tag_name'].strip("v"))
    lv.date = datetime.datetime.strptime(resp['published_at'], '%Y-%m-%dT%H:%M:%SZ')

    # Request the latest 100 version (the next are not needed, since these versions are too old)
    response = requests.get("https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=100",
                            headers=github_headers).json()

    # Iterate all versions until the first patch of the previous latest version
    for r in response:
        v = K8sVersionInfo.extract_version(r['tag_name'].split("-")[0].strip("v"))
        v.date = datetime.datetime.strptime(r['published_at'], '%Y-%m-%dT%H:%M:%SZ')

        if not r['draft'] and not r['prerelease']:
            k8s_versions.append(v)

        # Stop adding new version if the version we added is the previous latest minor versions first patch,
        # since it is most of the time around 3-6 months until a new version comes out or an old one goes into EOL
        if v.check_for_version(lv.major, (lv.minor-1), 0):
            break

    return [v for v in k8s_versions if is_current_version(v, k8s_versions, cve_version_list)]


async def main(argv):
    try:
        config = initialize_config(parse_arguments(argv))
    except (OSError, ConfigException, HelpException):
        print_usage()
        return 1

    cve_versions = await collect_cve_versions()
    k8s_versions = collect_accepted_k8s_versions(cve_versions)
    cluster_version, cluster_name = await get_k8s_cluster_version(config.kubeconfig)

    for k8sv in k8s_versions:
        if k8sv == cluster_version:
            logger.info("The K8s cluster version %s of cluster '%s' is still in the recency time window." %
                        (str(cluster_version), cluster_name))
            return 0

    for cvev in cve_versions:
        if cvev.is_version_affected(cluster_version):
            logger.error("The K8s cluster version %s of cluster '%s' is an outdated version "
                         "with a possible CRITICAL CVE." % (str(cluster_version), cluster_name))
            return 3

    logger.error("The K8s cluster version %s of cluster '%s' is outdated according to the Standard." %
                 (str(cluster_version), cluster_name))
    return 2


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
