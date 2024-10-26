import asyncio

from eth_typing import BlockNumber, ChecksumAddress


from utils.web3 import async_web3_factory, Observer, extract_transfer_from_block
from custom_types import RawTransfer
from db.transfer import (
    get_last_observed_block,
    insert_many_transfers,
)
from db.address import insert_new_adderss_to_db, get_active_address
from .config import (
    BATCH_BLOCK_NUMBER_SIZE,
    MAX_DELAY_PER_BLOCK_BATCH,
    CHAINS_CONFIG,
    ChainConfig,
)


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


async def filter_valid_transfer(
    transfers: list[RawTransfer], valid_addresses: set[ChecksumAddress]
) -> tuple[RawTransfer, ...]:
    return tuple(filter(lambda transfer: transfer.to in valid_addresses, transfers))


async def observe_deposit(chain: ChainConfig):
    last_observed_block = await get_last_observed_block(chain.chain_id)
    observer = Observer(chain=chain)
    while True:
        await insert_new_adderss_to_db()
        w3 = await async_web3_factory(chain)
        valid_addresses = await get_active_address()
        latest_block = await w3.eth.get_block_number()
        if last_observed_block is not None and last_observed_block == latest_block:
            print(f"block {last_observed_block} already observed continue")
            await asyncio.sleep(MAX_DELAY_PER_BLOCK_BATCH)
            continue
        elif last_observed_block is None:
            last_observed_block = latest_block
        valid_transfers = await observer.observe(
            w3,
            last_observed_block,
            latest_block,
            valid_addresses,
            extract_transfer_from_block,
            batch_size=BATCH_BLOCK_NUMBER_SIZE,
            max_delay_per_block_batch=MAX_DELAY_PER_BLOCK_BATCH,
        )
        if len(valid_transfers) > 0:
            await insert_many_transfers(valid_transfers)
        last_observed_block = latest_block + 1


if __name__ == "__main__":
    asyncio.run(observe_deposit(CHAINS_CONFIG["11155111"]))
