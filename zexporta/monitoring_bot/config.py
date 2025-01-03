import os
from decimal import Decimal

from web3 import Web3

from zexporta.config import (
    CHAINS_CONFIG,
    USER_DEPOSIT_BYTECODE_HASH,
    USER_DEPOSIT_FACTORY_ADDRESS,
    ChainId,
)

from .custom_types import MonitoringToke

LOGGER_PATH = "/var/log/monitoring_bot/"

TEST_USER_ID = int(os.environ["MONITORING_BOT_ZEX_USER_ID"])

WITHDRAWER_PRIVATE_KEY = os.environ["MONITORING_BOT_WITHDRAWER_PRIVATE_KEY"]

MONITORING_TOKENS = [
    MonitoringToke(
        symbol="USDT",
        chain_id=ChainId(137),
        amount=10_000,
        address=Web3.to_checksum_address("0xc2132D05D31c914a87C6611C10748AEb04B58e8F"),
        decimal=6,
    ),
    MonitoringToke(
        symbol="USDT",
        chain_id=ChainId(56),
        amount=10_000,
        address=Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955"),
        decimal=18,
    ),
    MonitoringToke(
        symbol="USDT",
        chain_id=ChainId(10),
        amount=10_000,
        address=Web3.to_checksum_address("0x94b008aA00579c1307B0EF2c499aD98a8ce58e58"),
        decimal=6,
    ),
]

DELAY = 60 * 60

TELEGRAM_BASE_URL = "https://api.telegram.org"
TELEGRAM_BOT_INFO = os.environ["TELEGRAM_BOT_INFO"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
