import asyncio
import logging

from eth_typing import BlockNumber, ChecksumAddress

from zex_deposit.custom_types import RawTransfer
from zex_deposit.db.address import get_active_address, insert_new_address_to_db
from zex_deposit.db.chain import (
    get_last_observed_block,
    upsert_chain_last_observed_block,
)
from zex_deposit.db.transfer import insert_many_transfers
from zex_deposit.utils.web3 import (
    Observer,
    async_web3_factory,
    extract_transfer_from_block,
)

from .config import (
    BATCH_BLOCK_NUMBER_SIZE,
    CHAINS_CONFIG,
    MAX_DELAY_PER_BLOCK_BATCH,
    ChainConfig,
)

logger = logging.getLogger(__name__)


async def get_block_batches(
    from_block: BlockNumber | int, latest_block: BlockNumber | int
) -> list[tuple[BlockNumber, ...]]:
    block_batches = [
        tuple(
            BlockNumber(j)
            for j in range(i, min(latest_block + 1, i + BATCH_BLOCK_NUMBER_SIZE + 1))
        )
        for i in range(from_block, latest_block + 1, BATCH_BLOCK_NUMBER_SIZE)
    ]
    return block_batches


async def filter_transfer(
    transfers: list[RawTransfer], accepted_addresses: set[ChecksumAddress]
) -> tuple[RawTransfer, ...]:
    return tuple(filter(lambda transfer: transfer.to in accepted_addresses, transfers))


async def observe_deposit(chain: ChainConfig):
    observer = Observer(chain=chain)
    while True:
        await insert_new_address_to_db()
        w3 = await async_web3_factory(chain)
        accepted_addresses = await get_active_address()
        latest_block = await w3.eth.get_block_number()
        last_observed_block = (
            await get_last_observed_block(chain.chain_id)
        ) or chain.from_block
        if last_observed_block is not None and last_observed_block == latest_block:
            logger.info(f"block {last_observed_block} already observed continue")
            await asyncio.sleep(MAX_DELAY_PER_BLOCK_BATCH)
            continue
        accepted_transfers = await observer.observe(
            w3,
            last_observed_block + 1,
            latest_block,
            accepted_addresses,
            extract_transfer_from_block,
            batch_size=BATCH_BLOCK_NUMBER_SIZE,
            max_delay_per_block_batch=MAX_DELAY_PER_BLOCK_BATCH,
        )
        if len(accepted_transfers) > 0:
            await insert_many_transfers(accepted_transfers)
        await upsert_chain_last_observed_block(
            chain.chain_id, block_number=latest_block
        )

async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(observe_deposit(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
