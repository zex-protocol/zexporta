# noqa: F401

import os

from zexporta.chain_config import CHAINS_CONFIG
from zexporta.settings import app_settings

CHAINS_CONFIG = CHAINS_CONFIG
DKG_JSON_PATH = app_settings.dkg.json_path
DKG_NAME = app_settings.dkg.name
EVM_NATIVE_TOKEN_ADDRESS = app_settings.evm_native_token_address
SENTRY_DNS = app_settings.sentry.dsn
USER_DEPOSIT_BYTECODE_HASH = app_settings.user_deposit.bytecode_hash
USER_DEPOSIT_FACTORY_ADDRESS = app_settings.user_deposit.factory_address
EVM_WITHDRAWER_PRIVATE_KEY = app_settings.withdrawer.evm_private_key
ZEX_ENCODE_VERSION = app_settings.zex.encode_version


LOGGER_PATH = "/var/log/deposit/"


BATCH_BLOCK_NUMBER_SIZE = app_settings.batch_block_number_size
MAX_DELAY_PER_BLOCK_BATCH = app_settings.max_delay_per_block_batch

SA_DELAY_SECOND = 10
SA_TIMEOUT = 200

SA_BATCH_BLOCK_NUMBER_SIZE = app_settings.sa.batch_block_number_size
SA_TRANSACTIONS_BATCH_SIZE = app_settings.sa.transactions_batch_size
SA_SHIELD_PRIVATE_KEY = app_settings.sa.shield_private_key
