import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zexporta.custom_types import (
    ChainConfig,
    WithdrawRequest,
    WithdrawStatus,
)
from zexporta.db.collections import db


async def __create_withdraw_index():
    await _withdraw_collection.create_index(("nonce", "chain_symbol"), unique=True)


_withdraw_collection = db["withdraw"]
asyncio.run(__create_withdraw_index())


async def insert_withdraw_if_not_exists(withdraw: WithdrawRequest):
    query = {
        "chain_symbol": withdraw.chain_symbol,
        "nonce": withdraw.nonce,
    }
    record = await _withdraw_collection.find_one(query)
    if not record:
        await _withdraw_collection.insert_one(withdraw.model_dump(mode="json"))


async def insert_withdraws_if_not_exists(withdraws: Iterable[WithdrawRequest]):
    await asyncio.gather(*[insert_withdraw_if_not_exists(withdraw) for withdraw in withdraws])


async def upsert_withdraw(withdraw: WithdrawRequest):
    update = {
        "$set": withdraw.model_dump(mode="json"),
    }
    filter_ = {
        "nonce": withdraw.nonce,
        "chain_symbol": withdraw.chain_symbol,
    }
    await _withdraw_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_withdraws(withdraws: list[WithdrawRequest]):
    await asyncio.gather(*[upsert_withdraw(withdraw) for withdraw in withdraws])


async def find_withdraws_by_status(
    status: WithdrawStatus,
    chain: ChainConfig,
    nonce: int = 0,
) -> list[WithdrawRequest]:
    res = []
    query = {
        "status": status.value,
        "chain_symbol": chain.chain_symbol,
        "nonce": {"$gte": nonce},
    }

    async for record in _withdraw_collection.find(query, sort={"nonce": ASCENDING}):
        res.append(chain.withdraw_request_type(**record))
    return res


async def find_withdraw_by_nonce(
    chain: ChainConfig,
    nonce,
) -> WithdrawRequest | None:
    query = {
        "chain_symbol": chain.chain_symbol,
        "nonce": nonce,
    }
    record = await _withdraw_collection.find_one(query)

    if record is not None:
        return chain.withdraw_request_type(**record)
    return None
