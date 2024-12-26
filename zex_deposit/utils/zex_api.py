from contextlib import asynccontextmanager
from enum import StrEnum
from json import JSONDecodeError

import httpx

from zex_deposit.config import ZEX_BASE_URL
from zex_deposit.custom_types import (
    BlockNumber,
    ChainConfig,
    UserId,
    WithdrawRequest,
)


class ZexPath(StrEnum):
    LAST_USER_ID = "/users/latest-id"
    DEPOSIT = "/deposit"
    LATEST_BLOCK = "/block/latest"
    WITHDRAWS = "/withdraws"
    LAST_WITHDRAW_NONCE = "/withdraw/nonce/last"


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


async def send_deposits(async_client: httpx.AsyncClient, withdraw: list):
    try:
        res = await async_client.post(
            url=f"{ZEX_BASE_URL}{ZexPath.DEPOSIT.value}",
            json=withdraw,
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
        res.raise_for_status()
        return res.json().get("block")
    except (
        httpx.RequestError,
        httpx.HTTPStatusError,
        JSONDecodeError,
        AttributeError,
    ) as e:
        raise ZexAPIError(e)


async def get_zex_last_withdraw_nonce(
    async_client: httpx.AsyncClient, chain: ChainConfig
) -> int:
    try:
        res = await async_client.get(
            url=f"{ZEX_BASE_URL}{ZexPath.LAST_WITHDRAW_NONCE.value}",
            params={"chain": chain.symbol},
        )
        if res.status_code == httpx.codes.NOT_FOUND:
            return -1
        res.raise_for_status()
        return res.json().get("nonce")
    except (
        httpx.RequestError,
        httpx.HTTPStatusError,
        JSONDecodeError,
        AttributeError,
    ) as e:
        raise ZexAPIError(e)


async def get_zex_withdraws(
    async_client: httpx.AsyncClient,
    chain: ChainConfig,
    offset: int,
    limit: int | None = None,
) -> list[WithdrawRequest]:
    from web3 import Web3

    params = dict()
    if limit is not None:
        params["limit"] = limit
    try:
        res = await async_client.get(
            url=f"{ZEX_BASE_URL}{ZexPath.WITHDRAWS.value}",
            params={"chain": chain.symbol, "offset": offset, **params},
            headers={"accept": "application/json"},
        )
        res.raise_for_status()
        withdraws = res.json()
        if not len(withdraws):
            raise ZexAPIError("Active withdraw not been found.")
        return [
            WithdrawRequest(
                amount=withdraw.get("amount"),
                nonce=withdraw.get("nonce"),
                recipient=Web3.to_checksum_address(withdraw.get("destination")),
                token_address=Web3.to_checksum_address(withdraw.get("tokenContract")),
                chain_id=chain.chain_id,
            )
            for withdraw in withdraws
        ]
    except (httpx.RequestError, httpx.HTTPStatusError, JSONDecodeError) as e:
        raise ZexAPIError(e)
