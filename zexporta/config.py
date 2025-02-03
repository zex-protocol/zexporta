import os

from bitcoinutils.setup import setup
from web3 import Web3

from .custom_types import (
    BTCConfig,
    ChainConfig,
    ChainId,
    ChainSymbol,
    EnvEnum,
    EVMConfig,
)

ENVIRONMENT = EnvEnum(os.environ["ENV"])

if ENVIRONMENT == EnvEnum.PROD:
    ZEX_BASE_URL = "https://api.zex.finance/v1"
    SEQUENCER_BASE_URL = ""
    SEQUENCER_APP_NAME = ""

    CHAINS_CONFIG: dict[str, ChainConfig] = {
        ChainSymbol.POL.value: EVMConfig(
            private_rpc=os.environ["POL_RPC"],
            chain_symbol=ChainSymbol.POL,
            finalize_block_count=20,
            poa=True,
            delay=1,
            batch_block_size=20,
            vault_address=Web3.to_checksum_address(
                "0xc3D07c4FDE03b8B1F9FeE3C19d906681b7b66B82"
            ),
            chain_id=ChainId(137),
        ),
        ChainSymbol.OPT.value: EVMConfig(
            private_rpc=os.environ["OP_RPC"],
            chain_symbol=ChainSymbol.OPT,
            finalize_block_count=10,
            poa=True,
            delay=1,
            batch_block_size=20,
            vault_address=Web3.to_checksum_address(
                "0xBa4e58D407F2D304f4d4eb476DECe5D9304D9c0E"
            ),
            chain_id=ChainId(10),
        ),
        ChainSymbol.BSC.value: EVMConfig(
            private_rpc=os.environ["BSC_RPC"],
            chain_symbol=ChainSymbol.BSC,
            finalize_block_count=10,
            poa=True,
            delay=1,
            batch_block_size=30,
            vault_address=Web3.to_checksum_address(
                "0xc3D07c4FDE03b8B1F9FeE3C19d906681b7b66B82"
            ),
            chain_id=ChainId(56),
        ),
        ChainSymbol.BTC.value: BTCConfig(
            private_rpc=os.environ["BTC_RPC"],
            private_indexer_rpc=os.environ["BTC_INDEXER"],
            chain_symbol=ChainSymbol.BTC,
            finalize_block_count=6,
            delay=10,
            batch_block_size=0,
            vault_address="",
        ),
    }
    setup("mainnet")

else:
    ZEX_BASE_URL = "https://api-dev.zex.finance/v1"
    SEQUENCER_BASE_URL = ""
    SEQUENCER_APP_NAME = ""

    CHAINS_CONFIG: dict[str, ChainConfig] = {
        ChainSymbol.HOL.value: EVMConfig(
            private_rpc=os.environ["HOL_RPC"],
            chain_symbol=ChainSymbol.HOL,
            finalize_block_count=1,
            delay=1,
            batch_block_size=20,
            vault_address=Web3.to_checksum_address(
                "0x17a8bC4724666738387Ef5Fc59F7EF835AF60979"
            ),
            chain_id=ChainId(17000),
        ),
        ChainSymbol.SEP.value: EVMConfig(
            private_rpc=os.environ["SEP_RPC"],
            chain_symbol=ChainSymbol.SEP,
            finalize_block_count=1,
            poa=True,
            delay=1,
            batch_block_size=20,
            vault_address=Web3.to_checksum_address(
                "0x17a8bC4724666738387Ef5Fc59F7EF835AF60979"
            ),
            chain_id=ChainId(11155111),
        ),
        ChainSymbol.BST.value: EVMConfig(
            private_rpc=os.environ["BST_RPC"],
            chain_symbol=ChainSymbol.BST,
            finalize_block_count=1,
            poa=True,
            delay=1,
            batch_block_size=30,
            vault_address=Web3.to_checksum_address(
                "0x17a8bC4724666738387Ef5Fc59F7EF835AF60979"
            ),
            chain_id=ChainId(97),
        ),
        ChainSymbol.BTC.value: BTCConfig(
            private_rpc=os.environ["BTC_RPC"],
            private_indexer_rpc=os.environ["BTC_INDEXER"],
            chain_symbol=ChainSymbol.BTC,
            finalize_block_count=6,
            delay=10,
            batch_block_size=0,
            vault_address="",
        ),
    }
    setup("testnet")


ZEX_ENCODE_VERSION = 1

BTC_GROUP_KEY_PUB = os.getenv("BTC_GROUP_KEY_PUB")

USER_DEPOSIT_FACTORY_ADDRESS = os.environ["USER_DEPOSIT_FACTORY_ADDRESS"]
USER_DEPOSIT_BYTECODE_HASH = os.environ["USER_DEPOSIT_BYTECODE_HASH"]
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")

SA_SHIELD_PRIVATE_KEY = os.environ["SA_SHIELD_PRIVATE_KEY"]

DKG_JSON_PATH = os.getenv("DKG_JSON_PATH", "./zexporta/dkgs/dkgs.json")
DKG_NAME = os.getenv("DKG_NAME", "ethereum")

EVM_WITHDRAWER_PRIVATE_KEY = os.environ["EVM_WITHDRAWER_PRIVATE_KEY"]
BTC_WITHDRAWER_PRIVATE_KEY = os.environ["BTC_WITHDRAWER_PRIVATE_KEY"]

SENTRY_DNS = os.getenv("SENTRY_DNS")
