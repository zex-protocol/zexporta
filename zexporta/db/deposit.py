import asyncio
from typing import Iterable

from eth_typing import ChainId
from pymongo import ASCENDING

from zexporta.custom_types import BlockNumber, Deposit, DepositStatus

from .collections import db


async def __create_deposit_index():
    await _deposit_collection.create_index(("tx_hash", "chain_id"), unique=True)


_deposit_collection = db["deposit"]
asyncio.run(__create_deposit_index())


async def insert_deposit_if_not_exists(deposit: Deposit):
    query = {
        "chain_id": deposit.chain_id,
        "tx_hash": deposit.tx_hash,
    }
    record = await _deposit_collection.find_one(query)
    if not record:
        await _deposit_collection.insert_one(deposit.model_dump(mode="json"))


async def insert_deposits_if_not_exists(deposits: Iterable[Deposit]):
    await asyncio.gather(
        *[insert_deposit_if_not_exists(deposit) for deposit in deposits]
    )


async def find_deposit_by_status(
    status: DepositStatus,
    chain_id: ChainId,
    from_block: BlockNumber | int | None = None,
    to_block: BlockNumber | int | None = None,
) -> list[Deposit]:
    res = []
    block_number_query = {"$gte": from_block or 0}
    if to_block and isinstance(to_block, int):
        block_number_query["$lte"] = to_block

    query = {
        "status": status.value,
        "chain_id": chain_id.value,
        "block_number": block_number_query,
    }
    async for record in _deposit_collection.find(
        query, sort={"block_number": ASCENDING}
    ):
        res.append(Deposit(**record))
    return res


async def update_deposit_status(tx_hash, new_status):
    await _deposit_collection.update_one(
        {"tx_hash": tx_hash}, {"$set": {"status": new_status}}
    )


async def delete_deposit(tx_hash):
    await _deposit_collection.delete_one({"tx_hash": tx_hash})


async def to_finalized(
    chain_id: ChainId,
    finalized_block_number: BlockNumber | int,
    tx_hashes: list[str],
):
    query = {
        "block_number": {"$lte": finalized_block_number},
        "status": DepositStatus.PENDING.value,
        "tx_hash": {"$in": tx_hashes},
        "chain_id": chain_id.value,
    }

    update = {"$set": {"status": DepositStatus.FINALIZED.value}}

    await _deposit_collection.update_many(query, update)


async def to_reorg(
    chain_id: ChainId,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
    tx_hashes: list[str] | None = None,
    status: DepositStatus = DepositStatus.PENDING,
):
    query = {
        "block_number": {"$lte": to_block, "$gte": from_block},
        "status": status.value,
        "chain_id": chain_id.value,
    }
    if tx_hashes:
        query["tx_hash"] = {"$in": tx_hashes}

    update = {"$set": {"status": DepositStatus.REORG.value}}
    await _deposit_collection.update_many(query, update)


async def get_pending_deposits_block_number(
    chain_id: ChainId, finalized_block_number: BlockNumber
) -> list[BlockNumber]:
    query = {
        "chain_id": chain_id.value,
        "status": DepositStatus.PENDING.value,
        "block_number": {"$lte": finalized_block_number},
    }
    block_numbers = set()
    async for record in _deposit_collection.find(
        query,
        sort=[("block_number", ASCENDING)],
    ):
        block_numbers.add(BlockNumber(record["block_number"]))
    return list(block_numbers)


async def get_block_numbers_by_status(
    chain_id: ChainId, status: DepositStatus
) -> list[BlockNumber]:
    query = {"chain_id": chain_id.value, "status": status.value}
    block_numbers = set()
    async for record in _deposit_collection.find(
        query,
        sort=[("block_number", ASCENDING)],
    ):
        block_numbers.add(BlockNumber(record["block_number"]))
    return list(block_numbers)


async def upsert_deposit(deposit: Deposit):
    update = {
        "$set": deposit.model_dump(mode="json"),
    }
    filter_ = {
        "tx_hash": deposit.tx_hash,
        "chain_id": deposit.chain_id,
    }
    await _deposit_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_deposits(deposits: list[Deposit]):
    await asyncio.gather(*[upsert_deposit(deposit) for deposit in deposits])
