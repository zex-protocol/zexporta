import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zexporta.custom_types import (
    BlockNumber,
    ChainId,
    EVMWithdrawRequest,
    WithdrawStatus,
)
from zexporta.db.collections import db


async def __create_withdraw_index():
    await _withdraw_collection.create_index(("nonce", "chain_id"), unique=True)


_withdraw_collection = db["withdraw"]
asyncio.run(__create_withdraw_index())


async def insert_withdraw_if_not_exists(withdraw: EVMWithdrawRequest):
    query = {
        "chain_id": withdraw.chain_id.value,
        "nonce": withdraw.nonce,
    }
    record = await _withdraw_collection.find_one(query)
    if not record:
        await _withdraw_collection.insert_one(withdraw.model_dump(mode="json"))


async def insert_withdraws_if_not_exists(withdraws: Iterable[EVMWithdrawRequest]):
    await asyncio.gather(*[insert_withdraw_if_not_exists(withdraw) for withdraw in withdraws])


async def upsert_withdraw(withdraw: EVMWithdrawRequest):
    update = {
        "$set": withdraw.model_dump(mode="json"),
    }
    filter_ = {
        "nonce": withdraw.nonce,
        "chain_id": withdraw.chain_id.value,
    }
    await _withdraw_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_withdraws(withdraws: list[EVMWithdrawRequest]):
    await asyncio.gather(*[upsert_withdraw(withdraw) for withdraw in withdraws])


async def find_withdraws_by_status(
    status: WithdrawStatus,
    chain_id: ChainId,
    nonce: BlockNumber | int = 0,
) -> list[EVMWithdrawRequest]:
    res = []
    query = {
        "status": status.value,
        "chain_id": chain_id.value,
        "nonce": {"$gte": nonce},
    }
    async for record in _withdraw_collection.find(query, sort={"nonce": ASCENDING}):
        res.append(EVMWithdrawRequest(**record))
    return res


async def find_withdraw_by_nonce(
    chain_id: ChainId,
    nonce,
) -> EVMWithdrawRequest | None:
    query = {
        "chain_id": chain_id.value,
        "nonce": nonce,
    }
    record = await _withdraw_collection.find_one(query)

    if record is not None:
        return EVMWithdrawRequest(**record)
    return None
