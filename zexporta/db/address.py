import asyncio
import logging

from pymongo import DESCENDING
from web3 import Web3

from zexporta.clients import get_compute_address_function
from zexporta.custom_types import (
    Address,
    BTCConfig,
    ChainConfig,
    EVMConfig,
    UserAddress,
    UserId,
)
from zexporta.utils.zex_api import (
    ZexAPIError,
    get_async_client,
    get_last_zex_user_id,
)

from .collections import db

_address_collections = {EVMConfig: db["evm_address"], BTCConfig: db["btc_address"]}


async def __create_evm_address_index():
    await _address_collections[EVMConfig].create_index("user_id", unique=True)
    await _address_collections[EVMConfig].create_index("address", unique=True)


async def __create_btc_address_index():
    await _address_collections[BTCConfig].create_index("user_id", unique=True)
    await _address_collections[BTCConfig].create_index("address", unique=True)


async def __create_indexes():
    await __create_evm_address_index()
    await __create_btc_address_index()


asyncio.run(__create_indexes())


def get_collection(chain: ChainConfig):
    match chain:
        case EVMConfig():
            return _address_collections[EVMConfig]
        case BTCConfig():
            return _address_collections[BTCConfig]
    raise NotImplementedError()


class UserNotExists(Exception):
    pass


logger = logging.getLogger(__name__)


async def get_active_address(
    chain: ChainConfig,
) -> dict[Address, UserId]:
    res = dict()
    collection = get_collection(chain=chain)
    async for address in collection.find({"is_active": True}):
        match chain:
            case ChainConfig():
                key = Web3.to_checksum_address(address["address"])
            case BTCConfig():
                key = address["address"]
            case _:
                raise NotImplementedError("")
        res[key] = address["user_id"]
    return res


async def get_last_user_id(chain: ChainConfig) -> UserId:
    collection = get_collection(chain=chain)
    result = await collection.find_one(
        {"is_active": True}, sort=[("user_id", DESCENDING)]
    )
    if result:
        return result["user_id"]
    raise UserNotExists()


async def insert_user_address(chain: ChainConfig, address: UserAddress):
    collection = get_collection(chain=chain)
    await collection.insert_one(address.model_dump(mode="json"))


async def insert_many_user_address(
    chain: ChainConfig, users_address: list[UserAddress]
):
    collection = get_collection(chain=chain)
    await collection.insert_many(
        user_address.model_dump(mode="json") for user_address in users_address
    )


def get_users_address_to_insert(
    chain: ChainConfig, first_to_compute: UserId, last_to_compute: UserId
) -> list[UserAddress]:
    users_address_to_insert = []
    for user_id in range(first_to_compute, last_to_compute + 1):
        users_address_to_insert.append(
            UserAddress(
                user_id=user_id,
                address=get_compute_address_function(chain)(
                    user_id,
                ),
            )
        )
    return users_address_to_insert


async def insert_new_address_to_db(chain: ChainConfig):
    async with get_async_client() as client:
        try:
            last_zex_user_id = await get_last_zex_user_id(client)
        except ZexAPIError as e:
            logger.error(f"Error in Zex API: {e}")
            return

    if last_zex_user_id is None:
        return
    try:
        first_id_to_compute = await get_last_user_id(chain=chain) + 1
    except UserNotExists:
        first_id_to_compute = 0
    users_address_to_insert = get_users_address_to_insert(
        chain, first_id_to_compute, last_zex_user_id
    )
    if len(users_address_to_insert) == 0:
        return
    await insert_many_user_address(chain, users_address=users_address_to_insert)
