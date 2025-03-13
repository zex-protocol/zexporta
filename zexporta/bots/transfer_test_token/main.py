import asyncio
import logging
import logging.config

from clients.evm.client import compute_create2_address, get_evm_async_client
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3

from zexporta.bots.custom_types import BotToken
from zexporta.bots.transfer_test_token.config import (
    HOLDER_PRIVATE_KEY,
    LOGGER_PATH,
    TEST_TOKENS,
)
from zexporta.bots.transfer_test_token.database import (
    get_last_transferred_id,
    upsert_last_transferred_id,
)
from zexporta.bots.utils.deposit import send_deposit
from zexporta.config import (
    CHAINS_CONFIG,
)
from zexporta.custom_types import ChecksumAddress, EVMConfig, UserId
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.zex_api import ZexAPIError, get_async_client, get_last_zex_user_id

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/transfer_test_token_bot.log"))
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
    test_tokens: list[BotToken],
    account: LocalAccount,
    user_address: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter,
):
    for test_token in test_tokens:
        await send_deposit(w3, test_token, account, user_address, logger)


async def transfer_test_tokens(chain: EVMConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    w3 = get_evm_async_client(chain, _logger).client
    account = w3.eth.account.from_key(HOLDER_PRIVATE_KEY)
    test_tokens = [token for token in TEST_TOKENS if token.chain_symbol == chain.chain_symbol]
    if len(test_tokens) == 0:
        _logger.error("No token for transfer found")

    while True:
        last_transferred_user_id = await get_last_transferred_id(chain.chain_symbol) or 0

        last_user_id = await _get_last_user_id() or 0

        if last_transferred_user_id == last_user_id:
            _logger.info("There is no new user to transfer to")
            await asyncio.sleep(chain.delay)

        for id in range(last_transferred_user_id + 1, last_user_id + 1):
            _logger.info(f"Initiate transferring to user with id: {id}")

            user_address = compute_create2_address(
                salt=id,
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
        if isinstance(chain, EVMConfig)
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
