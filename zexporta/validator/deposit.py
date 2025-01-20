import asyncio
from hashlib import sha256

from zexporta.custom_types import (
    BlockNumber,
    DepositStatus,
    EVMConfig,
    SaDepositSchema,
    Timestamp,
    TxHash,
)
from zexporta.db.address import get_active_address, insert_new_address_to_db
from zexporta.utils.encoder import DEPOSIT_OPERATION, encode_zex_deposit
from zexporta.utils.observer import get_accepted_deposits
from zexporta.utils.web3 import (
    async_web3_factory,
    get_finalized_block_number,
    get_transfers_by_tx,
)

from .config import ZEX_ENCODE_VERSION


class NoTxHashError(Exception):
    "Raise when a txs_hash list is empty"


class NotFinalizedBlockError(Exception):
    "Raise when a block number is bigger then current finalized block"


def deposit(chain_config: EVMConfig, data: SaDepositSchema, logger) -> dict:
    txs_hash = data.txs_hash
    if len(txs_hash) == 0:
        raise NoTxHashError()
    deposits = asyncio.run(
        get_deposits(
            chain=chain_config,
            txs_hash=txs_hash,
            sa_finalized_block_number=data.finalized_block_number,
            sa_timestamp=data.timestamp,
        )
    )
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


async def get_deposits(
    chain: EVMConfig,
    txs_hash: list[TxHash],
    sa_finalized_block_number: BlockNumber,
    sa_timestamp: Timestamp,
):
    w3 = await async_web3_factory(chain=chain)
    finalized_block_number = await get_finalized_block_number(w3, chain)
    if sa_finalized_block_number > finalized_block_number:
        raise NotFinalizedBlockError(
            f"sa_finalized_block_number: {sa_finalized_block_number} \
            is not finalized in validator , finalized_block: {finalized_block_number}"
        )
    await insert_new_address_to_db()
    accepted_addresses = await get_active_address()
    transfers = await asyncio.gather(
        *[
            get_transfers_by_tx(w3, chain.chain_symbol, tx_hash, sa_timestamp)
            for tx_hash in txs_hash
        ]
    )
    deposits = await get_accepted_deposits(
        w3,
        chain,
        [
            transfer
            for transfer in transfers
            if transfer is not None and transfer.block_number <= finalized_block_number
        ],
        accepted_addresses,
        deposit_status=DepositStatus.VERIFIED,
    )
    return sorted(deposits)
