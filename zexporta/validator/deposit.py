import asyncio
from hashlib import sha256

from zexporta.clients import get_btc_async_client
from zexporta.config import ZEX_ENCODE_VERSION
from zexporta.custom_types import BlockNumber, BTCConfig, ChainConfig, DepositStatus
from zexporta.db.address import get_active_address, insert_new_address_to_db
from zexporta.utils.btc import (
    extract_btc_transfer_from_block,
    get_btc_finalized_block_number,
)
from zexporta.utils.btc_observer import (
    get_accepted_transfers as get_btc_accepted_transfers,
)
from zexporta.utils.encoder import DEPOSIT_OPERATION, encode_zex_deposit
from zexporta.utils.observer import get_accepted_deposits
from zexporta.utils.web3 import (
    async_web3_factory,
    extract_transfer_from_block,
    filter_blocks,
    get_finalized_block_number,
)


class BlocksIsEmpty(Exception):
    "Raise when a blocks list is empty"


class NotFinalizedBlockError(Exception):
    "Raise when a block number is bigger then current finalized block"


def deposit(chain_config, data: dict, logger) -> dict:
    blocks = data["blocks"]
    if len(blocks) < 1:
        raise BlocksIsEmpty()
    get_deposits = DEPOSIT_GETTERS[chain_config]
    deposits = asyncio.run(get_deposits(chain=chain_config, blocks=blocks))
    encoded_data = encode_zex_deposit(
        version=ZEX_ENCODE_VERSION,
        operation_type=DEPOSIT_OPERATION,
        chain=chain_config,
        deposits=deposits,
    )
    logger.info(f"encoded_data is: {encoded_data}")
    return {
        "hash": sha256(encoded_data).hexdigest(),
        "data": {
            "deposits": [deposit.model_dump(mode="json") for deposit in deposits],
        },
    }


async def get_evm_deposits(chain: ChainConfig, blocks: list[BlockNumber]):
    blocks.sort()
    to_block = blocks[-1]
    w3 = await async_web3_factory(chain=chain)
    finalized_block_number = await get_finalized_block_number(w3, chain)
    if to_block > finalized_block_number:
        raise NotFinalizedBlockError(
            f"to_block: {to_block} is not finalized, finalized_block: {finalized_block_number}"
        )
    await insert_new_address_to_db()
    accepted_addresses = await get_active_address(chain)
    deposits = []
    for _blocks in [
        blocks[i : (i + chain.batch_block_size)]
        for i in range(0, len(blocks), chain.batch_block_size)
    ]:
        transfers = await filter_blocks(
            w3,
            _blocks,
            extract_transfer_from_block,
            chain_id=chain.chain_id,
            max_delay_per_block_batch=chain.delay,
        )
        deposits.extend(
            await get_accepted_deposits(
                w3,
                chain,
                transfers,
                accepted_addresses,
                deposit_status=DepositStatus.VERIFIED,
            )
        )
    return sorted(deposits)


async def get_btc_deposits(chain: BTCConfig, blocks: list[BlockNumber]):
    blocks.sort()
    to_block = blocks[-1]
    btc = get_btc_async_client(chain)
    finalized_block_number = await get_btc_finalized_block_number(btc, chain)
    if to_block > finalized_block_number:
        raise NotFinalizedBlockError(
            f"to_block: {to_block} is not finalized, finalized_block: {finalized_block_number}"
        )
    await insert_new_address_to_db()
    accepted_addresses = await get_active_address(chain)
    deposits = []
    for i in blocks:
        block = await btc.get_block_by_identifier(i)
        transfers = extract_btc_transfer_from_block(i, block, chain.chain_id)
        accepted_transfers = await get_btc_accepted_transfers(
            transfers, accepted_addresses
        )
        deposits.extend(accepted_transfers)
    return sorted(deposits)


DEPOSIT_GETTERS = {ChainConfig: get_evm_deposits, BTCConfig: get_btc_deposits}
