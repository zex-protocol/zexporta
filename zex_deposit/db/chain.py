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


async def get_last_observed_block(chain_id):
    query = {"chainId": chain_id}
    result = await chain_collection.find_one(query)
    if result:
        return result["last_observed_block"]
    else:
        return None
