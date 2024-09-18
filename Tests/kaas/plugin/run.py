from plugin_kind import PluginKind
from plugin_static import PluginStatic
import os

if __name__ == "__main__":

    match os.environ['CLUSTER_PROVIDER']:
        case "static":
            plugin = PluginStatic()
        case "kind":
            plugin = PluginKind()
        case _:
            raise NotImplementedError(f"{os.environ['CLUSTER_PROVIDER']} is not valid ")

    plugin.run()
