from zex_deposit.custom_types import BlockNumber, ChainId

from .database import chain_collection


async def upsert_chain_last_observed_block(
    chain_id: ChainId, block_number: BlockNumber | int
):
    query = {"chainId": chain_id.value}
    update = {
        "$set": {
            "last_observed_block": block_number,
        }
    }

    result = await chain_collection.update_one(query, update, upsert=True)
    return result


async def get_last_observed_block(chain_id: ChainId) -> BlockNumber | None:
    query = {"chainId": chain_id.value}
    result = await chain_collection.find_one(query)
    if result:
        return result("last_observed_block")
    else:
        return None


async def upsert_chain_last_withdraw_nonce(chain_id: ChainId, nonce: int):
    query = {"chainId": chain_id.value}
    update = {
        "$set": {
            "last_withdraw_nonce": nonce,
        }
    }

    await chain_collection.update_one(query, update, upsert=True)


async def get_last_withdraw_nonce(chain_id: ChainId) -> int:
    query = {"chainId": chain_id.value}
    result = await chain_collection.find_one(query)
    if result:
        return result.get("last_withdraw_nonce", -1)
    else:
        return -1
