import asyncio
from hashlib import sha256

from zexporta.custom_types import BlockNumber, ChainConfig, TransferStatus
from zexporta.db.address import get_active_address, insert_new_address_to_db
from zexporta.utils.encoder import DEPOSIT_OPERATION, encode_zex_deposit
from zexporta.utils.observer import get_accepted_transfers
from zexporta.utils.web3 import (
    async_web3_factory,
    extract_transfer_from_block,
    filter_blocks,
    get_finalized_block_number,
)

from .config import ZEX_ENCODE_VERSION


class BlocksIsEmpty(Exception):
    "Raise when a blocks list is empty"


class NotFinalizedBlockError(Exception):
    "Raise when a block number is bigger then current finalized block"


def deposit(chain_config: ChainConfig, data: dict, logger) -> dict:
    blocks = data["blocks"]
    if len(blocks) < 1:
        raise BlocksIsEmpty()
    users_transfers = asyncio.run(
        get_users_transfers(chain=chain_config, blocks=blocks)
    )
    encoded_data = encode_zex_deposit(
        version=ZEX_ENCODE_VERSION,
        operation_type=DEPOSIT_OPERATION,
        chain=chain_config,
        users_transfers=users_transfers,
    )
    logger.info(f"encoded_data is: {encoded_data}")
    return {
        "hash": sha256(encoded_data).hexdigest(),
        "data": {
            "users_transfers": [
                user_transfer.model_dump(mode="json")
                for user_transfer in users_transfers
            ],
        },
    }


async def get_users_transfers(chain: ChainConfig, blocks: list[BlockNumber]):
    blocks.sort()
    to_block = blocks[-1]
    w3 = await async_web3_factory(chain=chain)
    finalized_block_number = await get_finalized_block_number(w3, chain)
    if to_block > finalized_block_number:
        raise NotFinalizedBlockError(
            f"to_block: {to_block} is not finalized, finalized_block: {finalized_block_number}"
        )
    await insert_new_address_to_db()
    accepted_addresses = await get_active_address()
    users_transfers = []
    for _blocks in [
        blocks[i : (i + chain.batch_block_size)]
        for i in range(0, len(blocks), chain.batch_block_size)
    ]:
        raw_transfers = await filter_blocks(
            w3,
            _blocks,
            extract_transfer_from_block,
            chain_id=chain.chain_id,
            max_delay_per_block_batch=chain.delay,
            transfer_status=TransferStatus.VERIFIED,
        )
        users_transfers.extend(
            (await get_accepted_transfers(w3, chain, raw_transfers, accepted_addresses))
        )
    return sorted(users_transfers)
