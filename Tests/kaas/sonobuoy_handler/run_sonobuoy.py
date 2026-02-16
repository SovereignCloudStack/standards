#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
import logging
import sys

import click

from sonobuoy_handler import SonobuoyHandler, check_sonobuoy_result

logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command("run")
@click.option("-k", "--kubeconfig", "kubeconfig", required=True, type=click.Path(exists=True), help="path/to/kubeconfig_file.yaml",)
@click.option("-r", "--result_dir_name", "result_dir_name", type=str, default="sonobuoy_results", help="directory name to store results at",)
@click.option("-c", "--check", "check_name", type=str, default="sonobuoy_executor", help="this MUST be the same name as the id in 'scs-compatible-kaas.yaml'",)
@click.option("--scs-sonobuoy-config", "scs_sonobuoy_config_yaml", type=click.Path(exists=True), default="kaas/sonobuoy-config.yaml", help="Configuration for Sonobuoy (yaml format)")
@click.option("-a", "--arg", "args", multiple=True)
def sonobuoy_run(kubeconfig, result_dir_name, check_name, scs_sonobuoy_config_yaml, args):
    sonobuoy_handler = SonobuoyHandler(check_name, kubeconfig, result_dir_name, scs_sonobuoy_config_yaml, args)
    sys.exit(sonobuoy_handler.run())


@cli.command("check-results")
@click.option("--scs-sonobuoy-config", "scs_sonobuoy_config_yaml", type=click.Path(exists=True), default="kaas/scs-sonobuoy-config.yaml", help="Configuration for Sonobuoy (yaml format)")
@click.argument("sonobuoy_result_yaml", type=click.Path(exists=True))
def check_results(scs_sonobuoy_config_yaml, sonobuoy_result_yaml):
    check_sonobuoy_result(scs_sonobuoy_config_yaml, sonobuoy_result_yaml)
    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    cli()
