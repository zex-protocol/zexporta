import os

from eth_typing import ChainId

from zex_deposit.custom_types import ChainConfig

BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("BATCH_BLOCK_NUMBER_SIZE", 10))
MAX_DELAY_PER_BLOCK_BATCH = 2
LOGGER_PATH = "/var/log/validator/validator.log"

VALIDATED_IPS = {
    "104.194.145.26": [
        "/pyfrost/v1/dkg/round1",
        "/pyfrost/v1/dkg/round2",
        "/pyfrost/v1/dkg/round3",
        "/pyfrost/v1/sign",
        "/pyfrost/v1/generate-nonces",
    ]
}

PRIVATE_KEY = (
    94337664340063690438010829915800780946232589158282044690319564900000952004167
)

CHAINS_CONFIG = {
    11155111: ChainConfig(
        private_rpc="https://ethereum-sepolia-rpc.publicnode.com",
        chain_id=ChainId(11155111),
        from_block=6995672,
    ),
    17000: ChainConfig(
        private_rpc="https://holesky.drpc.org",
        chain_id=ChainId(17000),
        from_block=2691362,
    ),
}

ZEX_ENCODE_VERSION = 1
