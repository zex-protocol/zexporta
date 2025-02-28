import asyncio
from functools import lru_cache

from zexporta.custom_types import BlockNumber

from .db import get_db_connection


@lru_cache()
def get_collection():
    _chain_collection = get_db_connection()["chain"]
    asyncio.run_coroutine_threadsafe(
        _chain_collection.create_index("chain_symbol", unique=True), asyncio.get_event_loop()
    )
    return _chain_collection


async def upsert_chain_last_observed_block(chain_symbol: str, block_number: BlockNumber):
    query = {"chain_symbol": chain_symbol}
    update = {
        "$set": {
            "last_observed_block": block_number,
        }
    }

    result = await get_collection().update_one(query, update, upsert=True)
    return result


async def get_last_observed_block(chain_symbol: str) -> BlockNumber | None:
    query = {"chain_symbol": chain_symbol}
    result = await get_collection().find_one(query)
    if result:
        return result.get("last_observed_block")
    else:
        return None


async def upsert_chain_last_withdraw_nonce(chain_symbol: str, nonce: int):
    query = {"chain_symbol": chain_symbol}
    update = {
        "$set": {
            "last_withdraw_nonce": nonce,
        }
    }

    await get_collection().update_one(query, update, upsert=True)


async def get_last_withdraw_nonce(chain_symbol: str) -> int:
    query = {"chain_symbol": chain_symbol}
    result = await get_collection().find_one(query)
    if result:
        return result.get("last_withdraw_nonce", -1)
    else:
        return -1
