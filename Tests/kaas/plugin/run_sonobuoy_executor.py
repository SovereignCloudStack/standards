#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#

from sonobuoy_executor import SonobuoyExecutor
import logging
import getopt
import sys
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sonobuoy_executor")

#TODO:!!! move this to class file
def parse_arguments(argv):
    """Parse cli arguments from the script call"""
    try:
        opts, args = getopt.gnu_getopt(argv, "k:t:h", ["kubeconfig=", "test=", "help"])
    except getopt.GetoptError:
        raise ConfigException

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            raise HelpException
        if opt[0] == "-k" or opt[0] == "--kubeconfig":
            kubeconfig = opt[1]

    return kubeconfig


if __name__ == "__main__":
    logger.info("read in kubeconfig")
    kubeconfig_path = parse_arguments(sys.argv)
    logger.info("Run sonobuoy_executor")
    sonobuoy_executor = SonobuoyExecutor(kubeconfig_path)
    sonobuoy_executor.run()
