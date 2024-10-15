import argparse

from plugin_kind import PluginKind
from plugin_static import PluginStatic
from plugin_cluster_stacks import PluginClusterStacks


def init_plugin(plugin_kind, config=None):
    if plugin_kind == "static":
        plugin = PluginStatic(config)

    elif plugin_kind == "kind":
        plugin = PluginKind(config)

    elif plugin_kind == "cluster-stacks":
        plugin = PluginClusterStacks(config)

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

# Todo: Can be removed after it will be done differently, only for dev purposes for now :)
# Add a main function to handle the command-line interface
def main():
    parser = argparse.ArgumentParser(description="Manage Kubernetes clusters with plugins")
    
    # Subcommands: create or delete
    subparsers = parser.add_subparsers(dest='command', help='create or delete a cluster')

    # Arguments for the 'create' command
    create_parser = subparsers.add_parser('create', help='Create a Kubernetes cluster')
    create_parser.add_argument('plugin_kind', choices=['static', 'kind', 'cluster-stacks'], help="The type of plugin to use")
    create_parser.add_argument('cluster_id', help="The ID of the cluster to create")
    create_parser.add_argument('k8s_version', help="The Kubernetes version to use for the cluster")
    create_parser.add_argument('kubeconfig_filepath', help="The path to save the kubeconfig file")

    # Arguments for the 'delete' command
    delete_parser = subparsers.add_parser('delete', help='Delete a Kubernetes cluster')
    delete_parser.add_argument('plugin_kind', choices=['static', 'kind', 'cluster-stacks'], help="The type of plugin to use")
    delete_parser.add_argument('cluster_id', help="The ID of the cluster to delete")

    args = parser.parse_args()

    if args.command == 'create':
        # Run the create cluster logic
        kubeconfig = run_plugin_create(args.plugin_kind, args.cluster_id, args.k8s_version, args.kubeconfig_filepath)
        print(f"Cluster created successfully. Kubeconfig saved at: {kubeconfig}")
    
    elif args.command == 'delete':
        # Run the delete cluster logic
        kubeconfig = run_plugin_delete(args.plugin_kind, args.cluster_id)
        print(f"Cluster {args.cluster_id} deleted successfully.")
    
    else:
        print("Invalid command. Use 'create' or 'delete'.")

if __name__ == "__main__":
    main()