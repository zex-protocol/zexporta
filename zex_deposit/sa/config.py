import os

from dotenv import load_dotenv
from eth_typing import ChainId
from web3 import Web3

from zex_deposit.custom_types import ChainConfig

load_dotenv()

LOGGER_PATH = "/var/log/sa/"


USER_DEPOSIT_FACTORY_ADDRESS = os.environ["USER_DEPOSIT_FACTORY_ADDRESS"]
USER_DEPOSIT_BYTECODE_HASH = os.environ["USER_DEPOSIT_BYTECODE_HASH"]
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("BATCH_BLOCK_NUMBER_SIZE", 5))
MAX_DELAY_PER_BLOCK_BATCH = int(os.getenv("MAX_DELAY_PER_BLOCK_BATCH", 3))

DKG_JSON_PATH = os.getenv("DKG_JSON_PATH", "./zex_deposit/dkgs/dkgs.json")
DKG_NAME = os.getenv("DKG_NAME", "ethereum")

CHAINS_CONFIG = {
    # 42161: ChainConfig(
    #     private_rpc=os.environ["ARB_RPC"],
    #     chain_id=ChainId(42161),
    #     from_block=273078242,
    #     symbol="ARB",
    #     finalize_block_count=30,
    #     delay=1,
    #     batch_block_size=20,
    # ),
    137: ChainConfig(
        private_rpc=os.environ["POL_RPC"],
        chain_id=ChainId(137),
        symbol="POL",
        finalize_block_count=20,
        poa=True,
        delay=1,
        batch_block_size=20,
        vault_address=Web3.to_checksum_address(
            "0xc3D07c4FDE03b8B1F9FeE3C19d906681b7b66B82"
        ),
    ),
    10: ChainConfig(
        private_rpc=os.environ["OP_RPC"],
        chain_id=ChainId(10),
        symbol="OPT",
        finalize_block_count=10,
        poa=True,
        delay=1,
        batch_block_size=20,
        vault_address=Web3.to_checksum_address(
            "0xBa4e58D407F2D304f4d4eb476DECe5D9304D9c0E"
        ),
    ),
    56: ChainConfig(
        private_rpc=os.environ["BSC_RPC"],
        chain_id=ChainId(56),
        symbol="BSC",
        finalize_block_count=10,
        poa=True,
        delay=1,
        batch_block_size=30,
        vault_address=Web3.to_checksum_address(
            "0xc3D07c4FDE03b8B1F9FeE3C19d906681b7b66B82"
        ),
    ),
}

SA_DELAY_SECOND = 10
ZEX_ENCODE_VERSION = 1
SA_TIMEOUT = 200
SA_BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("SA_BATCH_BLOCK_NUMBER_SIZE", 100))
WITHDRAWER_PRIVATE_KEY = os.environ["WITHDRAWER_PRIVATE_KEY"]
SA_SHIELD_PRIVATE_KEY = (
    "0xdc1349a720a14a08858984d312f4921135f5eb683a49a75ef7a8be17d995b3d9"
)
