import logging.config
import os

from flask import Flask
from pyfrost.network.node import Node

from zex_deposit.utils.logger import get_logger_config
from zex_deposit.utils.node_info import NodesInfo

from .config import LOGGER_PATH, PRIVATE_KEY
from .node_data_manager import NodeDataManager
from .node_validator import NodeValidators

logging.config.dictConfig(get_logger_config(LOGGER_PATH))


app = Flask(__name__)


def run_node(node_id: int) -> None:
    data_manager = NodeDataManager(
        f"./zex_deposit/data/dkg_keys-{node_id}.json",
    )
    nodes_info = NodesInfo()
    node = Node(
        data_manager,
        str(node_id),  # type: ignore
        PRIVATE_KEY,
        nodes_info,
        NodeValidators.caller_validator,  # type: ignore
        NodeValidators.data_validator,  # type: ignore
    )
    # node_info = nodes_info.lookup_node(str(node_id))
    app.register_blueprint(node.blueprint, url_prefix="/pyfrost")


run_node(int(os.environ["NODE_ID"], 16))
