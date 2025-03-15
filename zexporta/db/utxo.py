import asyncio
from functools import lru_cache
from typing import Iterable

from pymongo import DESCENDING

from zexporta.custom_types import (
    UTXO,
    Deposit,
    TxHash,
    UTXOStatus,
)

from .db import get_db_connection


async def __create_indexes(collection):
    await collection.create_index(("tx_hash", "index"), unique=True)


@lru_cache()
def get_collection():
    collection = get_db_connection()["btc_utxo"]
    asyncio.run_coroutine_threadsafe(
        __create_indexes(collection),
        asyncio.get_event_loop(),
    )
    return collection


async def insert_utxo_if_not_exists(utxo: UTXO):
    query = {
        "tx_hash": utxo.tx_hash,
        "index": utxo.index,
    }
    record = await get_collection().find_one(query)
    if not record:
        await get_collection().insert_one(utxo.model_dump(mode="json"))


async def insert_utxos_if_not_exists(utxos: Iterable[UTXO]):
    await asyncio.gather(*[insert_utxo_if_not_exists(utxo) for utxo in utxos])


async def find_utxo_by_status(
    status: UTXOStatus,
    limit: int | None = None,
) -> list[UTXO]:
    res = []
    query = {
        "status": status.value,
    }

    async for record in get_collection().find(query, sort={"amount": DESCENDING}):
        res.append(UTXO(**record))
        if limit and len(record) >= limit:
            break
    return res


async def update_utxo_status(tx_hash: TxHash, new_status: UTXOStatus):
    await get_collection().update_one({"tx_hash": tx_hash}, {"$set": {"status": new_status}})


async def delete_utxo(tx_hash: TxHash):
    await get_collection().delete_one({"tx_hash": tx_hash})


async def upsert_utxo(utxo: UTXO):
    update = {
        "$set": utxo.model_dump(mode="json"),
    }
    filter_ = {
        "tx_hash": utxo.tx_hash,
    }
    await get_collection().update_one(filter=filter_, update=update, upsert=True)


async def upsert_utxos(utxos: list[UTXO]):
    await asyncio.gather(*[upsert_utxo(utxo) for utxo in utxos])


async def populate_deposits_utxos(deposits: list[Deposit]):
    utxos = serialize_utxo_from_deposit(deposits)
    await insert_utxos_if_not_exists(utxos)


def serialize_utxo_from_deposit(deposits: list[Deposit]):
    utxos = []
    for deposit in deposits:
        transfer = deposit.transfer
        utxos.append(
            UTXO(
                status=UTXOStatus.UNSPENT,
                tx_hash=transfer.tx_hash,
                amount=transfer.value,
                index=transfer.index,
                address=transfer.to,
                salt=deposit.user_id,
            )
        )
    return utxos
