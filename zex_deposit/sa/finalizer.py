import asyncio
import logging
import logging.config
import math

from zex_deposit.db.transfer import (
    get_pending_transfers_block_number,
    to_finalized,
    to_reorg,
)
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.web3 import (
    async_web3_factory,
    filter_blocks,
    get_block_tx_hash,
    get_finalized_block_number,
)

from .config import (
    CHAINS_CONFIG,
    LOGGER_PATH,
    ChainConfig,
)

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


async def update_finalized_transfers(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    while True:
        w3 = await async_web3_factory(chain)
        finalized_block_number = await get_finalized_block_number(w3, chain)
        pending_blocks_number = await get_pending_transfers_block_number(
            chain_id=chain.chain_id, finalized_block_number=finalized_block_number
        )

        if len(pending_blocks_number) == 0:
            _logger.info(
                f"No pending tx has been found. finalized_block_number: {finalized_block_number}"
            )
            await asyncio.sleep(chain.delay)
            continue

        for i in range(math.ceil(len(pending_blocks_number) / chain.batch_block_size)):
            blocks_to_check = pending_blocks_number[
                (i * chain.batch_block_size) : ((i + 1) * chain.batch_block_size)
            ]
            results = await filter_blocks(
                w3,
                blocks_to_check,
                get_block_tx_hash,
                max_delay_per_block_batch=chain.delay,
            )
            await to_finalized(chain.chain_id, finalized_block_number, results)
            await to_reorg(chain.chain_id, min(blocks_to_check), max(blocks_to_check))


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(update_finalized_transfers(chain))
        for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
