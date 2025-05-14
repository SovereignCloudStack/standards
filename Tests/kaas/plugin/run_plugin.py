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


def load_config(path=None):
    if path:
        with open(path, "rb") as fileobj:
            cfg = yaml.load(fileobj, Loader=yaml.SafeLoader)
        if not isinstance(cfg, dict):
            raise RuntimeError('clusters.yaml must be a YAML dict')
        if 'clusters' not in cfg or not isinstance(cfg['clusters'], dict):
            raise RuntimeError('clusters.yaml must be a YAML dict, and so must be .clusters')
        return cfg
    path = os.path.join(os.path.expanduser('~'), '.config', 'scs', 'clusters.yaml')
    if os.path.exists(path):
        return load_config(path)
    raise FileNotFoundError('config')


def init_plugin(plugin_kind, config):
    plugin_maker = PLUGIN_LOOKUP.get(plugin_kind)
    if plugin_maker is None:
        raise ValueError(f"unknown plugin '{plugin_kind}'")
    return plugin_maker(config)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('cluster_id', type=str, default="default")
@cli.pass_obj
def create(cfg, cluster_id):
    spec = cfg[cluster_id]
    config = spec['config']
    config['name'] = cluster_id
    init_plugin(spec['kind'], config).create_cluster()


@cli.command()
@click.argument('cluster_id', type=str, default="default")
@cli.pass_obj
def delete(cfg, cluster_id):
    spec = cfg[cluster_id]
    config = spec['config']
    config['name'] = cluster_id
    init_plugin(spec['kind'], config).delete_cluster()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli(obj=load_config())
