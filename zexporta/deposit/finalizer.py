import asyncio
import logging.config

import sentry_sdk

from zexporta.custom_types import BTCConfig
from zexporta.deposit.networks_finalizers import (
    update_btc_finalized_transfers,
    update_finalized_transfers,
)
from zexporta.utils.logger import get_logger_config

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


FINALIZER_MAPPING = {
    BTCConfig: update_btc_finalized_transfers,
    CHAINS_CONFIG: update_finalized_transfers,
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
