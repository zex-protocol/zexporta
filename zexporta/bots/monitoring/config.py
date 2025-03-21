from web3 import Web3

from zexporta.bots.custom_types import BotToken
from zexporta.chain_config import CHAINS_CONFIG, ChainSymbol
from zexporta.settings import app_settings

CHAINS_CONFIG = CHAINS_CONFIG
USER_DEPOSIT_BYTECODE_HASH = app_settings.user_deposit.bytecode_hash
USER_DEPOSIT_FACTORY_ADDRESS = app_settings.user_deposit.factory_address

LOGGER_PATH = "/var/log/bot_monitoring/"

TEST_USER_ID = app_settings.monitoring.bot_zex_user_id

WITHDRAWER_PRIVATE_KEY = app_settings.monitoring.bot_withdrawer_private_key

MONITORING_TOKENS = [
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.SEP,
        amount=10_000,
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.BST,
        amount=10_000,
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.HOL,
        amount=10_000,
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
]

DELAY = 6 * 60 * 60

TELEGRAM_BASE_URL = app_settings.telegram.base_url
TELEGRAM_BOT_INFO = app_settings.telegram.bot_info
TELEGRAM_CHAT_ID = app_settings.telegram.chat_id
TELEGRAM_THREAD_ID = app_settings.telegram.thread_id
