import asyncio
import logging.config

import sentry_sdk

from zexporta.custom_types import BTCConfig, ChainConfig
from zexporta.deposit.config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS
from zexporta.deposit.finalizers import (
    update_btc_finalized_deposits,
    update_finalized_deposits,
)
from zexporta.utils.logger import get_logger_config

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


FINALIZER_MAPPING = {
    BTCConfig: update_btc_finalized_deposits,
    ChainConfig: update_finalized_deposits,
}


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(FINALIZER_MAPPING[type(chain)])
        for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
