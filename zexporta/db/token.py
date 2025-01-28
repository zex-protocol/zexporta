import asyncio

from zexporta.custom_types import Address

from .collections import db


async def __create_token_index():
    await _token_collection.create_index(("token_address", "chain_symbol"), unique=True)


_token_collection = db["token"]
asyncio.run(__create_token_index())


async def get_decimals(chain_symbol: str, token_address: Address) -> int | None:
    result = await _token_collection.find_one(
        {"chain_symbol": chain_symbol, "token_address": token_address},
        projection={"decimals": 1},
    )
    return result["decimals"] if result else None


async def insert_token(
    chain_symbol: str, token_address: Address, decimals: int
) -> None:
    await _token_collection.insert_one(
        {
            "chain_symbol": chain_symbol,
            "token_address": token_address,
            "decimals": decimals,
        }
    )
