import asyncio
import logging.config
import math

import sentry_sdk
from clients import filter_blocks, get_async_client

from zexporta.custom_types import ChainConfig, DepositStatus
from zexporta.db.deposit import (
    find_deposit_by_status,
    get_pending_deposits_block_number,
    to_finalized,
    to_reorg_block_number,
)
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


async def update_finalized_deposits(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    while True:
        try:
            client = get_async_client(chain, logger=_logger)
            finalized_block_number = await client.get_finalized_block_number()
            pending_blocks_number = await get_pending_deposits_block_number(
                chain=chain,
                finalized_block_number=finalized_block_number,
            )

            if len(pending_blocks_number) == 0:
                _logger.info(f"No pending tx has been found. finalized_block_number: {finalized_block_number}")
                await asyncio.sleep(chain.delay)
                continue

            for i in range(math.ceil(len(pending_blocks_number) / chain.batch_block_size)):
                blocks_to_check = pending_blocks_number[
                    (i * chain.batch_block_size) : ((i + 1) * chain.batch_block_size)
                ]
                results = await filter_blocks(
                    blocks_to_check,
                    client.get_block_tx_hash,
                    max_delay_per_block_batch=chain.delay,
                )
                deposit_finalizer_middleware = chain.deposit_finalizer_middleware
                if deposit_finalizer_middleware:
                    finalized_deposits_list = await find_deposit_by_status(
                        chain=chain,
                        status=DepositStatus.PENDING,
                        to_block=finalized_block_number,
                        txs_hash=results,
                    )
                    for middleware in deposit_finalizer_middleware:
                        await middleware(finalized_deposits_list)
                await to_finalized(chain, finalized_block_number, results)

                await to_reorg_block_number(chain, min(blocks_to_check), max(blocks_to_check))
        except Exception as e:
            _logger.exception(f"An error occurred: {e}")


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(update_finalized_deposits(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
