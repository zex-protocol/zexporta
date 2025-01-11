import asyncio
import logging.config

import sentry_sdk

from zex_deposit.config import DEFAULTS
from zex_deposit.deposit.networks_finalizers import (
    update_btc_finalized_transfers,
    update_finalized_transfers,
)
from zex_deposit.utils.logger import get_logger_config

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


FINALIZER_MAPPING = {
    "BTC": update_btc_finalized_transfers,
    DEFAULTS: update_finalized_transfers,
}


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(
            FINALIZER_MAPPING.get(chain.symbol, FINALIZER_MAPPING[DEFAULTS])(chain)
        )
        for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
