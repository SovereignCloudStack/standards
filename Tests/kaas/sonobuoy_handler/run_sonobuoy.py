#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
import logging
import sys

import click

from sonobuoy_handler import SonobuoyHandler

logger = logging.getLogger(__name__)


@click.command()
@click.option("-k", "--kubeconfig", "kubeconfig", required=True, type=click.Path(exists=True), help="path/to/kubeconfig_file.yaml",)
@click.option("-r", "--result_dir_name", "result_dir_name", type=str, default="sonobuoy_results", help="directory name to store results at",)
@click.option("-c", "--check", "check_name", type=str, default="sonobuoy_executor", help="this MUST be the same name as the id in 'scs-compatible-kaas.yaml'",)
@click.option("-a", "--arg", "args", multiple=True)
def sonobuoy_run(kubeconfig, result_dir_name, check_name, args):
    logger.info("Run sonobuoy_executor")
    sonobuoy_handler = SonobuoyHandler(check_name, kubeconfig, result_dir_name, args)
    return_code = sonobuoy_handler.run()
    sys.exit(return_code)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    sonobuoy_run()
