# noqa: F401

import os

from dotenv import load_dotenv

from zex_deposit.config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    MONGO_URI,
    SA_SHIELD_PRIVATE_KEY,
    USER_DEPOSIT_BYTECODE_HASH,
    USER_DEPOSIT_FACTORY_ADDRESS,
    ZEX_ENCODE_VERSION,
)

load_dotenv()

LOGGER_PATH = "/var/log/zex_deposit/depositor/"


BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("BATCH_BLOCK_NUMBER_SIZE", 5))
MAX_DELAY_PER_BLOCK_BATCH = int(os.getenv("MAX_DELAY_PER_BLOCK_BATCH", 3))

SA_DELAY_SECOND = 10
SA_TIMEOUT = 200
SA_BATCH_BLOCK_NUMBER_SIZE = int(os.getenv("SA_BATCH_BLOCK_NUMBER_SIZE", 100))
WITHDRAWER_PRIVATE_KEY = os.environ["WITHDRAWER_PRIVATE_KEY"]
