import asyncio
from logging import LoggerAdapter

import httpx
from clients import compute_btc_address
from zellular import Zellular

from zexporta.config import SEQUENCER_APP_NAME, SEQUENCER_BASE_URL
from zexporta.custom_types import (
    UTXO,
    BTCConfig,
    BTCWithdrawRequest,
    EVMConfig,
    WithdrawRequest,
)
from zexporta.db.sa_withdraw import (
    find_sa_withdraws_by_utxo,
    insert_sa_withdraw_if_not_exists,
)
from zexporta.utils.encoder import get_evm_withdraw_hash
from zexporta.utils.zex_api import get_zex_withdraws
from zexporta.withdraw.btc_utils import get_simple_withdraw_tx

limit_tx = 1


async def get_withdraw_request(
    chain: EVMConfig, sa_withdraw_nonce: int, logger: LoggerAdapter
) -> WithdrawRequest:
    async with httpx.AsyncClient() as client:
        withdraw = (
            await get_zex_withdraws(
                client, chain, offset=sa_withdraw_nonce, limit=sa_withdraw_nonce + 1
            )
        )[0]

    return withdraw


def evm_withdraw(chain: EVMConfig, sa_withdraw_nonce: int, logger: LoggerAdapter):
    withdraw_request = asyncio.run(
        get_withdraw_request(chain, sa_withdraw_nonce, logger)
    )
    zex_withdraw_hash = get_evm_withdraw_hash(withdraw_request)

    logger.info(f"hash for withdraw is: {zex_withdraw_hash}")
    return {
        "hash": zex_withdraw_hash,
        "data": withdraw_request.model_dump(mode="json"),
    }


async def btc_withdraw(
    chain: BTCConfig, sa_withdraw_nonce: int, data: dict, logger: LoggerAdapter
):
    withdraw_request = asyncio.run(
        get_withdraw_request(chain, sa_withdraw_nonce, logger)
    )
    zellular = Zellular(SEQUENCER_APP_NAME, SEQUENCER_BASE_URL)
    data = zellular.get_finalized(withdraw_request.zellular_index, None)[0]
    withdraw_request_utxos = [UTXO(**param) for param in data.get("utxos", [])]

    db_withdraw = await insert_sa_withdraw_if_not_exists(BTCWithdrawRequest(**data))
    if db_withdraw.utxos != withdraw_request_utxos:
        raise ValueError(
            f"Different Utxos:{db_withdraw.utxos}, {withdraw_request_utxos}"
        )

    withdraws = await find_sa_withdraws_by_utxo(chain, withdraw_request_utxos)
    nonces = {withdraw.nonce for withdraw in withdraws}
    if not nonces or len(nonces) > 1 or nonces[0] != withdraw_request.nonce:
        raise ValueError(f"Double Spending Utxos Error, withdraw_nonces:{nonces}")

    for utxo in withdraw_request_utxos:
        assert utxo.address == compute_btc_address(utxo.user_id)

    tx, _ = get_simple_withdraw_tx(
        withdraw_request, chain.vault_address, utxos=withdraw_request_utxos
    )
    zex_withdraw_hash = tx.to_hex()
    logger.info(f"hash for withdraw is: {zex_withdraw_hash}")

    return {
        "hash": zex_withdraw_hash,
        "data": withdraw_request.model_dump(mode="json"),
    }
