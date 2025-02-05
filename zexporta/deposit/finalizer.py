import asyncio
import logging.config
import math

import sentry_sdk
from clients import filter_blocks, get_async_client

from zexporta.custom_types import BTCConfig, ChainConfig, DepositStatus, UtxoStatus
from zexporta.db.deposit import (
    find_deposit_by_status,
    get_pending_deposits_block_number,
    to_finalized,
    to_reorg_block_number,
)
from zexporta.db.utxo import populate_deposits_utxos
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


async def update_finalized_deposits(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    while True:
        client = get_async_client(chain)
        finalized_block_number = await client.get_finalized_block_number()
        pending_blocks_number = await get_pending_deposits_block_number(
            chain=chain,
            finalized_block_number=finalized_block_number,
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
                blocks_to_check,
                client.get_block_tx_hash,
                max_delay_per_block_batch=chain.delay,
            )
            if isinstance(chain, BTCConfig):
                finalized_deposits = await find_deposit_by_status(
                    chain=chain,
                    status=DepositStatus.PENDING,
                    to_block=finalized_block_number,
                    txs_hash=results,
                )
                await populate_deposits_utxos(
                    finalized_deposits, status=UtxoStatus.UNSPENT
                )
            await to_finalized(chain, finalized_block_number, results)

            if isinstance(chain, BTCConfig):
                reorged_deposits = await find_deposit_by_status(
                    chain=chain,
                    status=DepositStatus.PENDING,
                    to_block=max(blocks_to_check),
                    from_block=min(blocks_to_check),
                )
                await populate_deposits_utxos(
                    reorged_deposits, status=UtxoStatus.REJECTED
                )
            await to_reorg_block_number(
                chain, min(blocks_to_check), max(blocks_to_check)
            )


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(update_finalized_deposits(chain))
        for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
