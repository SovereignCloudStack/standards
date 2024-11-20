#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
"""
K8s Node Distribution Check
https://github.com/SovereignCloudStack/standards

Return codes:
0: Node distribution according to standard
1: Help command used
2: Node distribution either not according to standard or not detected due to missing labels

One or more K8s clusters are checked by providing their kubeconfigs.
scs-0214-v1 requires a K8s cluster to be distributed over multiple
physical machines within different failure zones of an infrastructure.
For now, this is hard to test, since we would need to know a multitude
of things about the providers infrastructure, including things like
circuitry and physical distribution of different machines.
This test is for now only designed to work on the K8s layer, which is
done by checking several well-known labels (https://kubernetes.io/docs/reference/labels-annotations-taints/)
and comparing them. This doesn't always attest to a good distribution
and does require these labels to be set, but should yield overall pretty
good initial results.

    topology.kubernetes.io/zone
    topology.kubernetes.io/region
    node-role.kubernetes.io/control-plane

(c) Hannes Baum <hannes.baum@cloudandheat.com>, 6/2023
(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 4/2024
License: CC-BY-SA 4.0
"""

import asyncio
import getopt
import kubernetes_asyncio
import logging
import logging.config
import sys

# It is important to note, that the order of these labels matters for this test.
# Since we want to check if nodes are distributed, we want to do this from bigger
# infrastructure parts to smaller ones. So we first look if nodes are distributed
# across regions, then zones and then hosts. If one of these requirements is fulfilled,
# we don't need to check anymore, since a distribution was already detected.
LABELS = (
    "topology.kubernetes.io/region",
    "topology.kubernetes.io/zone",
)

logger = logging.getLogger(__name__)


class ConfigException(BaseException):
    """Exception raised if a configuration error occurs"""


class HelpException(BaseException):
    """Exception raised if the help functionality is called"""


class DistributionException(BaseException):
    """Exception raised if the distribution seems to be not enough"""


class LabelException(BaseException):
    """Exception raised if a label isn't set"""


class Config:
    kubeconfig = None


def print_usage():
    print("""
K8s Node Distribution Compliance Check

Usage: k8s-node-distribution-check.py [-h] [-c|--config PATH/TO/CONFIG] -k|--kubeconfig PATH/TO/KUBECONFIG

The script is used to determine the compliance with the SCS standard SCS-0214-v1 describing the distribution
and availability of K8s nodes.

The following return values are possible:
    0 - Distribution according to the standard could be verified.
    1 - The help output was delivered.
    2 - No distribution according to the standard could be detected for the nodes available.

The following arguments can be set:
    -k/--kubeconfig PATH/TO/KUBECONFIG - Path to the kubeconfig of the server we want to check
    -h                                 - Output help
""")


def parse_arguments(argv):
    """Parse cli arguments from the script call"""
    config = Config()

    try:
        opts, args = getopt.gnu_getopt(argv, "k:t:h", ["kubeconfig=", "test=", "help"])
    except getopt.GetoptError:
        raise ConfigException

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            raise HelpException
        if opt[0] == "-k" or opt[0] == "--kubeconfig":
            config.kubeconfig = opt[1]

    return config


def initialize_config(config):
    """Initialize the configuration for the test script"""

    if config.kubeconfig is None:
        raise ConfigException("A kubeconfig needs to be set in order to test a k8s cluster version.")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    return config


async def get_k8s_cluster_labelled_nodes(kubeconfig, interesting_labels):
    """Get the labels per node of the k8s cluster under test, ignoring labels we don't need."""
    await kubernetes_asyncio.config.load_kube_config(kubeconfig)

    nodes = list()

    async with kubernetes_asyncio.client.ApiClient() as api:
        core_api = kubernetes_asyncio.client.CoreV1Api(api)
        result = await core_api.list_node()
        for node in result.items:
            filtered_labels = {
                label: value
                for label, value in node.metadata.labels.items()
                if label in interesting_labels
            }
            nodes.append(filtered_labels)

    return nodes


def compare_labels(node_list, node_type="control"):

    label_data = {key: list() for key in LABELS}

    for node in node_list:
        for key in LABELS:
            try:
                label_data[key].append(node[key])
            except KeyError:
                raise LabelException(f"The label for {key.split('/')[1]}s doesn't seem to be set for all nodes.")

    for label in LABELS:
        if len(set(label_data[label])) <= 1:
            logger.warning(f"There seems to be no distribution across multiple {label.split('/')[1]}s "
                           "or labels aren't set correctly across nodes.")
        else:
            logger.info(
                f"The {node_type} nodes are distributed across "
                f"{str(len(set(label_data[label])))} {label.split('/')[1]}s."
            )
            return

    if node_type == "control":
        raise DistributionException("The distribution of nodes described in the standard couldn't be detected.")
    elif node_type == "worker":
        logger.warning("No node distribution could be detected for the worker nodes. "
                       "This produces only a warning, since it is just a recommendation.")
        return


def check_nodes(nodes):
    if len(nodes) < 2:
        logger.error("The tested cluster only contains a single node, which can't comply with the standard.")
        return 2

    labelled_control_nodes = [node for node in nodes if "node-role.kubernetes.io/control-plane" in node]
    try:
        if len(labelled_control_nodes) >= 1:
            worker_nodes = [node for node in nodes if "node-role.kubernetes.io/control-plane" not in node]
            # Compare the labels of both types, since we have enough of them with labels
            compare_labels(labelled_control_nodes, "control")
            compare_labels(worker_nodes, "worker")
        else:
            compare_labels(nodes)
    except (DistributionException, LabelException) as e:
        logger.error(str(e))
        return 2

    return 0


async def main(argv):
    try:
        config = initialize_config(parse_arguments(argv))
    except (OSError, ConfigException, HelpException) as e:
        logger.critical("%s", e)
        print_usage()
        return 1

    try:
        nodes = await get_k8s_cluster_labelled_nodes(
            config.kubeconfig,
            LABELS + ("node-role.kubernetes.io/control-plane", )
        )
    except BaseException as e:
        logger.critical("%s", e)
        return 1

    return_code = check_nodes(nodes)
    print("node-distribution-check: " + ('PASS', 'FAIL')[min(1, return_code)])
    return return_code


if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
