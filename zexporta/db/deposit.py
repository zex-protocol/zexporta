import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zexporta.custom_types import (
    BlockNumber,
    BTCDeposit,
    ChainSymbol,
    Deposit,
    DepositStatus,
    TxHash,
)

from .collections import db


async def __create_deposit_index():
    await _deposit_collection.create_index(("tx_hash", "chain_symbol"), unique=True)


async def __create_btc_deposit_index():
    await _btc_deposit_collection.create_index(
        ("tx_hash", "chain_symbol", "index"), unique=True
    )


async def create_indexes():
    await asyncio.gather(__create_deposit_index(), __create_btc_deposit_index())


_deposit_collection = db["deposit"]
_btc_deposit_collection = db["btc_deposit"]
asyncio.run(create_indexes())


def get_collection(chain_symbol: ChainSymbol):
    match chain_symbol.value.upper():
        case "BTC":
            return _btc_deposit_collection
        case _:
            return _deposit_collection


async def insert_deposit_if_not_exists(deposit: Deposit | BTCDeposit):
    collection = get_collection(deposit.chain_symbol)
    query = {
        "chain_symbol": deposit.chain_symbol,
        "tx_hash": deposit.tx_hash,
    }
    if isinstance(deposit, BTCDeposit):
        query["index"] = deposit.index

    record = await collection.find_one(query)
    if not record:
        await collection.insert_one(deposit.model_dump(mode="json"))


async def insert_deposits_if_not_exists(deposits: Iterable[Deposit | BTCDeposit]):
    await asyncio.gather(
        *[insert_deposit_if_not_exists(deposit) for deposit in deposits]
    )


async def find_deposit_by_status(
    status: DepositStatus,
    chain_symbol: ChainSymbol,
    from_block: BlockNumber | None = None,
    to_block: BlockNumber | None = None,
    limit: int | None = None,
) -> list[Deposit | BTCDeposit]:
    collection = get_collection(chain_symbol)
    res = []
    block_number_query = {"$gte": from_block or 0}
    if to_block and isinstance(to_block, int):
        block_number_query["$lte"] = to_block

    query = {
        "status": status.value,
        "block_number": block_number_query,
        "chain_symbol": chain_symbol.value,
    }

    DepositDeserializer = BTCDeposit if chain_symbol.value.upper() == "BTC" else Deposit

    async for record in collection.find(query, sort={"block_number": ASCENDING}):
        res.append(DepositDeserializer(**record))
        if limit and len(record) >= limit:
            break
    return res


async def update_deposit_status(tx_hash, new_status, chain_symbol: ChainSymbol):
    collection = get_collection(chain_symbol)
    await collection.update_one({"tx_hash": tx_hash}, {"$set": {"status": new_status}})


async def delete_deposit(tx_hash, chain_symbol: ChainSymbol):
    collection = get_collection(chain_symbol)
    await collection.delete_one({"tx_hash": tx_hash})


async def to_finalized(
    chain_symbol: ChainSymbol,
    finalized_block_number: BlockNumber,
    txs_hash: list[str],
):
    collection = get_collection(chain_symbol)
    query = {
        "block_number": {"$lte": finalized_block_number},
        "status": DepositStatus.PENDING.value,
        "tx_hash": {"$in": txs_hash},
        "chain_symbol": chain_symbol.value,
    }

    update = {"$set": {"status": DepositStatus.FINALIZED.value}}

    await collection.update_many(query, update)


async def to_reorg_block_number(
    chain_symbol: ChainSymbol,
    from_block: BlockNumber,
    to_block: BlockNumber,
    status: DepositStatus = DepositStatus.PENDING,
):
    collection = get_collection(chain_symbol)
    query = {
        "block_number": {"$lte": to_block, "$gte": from_block},
        "status": status.value,
        "chain_symbol": chain_symbol.value,
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await collection.update_many(query, update)


async def to_reorg_with_tx_hash(
    chain_symbol: ChainSymbol,
    txs_hash: list[TxHash],
    status: DepositStatus = DepositStatus.PENDING,
):
    collection = get_collection(chain_symbol)
    query = {
        "status": status.value,
        "chain_symbol": chain_symbol.value,
        "tx_hash": {"$in": txs_hash},
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await collection.update_many(query, update)


async def get_pending_deposits_block_number(
    chain_symbol: ChainSymbol, finalized_block_number: BlockNumber
) -> list[BlockNumber]:
    collection = get_collection(chain_symbol)
    query = {
        "chain_symbol": chain_symbol.value,
        "status": DepositStatus.PENDING.value,
        "block_number": {"$lte": finalized_block_number},
    }
    block_numbers = set()
    async for record in collection.find(
        query,
        sort=[("block_number", ASCENDING)],
    ):
        block_numbers.add(record["block_number"])
    return list(block_numbers)


async def get_block_numbers_by_status(
    chain_symbol: ChainSymbol, status: DepositStatus
) -> list[BlockNumber]:
    collection = get_collection(chain_symbol)
    query = {"chain_symbol": chain_symbol.value, "status": status.value}
    block_numbers = set()
    async for record in collection.find(
        query,
        sort=[("block_number", ASCENDING)],
    ):
        block_numbers.add(record["block_number"])
    return list(block_numbers)


async def upsert_deposit(deposit: Deposit):
    collection = get_collection(deposit.chain_symbol)
    update = {
        "$set": deposit.model_dump(mode="json"),
    }
    filter_ = {
        "tx_hash": deposit.tx_hash,
        "chain_symbol": deposit.chain_symbol.value,
    }
    await collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_deposits(deposits: list[Deposit]):
    await asyncio.gather(*[upsert_deposit(deposit) for deposit in deposits])
