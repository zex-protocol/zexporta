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
    # 42161: ChainConfig(
    #     private_rpc=os.environ["ARB_RPC"],
    #     chain_id=ChainId(42161),
    #     from_block=273078242,
    #     symbol="ARB",
    #     finalize_block_count=30,
    #     delay=0.1,
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
            "0x4ba18Af73e7E39636cD647b6c6A7E6D6a9086e6c"
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
            "0x4ba18Af73e7E39636cD647b6c6A7E6D6a9086e6c"
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
            "0x701E471BFaBeb55a5d5b864ACeD49fE745d530c2"
        ),
    ),
}


ZEX_ENCODE_VERSION = 1
