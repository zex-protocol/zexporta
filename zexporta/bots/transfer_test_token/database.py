import asyncio

from pymongo import AsyncMongoClient

from zexporta.custom_types import UserId
from zexporta.settings import app_settings

client = AsyncMongoClient(app_settings.mongo.get_uri())
db = client["test_token_transfer_database"]


async def __create_test_token_transfer():
    await _test_token_transfer_collection.create_index("chain_symbol", unique=True)


_test_token_transfer_collection = db["test_token_transfer"]
asyncio.run(__create_test_token_transfer())


async def upsert_last_transferred_id(chain_symbol: str, user_id: UserId):
    query = {"chain_symbol": chain_symbol}
    update = {
        "$set": {
            "last_user_id": user_id,
        }
    }

    result = await _test_token_transfer_collection.update_one(query, update, upsert=True)
    return result


async def get_last_transferred_id(chain_symbol: str) -> UserId | None:
    query = {"chain_symbol": chain_symbol}
    result = await _test_token_transfer_collection.find_one(query)
    if result:
        return result.get("last_user_id")
    else:
        return None
