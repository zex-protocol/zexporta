import asyncio
from typing import Iterable

from pymongo import ASCENDING

from zex_deposit.custom_types import (
    BlockNumber,
    ChainId,
    WithdrawRequest,
    WithdrawStatus,
)
from zex_deposit.db.collections import withdraw_collection


async def insert_withdraw_if_not_exists(withdraw: WithdrawRequest):
    query = {
        "chain_id": withdraw.chain_id,
        "nonce": withdraw.nonce,
    }
    record = await withdraw_collection.find_one(query)
    if not record:
        await withdraw_collection.insert_one(withdraw.model_dump(mode="json"))


async def insert_withdraws_if_not_exists(withdraws: Iterable[WithdrawRequest]):
    await asyncio.gather(
        *[insert_withdraw_if_not_exists(withdraw) for withdraw in withdraws]
    )


async def upsert_withdraw(withdraw: WithdrawRequest):
    update = {
        "$set": withdraw.model_dump(mode="json"),
    }
    filter_ = {
        "nonce": withdraw.nonce,
        "chain_id": withdraw.chain_id,
    }
    await withdraw_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_withdraws(withdraws: list[WithdrawRequest]):
    await asyncio.gather(*[upsert_withdraw(withdraw) for withdraw in withdraws])


async def find_withdraws_by_status(
    status: WithdrawStatus,
    chain_id: ChainId,
    nonce: BlockNumber | int = 0,
) -> list[WithdrawRequest]:
    res = []
    query = {
        "status": status.value,
        "chain_id": chain_id.value,
        "nonce": {"$gte": nonce},
    }
    async for record in withdraw_collection.find(query, sort={"nonce": ASCENDING}):
        res.append(WithdrawRequest(**record))
    return res


async def find_withdraw_by_nonce(
    chain_id: ChainId,
    nonce,
) -> WithdrawRequest | None:
    query = {
        "chain_id": chain_id.value,
        "nonce": nonce,
    }
    record = await withdraw_collection.find_one(query)

    if record is not None:
        return WithdrawRequest(**record)
    return None
