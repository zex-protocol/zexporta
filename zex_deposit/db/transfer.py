import asyncio
from typing import Iterable

from pymongo import ASCENDING
from eth_typing import ChainId

from zex_deposit.custom_types import BlockNumber, TransferStatus, UserTransfer
from .database import transfer_collection


async def insert_transfer(transfer: UserTransfer):
    await transfer_collection.insert_one(transfer.model_dump())


async def insert_many_transfers(transfers: Iterable[UserTransfer]):
    await transfer_collection.insert_many(
        transfer.model_dump() for transfer in transfers
    )


async def find_transactions_by_status(
    status: TransferStatus,
    chain_id: ChainId,
    from_block: BlockNumber | int | None = None,
) -> list[UserTransfer]:
    res = []
    query = {
        "status": status.value,
        "chain_id": chain_id.value,
        "block_number": {"$gte": from_block or 0},
    }
    async for record in transfer_collection.find(
        query, sort={"block_number": ASCENDING}
    ):
        res.append(UserTransfer(**record))
    return res


async def update_transaction_status(tx_hash, new_status):
    await transfer_collection.update_one(
        {"tx_hash": tx_hash}, {"$set": {"status": new_status}}
    )


async def delete_transaction(tx_hash):
    await transfer_collection.delete_one({"tx_hash": tx_hash})


async def to_finalized(
    chain_id: ChainId,
    finalized_block_number: BlockNumber,
    tx_hashes: list[str],
):
    query = {
        "block_number": {"$lte": finalized_block_number},
        "status": TransferStatus.PENDING.value,
        "tx_hash": {"$in": tx_hashes},
        "chain_id": chain_id.value,
    }

    update = {"$set": {"status": TransferStatus.FINALIZED.value}}

    await transfer_collection.update_many(query, update)


async def to_reorg(
    chain_id: ChainId,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
    status: TransferStatus = TransferStatus.PENDING,
):
    query = {
        "block_number": {"$lte": to_block, "$gte": from_block},
        "status": status.value,
        "chain_id": chain_id.value,
    }
    update = {"$set": {"status": TransferStatus.REORG.value}}
    await transfer_collection.update_many(query, update)


async def get_pending_transfers_block_number(
    chain_id: ChainId, finalized_block_number: BlockNumber
) -> list[BlockNumber]:
    query = {
        "chain_id": chain_id.value,
        "status": TransferStatus.PENDING.value,
        "block_number": {"$lte": finalized_block_number},
    }
    block_numbers = set()
    async for record in transfer_collection.find(
        query,
        sort=[("block_number", ASCENDING)],
    ):
        block_numbers.add(BlockNumber(record["block_number"]))
    return list(block_numbers)


async def upsert_verified_transfers(verified_transfers: list[UserTransfer]):
    tasks = []
    for verified_transfer in verified_transfers:
        update = {
            "$set": verified_transfer.model_dump(),
        }
        filter_ = {
            "tx_hash": verified_transfer.tx_hash,
            "chain_id": verified_transfer.chain_id,
        }
        tasks.append(
            asyncio.create_task(
                transfer_collection.update_one(
                    filter=filter_, update=update, upsert=True
                )
            )
        )
    [await task for task in tasks]
