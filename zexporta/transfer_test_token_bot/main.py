import asyncio
import logging
import logging.config

from eth_account.signers.local import LocalAccount
from eth_typing import HexStr
from web3 import AsyncWeb3

from zexporta.config import (
    CHAINS_CONFIG,
    USER_DEPOSIT_FACTORY_ADDRESS,
    USER_DEPOSIT_BYTECODE_HASH,
)
from zexporta.custom_types import ChecksumAddress, EVMConfig, UserId
from zexporta.transfer_test_token_bot.config import (
    HOLDER_PRIVATE_KEY,
    TEST_TOKENS,
    LOGGER_PATH,
)
from zexporta.transfer_test_token_bot.custom_types import TestToken
from zexporta.transfer_test_token_bot.database import (
    get_last_transferred_id,
    upsert_last_transferred_id,
)
from zexporta.utils.abi import ERC20_ABI
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.web3 import async_web3_factory, compute_create2_address
from zexporta.utils.zex_api import get_async_client, get_last_zex_user_id, ZexAPIError

logging.config.dictConfig(
    get_logger_config(logger_path=f"{LOGGER_PATH}/transfer_test_token_bot.log")
)
logger = logging.getLogger(__name__)


async def _get_last_user_id() -> UserId | None:
    async with get_async_client() as client:
        try:
            last_zex_user_id = await get_last_zex_user_id(client)
        except ZexAPIError as e:
            logger.error(f"Error in Zex API: {e}")
            return None
    return last_zex_user_id


async def _send_deposits(
    w3: AsyncWeb3,
    test_tokens: list[TestToken],
    account: LocalAccount,
    user_address: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter,
):
    nonce = await w3.eth.get_transaction_count(account.address)
    for test_token in test_tokens:
        ERC20_token = w3.eth.contract(address=test_token.address, abi=ERC20_ABI)
        tx = await ERC20_token.functions.transfer(
            user_address, test_token.amount
        ).build_transaction({"from": account.address, "nonce": nonce})
        signed_tx = account.sign_transaction(tx)
        try:
            tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Transaction sent. Hash: {tx_hash.hex()}")
            receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(
                f"Transaction mined. Hash: {tx_hash.hex()}, Block: {receipt.blockNumber}"
            )
            nonce += 1
        except asyncio.TimeoutError:
            logger.error(f"Transaction timed out. Deposit address: {user_address}")


async def transfer_test_tokens(chain: EVMConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    w3 = await async_web3_factory(chain)
    account = w3.eth.account.from_key(HOLDER_PRIVATE_KEY)
    test_tokens = [token for token in TEST_TOKENS if token.chain_id == chain.chain_id]
    if len(test_tokens) == 0:
        _logger.error("No token for transfer found")

    while True:
        last_transferred_user_id = await get_last_transferred_id(chain.chain_symbol)

        if last_transferred_user_id is None:
            last_transferred_user_id = 0

        last_user_id = await _get_last_user_id()

        if last_user_id is not None and last_transferred_user_id == last_user_id:
            _logger.info("There is no new user to transfer to")
            await asyncio.sleep(chain.delay)

        for id in range(last_transferred_user_id + 1, last_user_id + 1):
            _logger.info(f"Initiate transferring to user with id: {id}")

            user_address = compute_create2_address(
                deployer_address=USER_DEPOSIT_FACTORY_ADDRESS,
                salt=id,
                bytecode_hash=HexStr(USER_DEPOSIT_BYTECODE_HASH),
            )

            _logger.info(f"Deposit address for user with id: {id} is {user_address}")

            await _send_deposits(
                w3,
                test_tokens,
                account=account,
                user_address=user_address,
                logger=_logger,
            )
            await upsert_last_transferred_id(chain.chain_symbol, id)
            _logger.info(f"Transferring to user with id: {id} is completed")


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(transfer_test_tokens(chain))
        for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
