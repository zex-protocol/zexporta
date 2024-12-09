import asyncio
from logging import LoggerAdapter

import httpx

from zex_deposit.custom_types import ChainConfig, WithdrawRequest
from zex_deposit.utils.encoder import get_withdraw_hash
from zex_deposit.utils.zex_api import get_zex_withdraw

limit_tx = 1


async def get_withdraw_request(
    chain: ChainConfig, vault_nonce: int, logger: LoggerAdapter
) -> WithdrawRequest:
    try:
        client = httpx.AsyncClient()

        return await get_zex_withdraw(
            client, chain, offset=vault_nonce, limit=vault_nonce + 1
        )
    finally:
        await client.aclose()


def withdraw(chain: ChainConfig, vault_nonce: int, logger: LoggerAdapter):
    withdraw_request = asyncio.run(get_withdraw_request(chain, vault_nonce, logger))
    zex_withdraw_hash = get_withdraw_hash(withdraw_request, chain)

    logger.info(f"hash for withdraw is: {zex_withdraw_hash}")
    return {
        "hash": zex_withdraw_hash,
        "data": {**withdraw_request.model_dump(), "chain_id": chain.chain_id},
    }
