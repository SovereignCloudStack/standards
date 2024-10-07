#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#

from plugin_kind import PluginKind
from plugin_static import PluginStatic
import os
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("interface")

if __name__ == "__main__":

    logger.info("Select provider plugin")
    match os.environ['CLUSTER_PROVIDER']:
        case "static":
            plugin = PluginStatic()
        case "kind":
            plugin = PluginKind()
        case _:
            logger.error("provider plugin not implemented")
            raise NotImplementedError(f"{os.environ['CLUSTER_PROVIDER']} is not valid ")

    logger.info("Run plugin")
    plugin.run()
