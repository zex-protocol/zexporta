import os

from eth_typing import ChainId
from web3 import Web3

from zex_deposit.custom_types import ChainConfig

LOGGER_PATH = "/var/log/validator/validator.log"

VALIDATED_IPS = {
    "104.194.145.26": [
        "/pyfrost/v1/dkg/round1",
        "/pyfrost/v1/dkg/round2",
        "/pyfrost/v1/dkg/round3",
        "/pyfrost/v1/sign",
        "/pyfrost/v1/generate-nonces",
    ],
    "172.20.0.1": [
        "/pyfrost/v1/dkg/round1",
        "/pyfrost/v1/dkg/round2",
        "/pyfrost/v1/dkg/round3",
        "/pyfrost/v1/sign",
        "/pyfrost/v1/generate-nonces",
    ],
}

PRIVATE_KEY = int(os.environ["NODE_PRIVATE_KEY"])

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

ZEX_ENCODE_VERSION = 1
