import os

from web3 import Web3

from .custom_types import ChainConfig, ChainId, EnvEnum

ENVIRONMENT = EnvEnum(os.environ["ENV"])

if ENVIRONMENT == EnvEnum.PROD:
    ZEX_BASE_URL = "https://api.zex.finance/v1"

    CHAINS_CONFIG = {
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
else:
    ZEX_BASE_URL = "https://api-dev.zex.finance/v1"
    CHAINS_CONFIG = {
        137: ChainConfig(
            private_rpc=os.environ["POL_RPC"],
            chain_id=ChainId(137),
            symbol="POL",
            finalize_block_count=20,
            poa=True,
            delay=1,
            batch_block_size=20,
            vault_address=Web3.to_checksum_address(
                "0xcb00C4e20F84aE691C9739e4E202eaCafD187e8d"
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
                "0xcb00C4e20F84aE691C9739e4E202eaCafD187e8d"
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
                "0x17a8bC4724666738387Ef5Fc59F7EF835AF60979"
            ),
        ),
    }

ZEX_ENCODE_VERSION = 1

USER_DEPOSIT_FACTORY_ADDRESS = os.environ["USER_DEPOSIT_FACTORY_ADDRESS"]
USER_DEPOSIT_BYTECODE_HASH = os.environ["USER_DEPOSIT_BYTECODE_HASH"]
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")

SA_SHIELD_PRIVATE_KEY = os.environ["SA_SHIELD_PRIVATE_KEY"]

DKG_JSON_PATH = os.getenv("DKG_JSON_PATH", "./zexporta/dkgs/dkgs.json")
DKG_NAME = os.getenv("DKG_NAME", "ethereum")

WITHDRAWER_PRIVATE_KEY = os.environ["WITHDRAWER_PRIVATE_KEY"]

SENTRY_DNS = os.getenv("SENTRY_DNS")
