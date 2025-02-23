import asyncio
import logging.config

import httpx
import sentry_sdk
from clients import EVMConfig

from zexporta.custom_types import ChainConfig
from zexporta.db.chain import (
    get_last_withdraw_nonce,
    upsert_chain_last_withdraw_nonce,
)
from zexporta.db.withdraw import insert_withdraws_if_not_exists
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.zex_api import (
    ZexAPIError,
    get_zex_last_withdraw_nonce,
    get_zex_withdraws,
)

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS, WITHDRAW_DELAY_SECOND

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/observer.log"))
logger = logging.getLogger(__name__)


async def did_last_nonce_observed(client: httpx.AsyncClient, last_withdraw_nonce: int, chain: ChainConfig) -> bool:
    zex_last_nonce = await get_zex_last_withdraw_nonce(client, chain)

    if last_withdraw_nonce >= zex_last_nonce:
        return True
    return False


async def observe_withdraw(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)

    while True:
        client = httpx.AsyncClient()
        try:
            last_withdraw_nonce = await get_last_withdraw_nonce(chain.chain_symbol)

            last_nonce_observed = await did_last_nonce_observed(client, last_withdraw_nonce, chain)
            if last_nonce_observed:
                _logger.info("No withdraw to process ...")
                continue
            withdraws = await get_zex_withdraws(async_client=client, chain=chain, offset=last_withdraw_nonce + 1)
            _logger.info(f"withdraws: {withdraws}")
            await insert_withdraws_if_not_exists(withdraws)
            await upsert_chain_last_withdraw_nonce(chain.chain_symbol, last_withdraw_nonce + len(withdraws))

        except ZexAPIError as e:
            _logger.error(f"Error at sending deposit to Zex: {e}")
            continue

        finally:
            await client.aclose()
            await asyncio.sleep(WITHDRAW_DELAY_SECOND)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(observe_withdraw(chain)) for chain in CHAINS_CONFIG.values() if isinstance(chain, EVMConfig)
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
