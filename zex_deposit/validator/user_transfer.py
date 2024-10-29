from functools import partial

from utils.web3 import async_web3_factory, extract_transfer_from_block, Observer
from db.address import get_active_address, insert_new_adderss_to_db
from custom_types import ChainConfig, TransferStatus, BlockNumber


async def get_users_transfers(
    chain: ChainConfig, from_block: BlockNumber | int, to_blcok: BlockNumber | int
):
    w3 = await async_web3_factory(chain=chain)
    observer = Observer(chain=chain)
    await insert_new_adderss_to_db()
    valid_addresses = await get_active_address()
    users_transfers = await observer.observe(
        w3,
        from_block=from_block,
        to_block=to_blcok,
        valid_addresses=valid_addresses,
        extract_block_logic=extract_transfer_from_block,
        transfer_status=TransferStatus.FINALIZED,
    )
    return sorted(users_transfers)
