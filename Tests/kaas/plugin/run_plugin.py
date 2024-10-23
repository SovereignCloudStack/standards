#!/usr/bin/env python3
import logging
import os.path

import click
import yaml

from plugin_kind import PluginKind
from plugin_static import PluginStatic


PLUGIN_LOOKUP = {
  "kind": PluginKind,
  "static": PluginStatic,
}


def init_plugin(plugin_kind, config=None):
    plugin_maker = PLUGIN_LOOKUP.get(plugin_kind)
    if plugin_maker is None:
        raise ValueError(f"unknown plugin '{plugin_kind}'")
    return plugin_maker(config)


def run_plugin_create(plugin_kind, clusterspec):
    plugin = init_plugin(plugin_kind)
    for cluster_id, cluster_info in clusterspec.items():
        plugin.create(cluster_id, cluster_info['branch'], os.path.abspath(cluster_info['kubeconfig']))


def run_plugin_delete(plugin_kind, clusterspec):
    plugin = init_plugin(plugin_kind)
    for cluster_id in clusterspec:
        plugin.delete(cluster_id)


def load_spec(clusterspec_path):
    with open(clusterspec_path, "rb") as fileobj:
        return yaml.load(fileobj, Loader=yaml.SafeLoader)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('plugin_kind', type=click.Choice(list(PLUGIN_LOOKUP), case_sensitive=False))
@click.argument('clusterspec_path', type=click.Path(exists=True, dir_okay=False))
def create(plugin_kind, clusterspec_path):
    clusterspec = load_spec(clusterspec_path)['clusters']
    run_plugin_create(plugin_kind, clusterspec)


@cli.command()
@click.argument('plugin_kind', type=click.Choice(list(PLUGIN_LOOKUP), case_sensitive=False))
@click.argument('clusterspec_path', type=click.Path(exists=True, dir_okay=False))
def delete(plugin_kind, clusterspec_path):
    clusterspec = load_spec(clusterspec_path)['clusters']
    run_plugin_delete(plugin_kind, clusterspec)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli()
