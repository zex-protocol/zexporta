import threading
from urllib.parse import urlparse

from pyfrost.network.abstract import NodesInfo as BaseNodeInfo

from zexporta.config import ENVIRONMENT
from zexporta.custom_types import EnvEnum

if ENVIRONMENT == EnvEnum.PROD:
    from ._dummy_node_info import dummy_node_info

else:
    from ._dev_node_info import dummy_node_info


class NodesInfo(BaseNodeInfo):
    @property
    def prefix(self):  # type: ignore
        return "/pyfrost/"

    def __init__(self):
        self._stop_event = threading.Event()
        self.nodes = self._convert_operators_to_nodes(dummy_node_info.get("data", {}).get("operators", []))

    def _convert_operators_to_nodes(self, operators):
        nodes = {}
        for operator in operators:
            parsed_url = urlparse(operator["socket"])
            node_info = {
                "public_key": operator["id"],
                "pubkeyG1_X": operator["pubkeyG1_X"],
                "pubkeyG1_Y": operator["pubkeyG1_Y"],
                "pubkeyG2_X": operator["pubkeyG2_X"],
                "pubkeyG2_Y": operator["pubkeyG2_Y"],
                "socket": operator["socket"],
                "stake": operator["stake"],
                "host": parsed_url.hostname,
                "port": parsed_url.port,
            }
            nodes[str(int(operator["operatorId"], 16))] = node_info
        return nodes

    def lookup_node(self, node_id: str | None = None):
        return self.nodes.get(node_id, {})

    def get_all_nodes(self, n: int | None = None):
        if n is None:
            n = len(self.nodes)
        return list(self.nodes.keys())[:n]
