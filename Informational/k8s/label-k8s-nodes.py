
import asyncio
import kubernetes_asyncio
import sys

HOST = "HOST"
ZONE = "ZONE"
REGION = "REGION"


async def main(argv):

    set_labels = (
        "topology.kubernetes.io/region",
        "topology.kubernetes.io/zone",
        "topology.scs.community/host-id",
    )

    await kubernetes_asyncio.config.load_kube_config(argv[0])

    async with (kubernetes_asyncio.client.ApiClient() as api):
        core_api = kubernetes_asyncio.client.CoreV1Api(api)
        result = await core_api.list_node()
        for node in result.items:
            labels = {
                label: value
                for label, value in node.metadata.labels.items()
            }
            for sl in set_labels:
                temp = ""
                if sl == "topology.kubernetes.io/region":
                    try:
                        temp = labels["topology.cinder.csi.openstack.org/region"]
                    except KeyError:
                        temp = REGION
                if sl == "topology.kubernetes.io/zone":
                    try:
                        temp = labels["topology.cinder.csi.openstack.org/zone"]
                    except KeyError:
                        temp = ZONE
                if sl == "topology.scs.community/host-id":
                    try:
                        temp = labels["kubernetes.io/hostname"]
                    except KeyError:
                        temp = HOST
                node.metadata.labels[sl] = temp
            result = await core_api.patch_node(node.metadata.name, node)
            print(result.metadata.labels)

    return 0

if __name__ == "__main__":
    return_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(return_code)
