import sys

from pyfrost.network.node import Node
from flask import Flask

from utils.node_info import NodesInfo
from .node_data_manager import NodeDataManager
from .node_validator import NodeValidators
from .config import PRIVATE_KEY


def run_node(node_id: int) -> None:
    data_manager = NodeDataManager(
        f"./data/dkg_keys-{node_id}.json",
        f"./data/nonces-{node_id}.json",
    )
    nodes_info = NodesInfo()
    node = Node(
        data_manager,
        str(node_id),
        PRIVATE_KEY,
        nodes_info,
        NodeValidators.caller_validator,
        NodeValidators.data_validator,
    )
    node_info = nodes_info.lookup_node(str(node_id))
    app = Flask(__name__)
    app.register_blueprint(node.blueprint, url_prefix="/pyfrost")
    app.run(host=node_info["host"], port=int(node_info["port"]), debug=True)

if __name__  == "__main__":
    run_node(int(sys.argv[1], 16))