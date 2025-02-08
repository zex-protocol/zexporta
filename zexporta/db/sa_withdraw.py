import asyncio
from typing import Iterable

from zexporta.custom_types import (
    UTXO,
    ChainConfig,
    WithdrawRequest,
)
from zexporta.db.collections import sa_db


async def __create_sa_withdraw_index():
    await _sa_withdraw_collection.create_index(("nonce", "chain_symbol"), unique=True)


_sa_withdraw_collection = sa_db["withdraw"]
asyncio.run(__create_sa_withdraw_index())


async def insert_sa_withdraw_if_not_exists(withdraw: WithdrawRequest):
    query = {
        "chain_symbol": withdraw.chain_symbol,
        "nonce": withdraw.nonce,
    }
    record = await _sa_withdraw_collection.find_one(query)
    if not record:
        await _sa_withdraw_collection.insert_one(withdraw.model_dump(mode="json"))
        record = withdraw
    return record


async def insert_sa_withdraws_if_not_exists(withdraws: Iterable[WithdrawRequest]):
    await asyncio.gather(
        *[insert_sa_withdraw_if_not_exists(withdraw) for withdraw in withdraws]
    )


async def upsert_sa_withdraw(withdraw: WithdrawRequest):
    update = {
        "$set": withdraw.model_dump(mode="json"),
    }
    filter_ = {
        "nonce": withdraw.nonce,
        "chain_symbol": withdraw.chain_symbol,
    }
    await _sa_withdraw_collection.update_one(filter=filter_, update=update, upsert=True)


async def upsert_sa_withdraws(withdraws: list[WithdrawRequest]):
    await asyncio.gather(*[upsert_sa_withdraw(withdraw) for withdraw in withdraws])


async def find_sa_withdraws_by_utxo(
    chain: ChainConfig, utxos: list[UTXO]
) -> list[WithdrawRequest]:
    res = []
    query = {"utxos": {"$elemMatch": {"$in": utxos}}}
    async for record in await sa_db.find(query).to_list(None):
        res.append(chain.get_sa_withdraw_request_type()(**record))
    return res


async def find_sa_withdraw_by_nonce(
    chain: ChainConfig,
    nonce,
) -> WithdrawRequest | None:
    query = {
        "chain_symbol": chain.chain_symbol,
        "nonce": nonce,
    }
    record = await _sa_withdraw_collection.find_one(query)

    if record is not None:
        return chain.get_sa_withdraw_request_type()(**record)
    return None
