from .plugin_kind import PluginKind
from .plugin_static import PluginStatic


def init_plugin(plugin_kind, config=None):
    if plugin_kind == "static":
        plugin = PluginStatic(config)

    elif plugin_kind == "kind":
        plugin = PluginKind(config)

    else:
        raise ValueError(f"unknown plugin '{plugin_kind}'")

    return plugin


def run_plugin_create(plugin_kind, cluster_id, k8s_version, kubeconfig_filepath):
    plugin = init_plugin(plugin_kind)
    kubeconfig = plugin.create(cluster_id, k8s_version, kubeconfig_filepath)
    return kubeconfig


def run_plugin_delete(plugin_kind, cluster_id):
    plugin = init_plugin(plugin_kind)
    kubeconfig = plugin.delete(cluster_id)
    return kubeconfig
