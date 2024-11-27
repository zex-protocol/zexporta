import os
import threading
import time
import requests
from urllib.parse import urlparse

from pyfrost.network.abstract import NodesInfo as BaseNodeInfo

from ._dummy_node_info import dummy_node_info


class NodesInfo(BaseNodeInfo):
    @property
    def prefix(self):
        return "/pyfrost/"

    subgraph_url = (
        "https://api.studio.thegraph.com/query/85556/bls_apk_registry/version/latest"
    )

    def __init__(self):
        self.nodes = {}
        self._stop_event = threading.Event()
        self.sync_with_subgraph()
        self.start_sync_thread()

    def sync_with_subgraph(self):
        query = """
        query MyQuery {
          operators(where: {registered: true}) {
            id
            operatorId
            pubkeyG1_X
            pubkeyG1_Y
            pubkeyG2_X
            pubkeyG2_Y
            socket
            stake
          }
        }
        """
        if os.getenv("ENVIRONMENT", "dev") == "dev":
            self.nodes = self._convert_operators_to_nodes(
                dummy_node_info.get("data", {}).get("operators", [])
            )
            return
        try:
            response = requests.post(self.subgraph_url, json={"query": query})
            if response.status_code == 200:
                data = response.json()
                operators = data.get("data", {}).get("operators", [])
                self.nodes = self._convert_operators_to_nodes(operators)
                print("Synced with subgraph successfully.")
            else:
                print(
                    f"Failed to fetch data from subgraph. Status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

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

    def _sync_periodically(self, interval):
        while not self._stop_event.is_set():
            self.sync_with_subgraph()
            time.sleep(interval)

    def start_sync_thread(self):
        sync_interval = 60  # 1 minute
        self._sync_thread = threading.Thread(
            target=self._sync_periodically, args=(sync_interval,)
        )
        self._sync_thread.daemon = True
        self._sync_thread.start()

    def stop_sync_thread(self):
        self._stop_event.set()
        self._sync_thread.join()

    def lookup_node(self, node_id: str | None = None):
        return self.nodes.get(node_id, {})

    def get_all_nodes(self, n: int | None = None):
        if n is None:
            n = len(self.nodes)
        return list(self.nodes.keys())[:n]
