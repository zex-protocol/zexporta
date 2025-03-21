import asyncio
import logging.config

import clients.exceptions as client_exception
import sentry_sdk
from clients import (
    get_async_client,
)

from zexporta.custom_types import ChainConfig
from zexporta.db.address import get_active_address, insert_new_address_to_db
from zexporta.db.chain import (
    get_last_observed_block,
    upsert_chain_last_observed_block,
)
from zexporta.db.deposit import insert_deposits_if_not_exists
from zexporta.explorer import explorer
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/observer.log"))
logger = logging.getLogger(__name__)


async def observe_deposit(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    last_observed_block = await get_last_observed_block(chain.chain_symbol)
    while True:
        client = get_async_client(chain, logger=_logger)
        latest_block = await client.get_latest_block_number()
        if last_observed_block is not None and last_observed_block == latest_block:
            _logger.info(f"Block {last_observed_block} already observed continue")
            await asyncio.sleep(chain.delay)
            continue
        last_observed_block = last_observed_block or (latest_block - 1)
        to_block = min(latest_block, last_observed_block + chain.batch_block_size)
        if last_observed_block >= to_block:
            _logger.warning(f"last_observed_block: {last_observed_block} is bigger then to_block {to_block}")
            continue
        await insert_new_address_to_db(chain)
        accepted_addresses = await get_active_address(chain)
        try:
            accepted_deposits = await explorer(
                client,
                last_observed_block + 1,
                to_block,
                accepted_addresses,
                client.extract_transfer_from_block,
                logger=_logger,
                batch_size=chain.batch_block_size,
                max_delay_per_block_batch=chain.delay,
            )
        except client_exception.BaseClientError as e:
            logger.error(f"Client raise Error, {e}")
        except ValueError as e:
            _logger.error(f"ValueError: {e}")
            await asyncio.sleep(10)
        except Exception as e:
            _logger.exception(f"Exception: {e}")
            await asyncio.sleep(5)
        else:
            if len(accepted_deposits) > 0:
                await insert_deposits_if_not_exists(chain, accepted_deposits)

        await upsert_chain_last_observed_block(chain.chain_symbol, to_block)
        last_observed_block = to_block


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(observe_deposit(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
