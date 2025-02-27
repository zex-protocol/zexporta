import asyncio
import logging
import logging.config

from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3

from zexporta.bots.custom_types import BotToken
from zexporta.custom_types import ChecksumAddress
from zexporta.utils.abi import ERC20_ABI
from zexporta.utils.logger import ChainLoggerAdapter


async def send_deposit(
    w3: AsyncWeb3,
    monitoring_token: BotToken,
    account: LocalAccount,
    user_address: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter,
):
    ERC20_token = w3.eth.contract(address=monitoring_token.address, abi=ERC20_ABI)
    nonce = await w3.eth.get_transaction_count(account.address, "pending")
    tx = await ERC20_token.functions.transfer(user_address, monitoring_token.amount).build_transaction(
        {"from": account.address, "nonce": nonce}
    )
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")
    return tx_hash


async def wait_for_transaction_receipt(w3, tx_hash, logger):
    while True:
        try:
            receipt = await w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except Exception as e:
            logger.debug(f"Waiting for transaction receipt: {e}")
        await asyncio.sleep(5)
