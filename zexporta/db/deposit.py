import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zexporta.custom_types import (
    BlockNumber,
    BTCConfig,
    ChainConfig,
    Deposit,
    DepositStatus,
    EVMConfig,
    TxHash,
)

from .collections import db

_deposit_collections = {EVMConfig: db["evm_deposit"], BTCConfig: db["btc_deposit"]}


async def __create_indexes():
    await _deposit_collections[EVMConfig].create_index(
        ("transfer.tx_hash", "transfer.chain_symbol"), unique=True
    )
    await _deposit_collections[BTCConfig].create_index(
        ("transfer.tx_hash", "transfer.chain_symbol", "transfer.index"), unique=True
    )


asyncio.run(__create_indexes())


def get_collection(chain: ChainConfig):
    match chain:
        case EVMConfig():
            return _deposit_collections[EVMConfig]
        case BTCConfig():
            return _deposit_collections[BTCConfig]
    raise NotImplementedError()


async def insert_deposit_if_not_exists(chain: ChainConfig, deposit: Deposit):
    collection = get_collection(chain)
    query = {
        "transfer.chain_symbol": deposit.transfer.chain_symbol,
        "transfer.tx_hash": deposit.transfer.tx_hash,
    }
    record = await collection.find_one(query)
    if not record:
        await collection.insert_one(deposit.model_dump(mode="json"))


async def insert_deposits_if_not_exists(
    chain: ChainConfig, deposits: Iterable[Deposit]
):
    await asyncio.gather(
        *[insert_deposit_if_not_exists(chain, deposit) for deposit in deposits]
    )


async def find_deposit_by_status(
    chain: ChainConfig,
    status: DepositStatus,
    from_block: BlockNumber | None = None,
    to_block: BlockNumber | None = None,
    limit: int | None = None,
) -> list[Deposit]:
    collection = get_collection(chain)
    res = []
    block_number_query = {"$gte": from_block or 0}
    if to_block:
        block_number_query["$lte"] = to_block

    query = {
        "status": status.value,
        "transfer.block_number": block_number_query,
        "transfer.chain_symbol": chain.chain_symbol,
    }

    async for record in collection.find(
        query, sort={"transfer.block_number": ASCENDING}
    ):
        transfer = chain.transfer_class(**record["transfer"])
        del record["transfer"]
        res.append(Deposit(transfer=transfer, **record))
        if limit and len(record) >= limit:
            break
    return res


async def update_deposit_status(
    chain: ChainConfig, tx_hash: TxHash, new_status: DepositStatus
):
    collection = get_collection(chain)
    await collection.update_one(
        {"transfer.tx_hash": tx_hash}, {"$set": {"status": new_status}}
    )


async def delete_deposit(chain: ChainConfig, tx_hash: TxHash):
    collection = get_collection(chain)
    await collection.delete_one({"transfer.tx_hash": tx_hash})


async def to_finalized(
    chain: ChainConfig,
    finalized_block_number: BlockNumber,
    txs_hash: list[TxHash],
):
    collection = get_collection(chain)
    query = {
        "status": DepositStatus.PENDING.value,
        "transfer.block_number": {"$lte": finalized_block_number},
        "transfer.tx_hash": {"$in": txs_hash},
        "transfer.chain_symbol": chain.chain_symbol,
    }

    update = {"$set": {"status": DepositStatus.FINALIZED.value}}

    await collection.update_many(query, update)


async def to_reorg_block_number(
    chain: ChainConfig,
    from_block: BlockNumber,
    to_block: BlockNumber,
    status: DepositStatus = DepositStatus.PENDING,
):
    collection = get_collection(chain)
    query = {
        "status": status.value,
        "transfer.block_number": {"$lte": to_block, "$gte": from_block},
        "transfer.chain_symbol": chain.chain_symbol,
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await collection.update_many(query, update)


async def to_reorg_with_tx_hash(
    chain: ChainConfig,
    txs_hash: list[TxHash],
    status: DepositStatus = DepositStatus.PENDING,
):
    collection = get_collection(chain)
    query = {
        "status": status.value,
        "transfer.chain_symbol": chain.chain_symbol,
        "transfer.tx_hash": {"$in": txs_hash},
    }
    update = {"$set": {"status": DepositStatus.REORG.value}}
    await collection.update_many(query, update)


async def get_pending_deposits_block_number(
    chain: ChainConfig, finalized_block_number: BlockNumber
) -> list[BlockNumber]:
    collection = get_collection(chain)
    query = {
        "status": DepositStatus.PENDING.value,
        "transfer.chain_symbol": chain.chain_symbol,
        "transfer.block_number": {"$lte": finalized_block_number},
    }
    block_numbers = set()
    async for record in collection.find(
        query,
        sort=[("transfer.block_number", ASCENDING)],
    ):
        block_numbers.add(record["transfer"]["block_number"])
    return list(block_numbers)


async def get_block_numbers_by_status(
    chain: ChainConfig, status: DepositStatus
) -> list[BlockNumber]:
    collection = get_collection(chain)
    query = {"transfer.chain_symbol": chain.chain_symbol, "status": status.value}
    block_numbers = set()
    async for record in collection.find(
        query,
        sort=[("transfer.block_number", ASCENDING)],
    ):
        block_numbers.add(record["transfer"]["block_number"])
    return list(block_numbers)


async def upsert_deposit(chain: ChainConfig, deposit: Deposit):
    collection = get_collection(chain)
    update = {
        "$set": deposit.model_dump(mode="json"),
    }
    filter_ = {
        "transfer.tx_hash": deposit.transfer.tx_hash,
        "transfer.chain_symbol": deposit.transfer.chain_symbol,
    }
    await collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_deposits(chain: ChainConfig, deposits: list[Deposit]):
    await asyncio.gather(*[upsert_deposit(chain, deposit) for deposit in deposits])
