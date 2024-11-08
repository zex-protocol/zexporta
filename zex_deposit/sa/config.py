import os
from enum import Enum

from dotenv import load_dotenv
from eth_typing import ChainId

from zex_deposit.custom_types import ChainConfig

load_dotenv()

LOGGER_PATH = "/var/log/sa/"


class ZexPath(Enum):
    LATEST_USER_URL = "users/latest-id"


ZEX_BASE_URL = "https://zex.idealmoney.io/api/v1"

INFURA_KEY = os.environ["INFURA_KEY"]
USER_DEPOSIT_FACTORY_ADDRESS = os.environ["USER_DEPOSIT_FACTORY_ADDRESS"]
USER_DEPOSIT_BYTECODE_HASH = os.environ["USER_DEPOSIT_BYTECODE_HASH"]
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("BATCH_BLOCK_NUMBER_SIZE", 5))
MAX_DELAY_PER_BLOCK_BATCH = int(os.getenv("MAX_DELAY_PER_BLOCK_BATCH", 3))

DKG_JSON_PATH = os.getenv("DKG_JSON_PATH", "./zex_deposit/dkgs/dkgs.json")
DKG_NAME = os.getenv("DKG_NAME", "ethereum")

CHAINS_CONFIG = {
    11155111: ChainConfig(
        private_rpc="https://ethereum-sepolia-rpc.publicnode.com",
        chain_id=ChainId(11155111),
        from_block=6995672,
        symbol="SEP",
    ),
    17000: ChainConfig(
        private_rpc="https://holesky.drpc.org",
        chain_id=ChainId(17000),
        from_block=2691362,
        symbol="HOL",
    ),
    97: ChainConfig(
        private_rpc="https://bsc-testnet-rpc.publicnode.com",
        chain_id=ChainId(97),
        from_block=2691362,
        symbol="BST",
    ),
}

SA_DELAY_SECOND = 10
ZEX_ENCODE_VERSION = 1
SA_TIMEOUT = 200
SA_BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("SA_BATCH_BLOCK_NUMBER_SIZE", 100))
