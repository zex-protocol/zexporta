import os

from eth_typing import ChainId

from custom_types import ChainConfig

BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("BATCH_BLOCK_NUMBER_SIZE", 5))
VALIDATED_IPS = {
    "127.0.0.1": [
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
        private_rpc=("https://ethereum-sepolia-rpc.publicnode.com"),
        chain_id=ChainId(11155111),
    )
}

ZEX_ENDODE_VERSION = 1