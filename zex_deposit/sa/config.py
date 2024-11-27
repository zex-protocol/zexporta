import os

from dotenv import load_dotenv
from eth_typing import ChainId

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
    42161: ChainConfig(
        private_rpc=os.environ["ARB_RPC"],
        chain_id=ChainId(42161),
        from_block=273078242,
        symbol="ARB",
        finalize_block_count=30,
        delay=0.1,
        batch_block_size=30,
    ),
    137: ChainConfig(
        private_rpc=os.environ["POL_RPC"],
        chain_id=ChainId(137),
        from_block=64122219,
        symbol="POL",
        finalize_block_count=20,
        poa=True,
        delay=1,
        batch_block_size=30,
    ),
    56: ChainConfig(
        private_rpc=os.environ["BSC_RPC"],
        chain_id=ChainId(56),
        from_block=43892677,
        symbol="BSC",
        finalize_block_count=10,
        poa=True,
        delay=1,
        batch_block_size=30,
    ),
}

SA_DELAY_SECOND = 10
ZEX_ENCODE_VERSION = 1
SA_TIMEOUT = 200
SA_BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("SA_BATCH_BLOCK_NUMBER_SIZE", 100))
VAULT_ADDRESS = "0x27E9Fc4a68D0b1D26030D7973a6EEdf52Ac425b9"
WITHDRAWER_PRIVATE_KEY = os.environ["WITHDRAWER_PRIVATE_KEY"]
