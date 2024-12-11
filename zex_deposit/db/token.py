from zex_deposit.custom_types import ChainId, ChecksumAddress

from .collections import token_collection


async def get_decimals(chain_id: int, token_address: ChecksumAddress) -> int | None:
    result = await token_collection.find_one(
        {"chain_id": chain_id, "token_address": token_address},
        projection={"decimals": 1},
    )
    return result["decimals"] if result else None


async def insert_token(
    chain_id: ChainId, token_address: ChecksumAddress, decimals: int
) -> None:
    await token_collection.insert_one(
        {
            "chain_id": chain_id.value,
            "token_address": token_address,
            "decimals": decimals,
        }
    )
