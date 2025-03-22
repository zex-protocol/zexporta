import logging
import logging.config
import os

import sentry_sdk
from flask import Flask
from pyfrost.network.node import Node

from zexporta.utils.logger import get_logger_config
from zexporta.utils.node_info import NodesInfo

from .config import LOGGER_PATH, PRIVATE_KEY, SENTRY_DNS
from .node_data_manager import NodeDataManager
from .node_validator import NodeValidators

app = Flask(__name__)

sentry_sdk.init(
    dsn=SENTRY_DNS,
)


def run_node(node_id: int) -> None:
    data_manager = NodeDataManager(
        f"./zexporta/data/dkg_keys-{node_id}.json",
    )
    nodes_info = NodesInfo()
    node = Node(
        data_manager,
        str(node_id),  # type: ignore
        PRIVATE_KEY,  # type: ignore
        nodes_info,
        NodeValidators.caller_validator,  # type: ignore
        NodeValidators.data_validator,  # type: ignore
    )
    logging.config.dictConfig(get_logger_config(LOGGER_PATH))
    app.register_blueprint(node.blueprint, url_prefix="/pyfrost")


run_node(int(os.environ["NODE_ID"], 16))
