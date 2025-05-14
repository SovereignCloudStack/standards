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
BASEPATH = os.path.join(os.path.expanduser('~'), '.config', 'scs')


def load_config(path='clusters.yaml'):
    if not os.path.isabs(path):
        return load_config(os.path.normpath(os.path.join(BASEPATH, path)))
    if not os.path.exists(path):
        raise FileNotFoundError()
    with open(path, "rb") as fileobj:
        cfg = yaml.load(fileobj, Loader=yaml.SafeLoader)
    if not isinstance(cfg, dict):
        raise RuntimeError('clusters.yaml must be a YAML dict')
    if 'clusters' not in cfg or not isinstance(cfg['clusters'], dict):
        raise RuntimeError('clusters.yaml must be a YAML dict, and so must be .clusters')
    return cfg


def init_plugin(plugin_kind, config):
    plugin_maker = PLUGIN_LOOKUP.get(plugin_kind)
    if plugin_maker is None:
        raise ValueError(f"unknown plugin '{plugin_kind}'")
    return plugin_maker(config, basepath=BASEPATH)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('cluster_id', type=str, default="default")
@click.pass_obj
def create(cfg, cluster_id):
    spec = cfg['clusters'][cluster_id]
    config = spec['config']
    config['name'] = cluster_id
    kubeconfig_path = os.path.abspath(os.path.join(cluster_id, 'kubeconfig.yaml'))
    init_plugin(spec['kind'], config).create_cluster(kubeconfig_path)


@cli.command()
@click.argument('cluster_id', type=str, default="default")
@click.pass_obj
def delete(cfg, cluster_id):
    spec = cfg['clusters'][cluster_id]
    config = spec['config']
    config['name'] = cluster_id
    init_plugin(spec['kind'], config).delete_cluster()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli(obj=load_config())
