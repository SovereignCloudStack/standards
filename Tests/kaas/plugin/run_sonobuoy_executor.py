#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#

from sonobuoy_executor import SonobuoyExecutor
import sys
import click
import logging

logging_config = {
    "level": "INFO",
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "sonobuoy_logs": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "sonobuoy_logs",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "handlers": ["console"]
    }
}


logger = logging.getLogger(__name__)


@click.command()
@click.option('-k', '--kubeconfig', 'kubeconfig', type=click.Path(exists=False), default=None, help='path/to/kubeconfig_file.yaml')
@click.option('-r', '--result_dir_name', 'result_dir_name', type=str, default="sonobuoy_results", help='directory name to store results at')
@click.option('-c', '--check', 'check_name', type=str, default="sonobuoy_executor", help='name of the check to p')  # TODO:!!! this should be eighter 'scs-kaas-tests' or 'cncf-conformance'
@click.option('--debug/--no-debug', default=False)  # TODO: Not Yet Implemented
def sonobuoy_run(kubeconfig, result_dir_name, check_name, debug):
    logger.info("Run sonobuoy_executor")
    sonobuoy_executor = SonobuoyExecutor(check_name, kubeconfig, result_dir_name)
    return_code = sonobuoy_executor.run()
    sys.exit(return_code)


if __name__ == "__main__":
    sonobuoy_run()
