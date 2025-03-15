import asyncio
from functools import lru_cache

from zexporta.custom_types import Address
from zexporta.db.db import get_db_connection


async def __create_token_index(collection):
    await collection.create_index(("token_address", "chain_symbol"), unique=True)


@lru_cache()
def get_collection():
    collection = get_db_connection()["token"]
    asyncio.run_coroutine_threadsafe(
        __create_token_index(collection),
        asyncio.get_event_loop(),
    )
    return collection


async def get_decimals(chain_symbol: str, token_address: Address) -> int | None:
    result = await get_collection().find_one(
        {"chain_symbol": chain_symbol, "token_address": token_address},
        projection={"decimals": 1},
    )
    return result["decimals"] if result else None


async def insert_token(chain_symbol: str, token_address: Address, decimals: int) -> None:
    await get_collection().insert_one(
        {
            "chain_symbol": chain_symbol,
            "token_address": token_address,
            "decimals": decimals,
        }
    )
