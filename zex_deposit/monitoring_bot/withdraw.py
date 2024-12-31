import asyncio
import struct
import time
from decimal import Decimal

import httpx
from web3 import Web3

from zex_deposit.custom_types import ChainConfig
from zex_deposit.utils.logger import ChainLoggerAdapter
from zex_deposit.utils.web3 import (
    async_web3_factory,
    get_ERC20_balance,
    get_signed_data,
)
from zex_deposit.utils.zex_api import get_user_withdraw_nonce, send_withdraw_request

from .config import (
    MONITORING_TOKENS,
    TEST_USER_ID,
    TEST_USER_PRIVATE_KEY,
    WITHDRAW_DESTINATION,
    WITHDRAW_PUBLIC_KEY,
)
from .custom_types import MonitoringToke

WITHDRAW_OPERATION = "w"


class WithdrawError(Exception):
    "raise when WithdrawError occurred"


def withdraw_msg(tx: bytes, logger: ChainLoggerAdapter) -> bytes:
    version, token_len = struct.unpack(">B x B", tx[:3])
    withdraw_format = f">3s {token_len}s d 20s I I 33s"
    unpacked = struct.unpack(
        withdraw_format, tx[3 : 3 + struct.calcsize(withdraw_format)]
    )
    token_chain, token_name, amount, destination, t, nonce, public = unpacked
    token_chain = token_chain.decode("ascii")
    token_name = token_name.decode("ascii")
    msg = f"v: {version}\n"
    msg += "name: withdraw\n"
    msg += f"token chain: {token_chain}\n"
    msg += f"token name: {token_name}\n"
    msg += f"amount: {amount}\n"
    msg += f'to: {"0x" + destination.hex()}\n'
    msg += f"t: {t}\n"
    msg += f"nonce: {nonce}\n"
    msg += f"public: {public.hex()}\n"
    msg = "\x19Ethereum Signed Message:\n" + str(len(msg)) + msg
    logger.debug("withdraw message: %s", msg)
    return msg.encode()


def create_tx(
    chain: ChainConfig, monitoring_token: MonitoringToke, nonce: int
) -> bytes:
    # Prepare withdrawal data
    version = 1

    token_chain = chain.symbol.encode()
    token_name = monitoring_token.symbol.encode()
    destination = bytes.fromhex(WITHDRAW_DESTINATION)
    t = int(time.time())
    public = bytes.fromhex(WITHDRAW_PUBLIC_KEY)
    amount = float(Decimal(monitoring_token.amount / 10**monitoring_token.decimal))
    token_len = len(token_name)
    pack_format = f"> B 1s B 3s {token_len}s d 20s I I 33s"
    return struct.pack(
        pack_format,
        version,
        WITHDRAW_OPERATION.encode(),
        token_len,
        token_chain,
        token_name,
        amount,
        destination,
        t,
        nonce,
        public,
    )


async def monitor_withdraw(
    async_client: httpx.AsyncClient, chain: ChainConfig, logger: ChainLoggerAdapter
):
    monitoring_token = [
        token for token in MONITORING_TOKENS if token.chain_id == chain.chain_id
    ]
    if len(monitoring_token) == 0:
        raise WithdrawError("No token for monitoring found.")

    monitoring_token = monitoring_token[0]
    w3 = await async_web3_factory(chain)
    balance_before = await get_ERC20_balance(
        w3,
        contract_address=monitoring_token.address,
        wallet_address=Web3.to_checksum_address(WITHDRAW_DESTINATION),
    )
    user_withdraw_nonce = await get_user_withdraw_nonce(
        async_client, chain, TEST_USER_ID
    )
    tx = create_tx(chain, monitoring_token, user_withdraw_nonce)
    msg = withdraw_msg(tx, logger)
    signed_data = bytes.fromhex(
        get_signed_data(TEST_USER_PRIVATE_KEY, primitive=msg)[2:]
    )[1:]
    send_data = (tx + signed_data).decode("latin-1")
    await send_withdraw_request(async_client, [send_data])
    await asyncio.sleep(120)
    balance_after = await get_ERC20_balance(
        w3,
        contract_address=monitoring_token.address,
        wallet_address=Web3.to_checksum_address(WITHDRAW_DESTINATION),
    )
    if balance_after == balance_before + monitoring_token.amount:
        return
    raise WithdrawError("User balance did not increase.")
