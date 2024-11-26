from contextlib import asynccontextmanager
from enum import Enum

import httpx

from zex_deposit.custom_types import BlockNumber, ChainConfig, UserId

ZEX_BASE_URL = "https://api.zex.zellular.xyz/v1"


class ZexPath(Enum):
    LAST_USER_ID = "/users/latest-id"
    DEPOSIT = "/deposit"
    LATEST_BLOCK = "/block/latest"
    WITHDRAWS = "/withdraws"


class ZexAPIError(Exception):
    pass


@asynccontextmanager
async def get_async_client():
    async with httpx.AsyncClient() as client:
        yield client


async def get_last_zex_user_id(async_client: httpx.AsyncClient) -> UserId | None:
    try:
        res = await async_client.get(f"{ZEX_BASE_URL}{ZexPath.LAST_USER_ID.value}")
        res.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise ZexAPIError(e)
    else:
        return res.json().get("id")


async def send_deposits(async_client: httpx.AsyncClient, data: list):
    try:
        res = await async_client.post(
            url=f"{ZEX_BASE_URL}{ZexPath.DEPOSIT.value}",
            json=data,
        )
        res.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise ZexAPIError(e)
    return res.json()


async def get_zex_latest_block(
        async_client: httpx.AsyncClient, chain: ChainConfig
) -> BlockNumber | None:
    try:
        res = await async_client.get(
            url=f"{ZEX_BASE_URL}{ZexPath.LATEST_BLOCK.value}",
            params={"chain": chain.symbol},
        )
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise ZexAPIError(e)
    return res.json().get("block")


async def get_zex_withdraw(async_client: httpx.AsyncClient, chain: ChainConfig, offset: int):
    try:
        res = await async_client.get(
            url=f"{ZEX_BASE_URL}{ZexPath.WITHDRAWS.value}",
            params={
                "chain": chain.symbol,
                "offset": offset,
                "limit": 1
            },
            headers={
                "accept": "application/json"
            },
        )
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise ZexAPIError(e)
    return res.json()
