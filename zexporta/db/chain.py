import asyncio

from zexporta.custom_types import BlockNumber

from .collections import db


async def __create_chain_index():
    await _chain_collection.create_index("chain_symbol", unique=True)


_chain_collection = db["chain"]
asyncio.run(__create_chain_index())


async def upsert_chain_last_observed_block(chain_symbol: str, block_number: BlockNumber):
    query = {"chain_symbol": chain_symbol}
    update = {
        "$set": {
            "last_observed_block": block_number,
        }
    }

    result = await _chain_collection.update_one(query, update, upsert=True)
    return result


async def get_last_observed_block(chain_symbol: str) -> BlockNumber | None:
    query = {"chain_symbol": chain_symbol}
    result = await _chain_collection.find_one(query)
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

    await _chain_collection.update_one(query, update, upsert=True)


async def get_last_withdraw_nonce(chain_symbol: str) -> int:
    query = {"chain_symbol": chain_symbol}
    result = await _chain_collection.find_one(query)
    if result:
        return result.get("last_withdraw_nonce", -1)
    else:
        return -1
