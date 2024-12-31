import os
from decimal import Decimal

from web3 import Web3

from zex_deposit.config import (
    CHAINS_CONFIG,
    USER_DEPOSIT_BYTECODE_HASH,
    USER_DEPOSIT_FACTORY_ADDRESS,
    WITHDRAWER_PRIVATE_KEY,
    ChainId,
)

from .custom_types import MonitoringToke

# LOGGER_PATH = "/var/log/monitoring_bot/"
LOGGER_PATH = "./"

TEST_USER_ID = 1

WITHDRAW_DESTINATION = "5fCeb18CF62bF791d7Aa0931D3159f95650A0061"

TEST_USER_PRIVATE_KEY = os.environ["TEST_USER_PRIVATE_KEY"]
WITHDRAW_PUBLIC_KEY = (
    "032b7a64a141e60302178baa1c12d7df40d284cd62dff2c80c5c6812d3959c2856"
)

MONITORING_TOKENS = [
    MonitoringToke(
        symbol="USDT",
        chain_id=ChainId(137),
        amount=10000,
        address=Web3.to_checksum_address("0xc2132D05D31c914a87C6611C10748AEb04B58e8F"),
        decimal=6,
    ),
]

DELAY = 30 * 60

TELEGRAM_BASE_URL = "https://api.telegram.org"
TELEGRAM_BOT_INFO = os.environ["TELEGRAM_BOT_INFO"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
