#!/usr/bin/env python3
import logging
import os.path

import click
import yaml

from plugin_kind import PluginKind
from plugin_static import PluginStatic
from plugin_cluster_stacks import PluginClusterStacks

PLUGIN_LOOKUP = {
    "kind": PluginKind,
    "static": PluginStatic,
    "cluster-stacks": PluginClusterStacks,
}


def init_plugin(plugin_kind, config_path):
    plugin_maker = PLUGIN_LOOKUP.get(plugin_kind)
    if plugin_maker is None:
        raise ValueError(f"unknown plugin '{plugin_kind}'")
    return plugin_maker(config_path)


def load_spec(clusterspec_path):
    with open(clusterspec_path, "rb") as fileobj:
        return yaml.load(fileobj, Loader=yaml.SafeLoader)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('plugin_kind', type=click.Choice(list(PLUGIN_LOOKUP), case_sensitive=False))
@click.argument('plugin_config', type=click.Path(exists=True, dir_okay=False))
@click.argument('clusterspec_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('cluster_id', type=str, default="default")
def create(plugin_kind, plugin_config, clusterspec_path, cluster_id):
    clusterspec = load_spec(clusterspec_path)['clusters']
    plugin = init_plugin(plugin_kind, plugin_config)
    clusterinfo = clusterspec[cluster_id]
    plugin.create_cluster(cluster_id, clusterinfo['branch'], os.path.abspath(clusterinfo['kubeconfig']))


@cli.command()
@click.argument('plugin_kind', type=click.Choice(list(PLUGIN_LOOKUP), case_sensitive=False))
@click.argument('plugin_config', type=click.Path(exists=True, dir_okay=False))
@click.argument('clusterspec_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('cluster_id', type=str, default="default")
def delete(plugin_kind, plugin_config, clusterspec_path, cluster_id):
    clusterspec = load_spec(clusterspec_path)['clusters']
    clusterinfo = clusterspec[cluster_id]
    plugin = init_plugin(plugin_kind, plugin_config)
    plugin.delete_cluster(cluster_id, os.path.abspath(clusterinfo['kubeconfig']))


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli()
