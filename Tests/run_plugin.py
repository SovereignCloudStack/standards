#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-test-runner.py
#
# (c) Toni Finger <Toni.Finger@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0

from kaas.plugin.plugin_kind import PluginKind
from kaas.plugin.plugin_static import PluginStatic
import click
import sys


def init_plugin(plugin_kind, config=None):
    if plugin_kind == "static":
        plugin = PluginStatic(config)

    elif plugin_kind == "kind":
        plugin = PluginKind(config)

    else:
        raise ValueError(f"unknown plugin '{plugin_kind}'")

    return plugin


@click.group()
@click.pass_obj
def cli(cfg):
    pass


@cli.result_callback()
def process_pipeline(rc, *args, **kwargs):
    sys.exit(rc)


@cli.command()
@click.option('--plugin', 'plugin', type=str, default="kind", help='type of the plugin to be used')
@click.option('--clusterid', 'cluster_id', type=str, default=None, help='Id or name of the cluster to be identified for the deletion process')
@click.option('--version', 'k8s_version', type=str, default=None, help='Kubernetes version of the cluster to create')
@click.option('--kubeconfig', 'kubeconfig_filepath', type=click.Path(exists=False), default="./kubeconfig.yaml", help='path/to/kubeconfig_file.yaml')
@click.option('--config', 'config', type=str, default=None, help='k8s cluster provisioner specific configuration')
@click.pass_obj
def create(cfg, plugin, cluster_id, k8s_version, kubeconfig_filepath, config):
    plugin = init_plugin(plugin, config)
    plugin.create(cluster_id, k8s_version, kubeconfig_filepath)
    return 0


@cli.command()
@click.option('--plugin', 'plugin', type=str, default="kind", help='type of the plugin to be used')
@click.option('--clusterid', 'cluster_id', type=str, default="", help='Id or name of the cluster to be identified for the deletion process')
@click.pass_obj
def delete(cfg, plugin, cluster_id):
    plugin = init_plugin(plugin)
    plugin.delete(cluster_id)
    return 0


if __name__ == '__main__':
    cli()
