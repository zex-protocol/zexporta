import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zexporta.custom_types import (
    BlockNumber,
    ChainSymbol,
    Deposit,
    DepositStatus,
    TxHash,
)

from .collections import db


async def __create_deposit_index():
    await _deposit_collection.create_index(("tx_hash", "chain_symbol"), unique=True)


_deposit_collection = db["deposit"]
asyncio.run(__create_deposit_index())


async def insert_deposit_if_not_exists(deposit: Deposit):
    query = {
        "chain_symbol": deposit.chain_symbol,
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
    chain_symbol: ChainSymbol,
    from_block: BlockNumber | int | None = None,
    limit: int | None = None,
) -> list[Deposit]:
    res = []
    query = {
        "status": status.value,
        "chain_symbol": chain_symbol.value,
        "block_number": {"$gte": from_block or 0},
    }
    async for record in _deposit_collection.find(
        query, sort={"block_number": ASCENDING}
    ):
        res.append(Deposit(**record))
        if limit and len(record) >= limit:
            break
    return res


async def update_deposit_status(tx_hash, new_status):
    await _deposit_collection.update_one(
        {"tx_hash": tx_hash}, {"$set": {"status": new_status}}
    )


async def delete_deposit(tx_hash):
    await _deposit_collection.delete_one({"tx_hash": tx_hash})


async def to_finalized(
    chain_symbol: ChainSymbol,
    finalized_block_number: BlockNumber,
    txs_hash: list[str],
):
    query = {
        "block_number": {"$lte": finalized_block_number},
        "status": DepositStatus.PENDING.value,
        "tx_hash": {"$in": txs_hash},
        "chain_symbol": chain_symbol.value,
    }

    update = {"$set": {"status": DepositStatus.FINALIZED.value}}

    await _deposit_collection.update_many(query, update)


async def to_reorg_block_number(
    chain_symbol: ChainSymbol,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
    status: DepositStatus = DepositStatus.PENDING,
):
    query = {
        "block_number": {"$lte": to_block, "$gte": from_block},
        "status": status.value,
        "chain_symbol": chain_symbol.value,
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await _deposit_collection.update_many(query, update)


async def to_reorg_with_tx_hash(
    chain_symbol: ChainSymbol,
    txs_hash: list[TxHash],
    status: DepositStatus = DepositStatus.PENDING,
):
    query = {
        "status": status.value,
        "chain_symbol": chain_symbol.value,
        "tx_hash": {"$in": txs_hash},
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await _deposit_collection.update_many(query, update)


async def get_pending_deposits_block_number(
    chain_symbol: ChainSymbol, finalized_block_number: BlockNumber
) -> list[BlockNumber]:
    query = {
        "chain_symbol": chain_symbol.value,
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
    chain_symbol: ChainSymbol, status: DepositStatus
) -> list[BlockNumber]:
    query = {"chain_symbol": chain_symbol.value, "status": status.value}
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
        "chain_symbol": deposit.chain_symbol.value,
    }
    await _deposit_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_deposits(deposits: list[Deposit]):
    await asyncio.gather(*[upsert_deposit(deposit) for deposit in deposits])
