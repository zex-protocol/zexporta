import asyncio

from zexporta.custom_types import ChainId, ChecksumAddress

from .collections import db


async def __create_token_index():
    await _token_collection.create_index(("token_address", "chain_id"), unique=True)


_token_collection = db["token"]
asyncio.run(__create_token_index())


async def get_decimals(chain_id: int, token_address: ChecksumAddress) -> int | None:
    result = await _token_collection.find_one(
        {"chain_id": chain_id, "token_address": token_address},
        projection={"decimals": 1},
    )
    return result["decimals"] if result else None


async def insert_token(
    chain_id: ChainId, token_address: ChecksumAddress, decimals: int
) -> None:
    await _token_collection.insert_one(
        {
            "chain_id": chain_id.value,
            "token_address": token_address,
            "decimals": decimals,
        }
    )
