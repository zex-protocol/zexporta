from pymongo import AsyncMongoClient
import asyncio

from .config import MONGO_URI

from zexporta.custom_types import ChainSymbol, UserId

client = AsyncMongoClient(MONGO_URI)
db = client["test_token_transfer_database"]


async def __create_test_token_transfer():
    await _test_token_transfer_collection.create_index("chain_symbol", unique=True)


_test_token_transfer_collection = db["test_token_transfer"]
asyncio.run(__create_test_token_transfer())


async def upsert_last_transferred_id(chain_symbol: ChainSymbol, user_id: UserId):
    query = {"chain_symbol": chain_symbol.value}
    update = {
        "$set": {
            "last_user_id": user_id,
        }
    }

    result = await _test_token_transfer_collection.update_one(
        query, update, upsert=True
    )
    return result


async def get_last_transferred_id(chain_symbol: ChainSymbol) -> UserId | None:
    query = {"chain_symbol": chain_symbol.value}
    result = await _test_token_transfer_collection.find_one(query)
    if result:
        return result.get("last_user_id")
    else:
        return None
