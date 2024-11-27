from zex_deposit.custom_types import BlockNumber, ChainConfig, TransferStatus
from zex_deposit.db.address import get_active_address, insert_new_address_to_db
from zex_deposit.utils.web3 import (
    async_web3_factory,
    extract_transfer_from_block,
    get_finalized_block_number,
)
from zex_deposit.utils.observer import Observer


class NotFinalizedBlockError(Exception):
    "Raise when a block number is bigger then current finalized block"


async def get_users_transfers(
    chain: ChainConfig, from_block: BlockNumber | int, to_block: BlockNumber | int
):
    w3 = await async_web3_factory(chain=chain)
    finalized_block_number = await get_finalized_block_number(w3, chain)
    if to_block > finalized_block_number:
        raise NotFinalizedBlockError(
            f"to_block: {to_block} is not finalized, finalized_block: {finalized_block_number}"
        )
    observer = Observer(chain=chain, w3=w3)
    await insert_new_address_to_db()
    accepted_addresses = await get_active_address()
    users_transfers = await observer.observe(
        from_block=from_block,
        to_block=to_block,
        accepted_addresses=accepted_addresses,
        extract_block_logic=extract_transfer_from_block,
        transfer_status=TransferStatus.VERIFIED,
        max_delay_per_block_batch=chain.delay,
        batch_size=chain.batch_block_size,
    )
    return sorted(users_transfers)
