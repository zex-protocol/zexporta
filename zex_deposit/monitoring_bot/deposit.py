import asyncio
import logging
import logging.config
from decimal import Decimal

import httpx
from eth_account.signers.local import LocalAccount
from eth_typing import HexStr
from web3 import AsyncWeb3

from zex_deposit.custom_types import ChainConfig, ChecksumAddress, UserId
from zex_deposit.monitoring_bot.config import (
    MONITORING_TOKENS,
    TEST_USER_ID,
    USER_DEPOSIT_BYTECODE_HASH,
    USER_DEPOSIT_FACTORY_ADDRESS,
    WITHDRAWER_PRIVATE_KEY,
)
from zex_deposit.utils.abi import ERC20_ABI
from zex_deposit.utils.logger import ChainLoggerAdapter
from zex_deposit.utils.web3 import async_web3_factory, compute_create2_address
from zex_deposit.utils.zex_api import get_user_asset

from .custom_types import MonitoringToke


class DepositError(Exception):
    "raise when deposit was not successful"


async def _send_deposit(
    w3: AsyncWeb3,
    monitoring_token: MonitoringToke,
    account: LocalAccount,
    user_address: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter,
):
    ERC20_token = w3.eth.contract(address=monitoring_token.address, abi=ERC20_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await ERC20_token.functions.transfer(
        user_address, monitoring_token.amount
    ).build_transaction({"from": account.address, "nonce": nonce})
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")
    return tx_hash


async def _wait_for_transaction_receipt(w3, tx_hash, logger):
    while True:
        try:
            receipt = await w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except Exception as e:
            logger.debug(f"Waiting for transaction receipt: {e}")
        await asyncio.sleep(5)


async def get_user_balance(
    client: httpx.AsyncClient, user_id: UserId, symbol: str
) -> Decimal:
    balance = [
        user_asset.free
        for user_asset in (await get_user_asset(client, user_id=user_id))
        if user_asset.asset == symbol
    ]
    if len(balance) == 0:
        return Decimal(0)
    return Decimal(balance[0])


async def monitor_deposit(
    async_client: httpx.AsyncClient, chain: ChainConfig, logger: ChainLoggerAdapter
):
    monitoring_token = [
        token for token in MONITORING_TOKENS if token.chain_id == chain.chain_id
    ]
    if len(monitoring_token) == 0:
        raise DepositError("No token for monitoring found")
    monitoring_token = monitoring_token[0]
    test_user_address = compute_create2_address(
        USER_DEPOSIT_FACTORY_ADDRESS,
        TEST_USER_ID,
        HexStr(USER_DEPOSIT_BYTECODE_HASH),
    )

    w3 = await async_web3_factory(chain)
    account = w3.eth.account.from_key(WITHDRAWER_PRIVATE_KEY)
    balance_before = await get_user_balance(
        async_client, TEST_USER_ID, monitoring_token.symbol
    )
    logger.info(f"Balance before deposit: {balance_before}")

    tx_hash = await _send_deposit(
        w3,
        monitoring_token,
        account=account,
        user_address=test_user_address,
        logger=logger,
    )
    receipt = await _wait_for_transaction_receipt(w3, tx_hash, logger)
    if receipt and receipt["status"] == 1:
        logger.info("Transaction successful.")
    else:
        raise DepositError("Transaction failed.")

    await asyncio.sleep(30)  # wait until deposit store in zex

    balance_after = await get_user_balance(
        async_client, TEST_USER_ID, monitoring_token.symbol
    )
    logger.info(f"Balance after deposit: {balance_after}")

    # Check if balance increased
    if balance_after == balance_before + Decimal(monitoring_token.amount) / Decimal(
        10**monitoring_token.decimal
    ):
        logger.info("Balance has increased. Deposit successful.")
        return
    raise DepositError("Balance is not correct, something went wrong.")
