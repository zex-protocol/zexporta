import asyncio

from zexporta.custom_types import BlockNumber, ChainId

from .collections import db


async def __create_chain_index():
    await _chain_collection.create_index("chain_id", unique=True)


_chain_collection = db["chain"]
asyncio.run(__create_chain_index())


async def upsert_chain_last_observed_block(
    chain_id: ChainId, block_number: BlockNumber | int
):
    query = {"chain_id": chain_id.value}
    update = {
        "$set": {
            "last_observed_block": block_number,
        }
    }

    result = await _chain_collection.update_one(query, update, upsert=True)
    return result


async def get_last_observed_block(chain_id: ChainId) -> BlockNumber | None:
    query = {"chain_id": chain_id.value}
    result = await _chain_collection.find_one(query)
    if result:
        return result.get("last_observed_block")
    else:
        return None


async def upsert_chain_last_withdraw_nonce(chain_id: ChainId, nonce: int):
    query = {"chain_id": chain_id.value}
    update = {
        "$set": {
            "last_withdraw_nonce": nonce,
        }
    }

    await _chain_collection.update_one(query, update, upsert=True)


async def get_last_withdraw_nonce(chain_id: ChainId) -> int:
    query = {"chain_id": chain_id.value}
    result = await _chain_collection.find_one(query)
    if result:
        return result.get("last_withdraw_nonce", -1)
    else:
        return -1
