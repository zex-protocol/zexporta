import asyncio
import logging
import logging.config
import time

import httpx

from zexporta.custom_types import ChainConfig
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import (
    CHAINS_CONFIG,
    DELAY,
    LOGGER_PATH,
    TELEGRAM_BASE_URL,
    TELEGRAM_BOT_INFO,
    TELEGRAM_CHAT_ID,
)
from .deposit import monitor_deposit
from .withdraw import monitor_withdraw

logging.config.dictConfig(
    get_logger_config(logger_path=f"{LOGGER_PATH}/monitoring_bot.log")
)
logger = logging.getLogger(__name__)


# //sendMessage?chat_id=-4763738874&text={message}
async def send_msg_to_telegram(async_client: httpx.AsyncClient, msg: str):
    await async_client.get(
        url=f"{TELEGRAM_BASE_URL}/{TELEGRAM_BOT_INFO}/sendMessage",
        params={"text": msg, "chat_id": TELEGRAM_CHAT_ID},
    )


async def monitor(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    client = httpx.AsyncClient()
    try:
        try:
            await send_msg_to_telegram(
                client, f"🟩 Start deposit on chain {chain.symbol} ..."
            )
            _logger.info("Start monitoring deposit.")
            _ = await monitor_deposit(client, chain, _logger)
            _logger.info("Deposit was successful.")
            await send_msg_to_telegram(
                client, f"🟩 Deposit was successful on chain {chain.symbol}."
            )
        except Exception as e:
            _logger.error(f"DepositError occurred, type: {type(e)}, {str(e)}")
            await send_msg_to_telegram(
                client,
                f"🟥 Error at Deposit on chain {chain.symbol}, type: {type(e)}, {str(e)}",
            )
            return
        try:
            await send_msg_to_telegram(
                client, f"🟩 Start withdrawing on chain {chain.symbol} ..."
            )
            _logger.info("Start monitoring withdraw.")
            _ = await monitor_withdraw(client, chain, _logger)
            _logger.info("Withdraw was successful")
            await send_msg_to_telegram(
                client, f"🟩 Withdraw was successful for chin {chain.symbol}."
            )
        except Exception as e:
            _logger.error(f"WithdrawError occurred, type: {type(e)}, {e}")
            await send_msg_to_telegram(
                client,
                f"🟥 Error at Withdraw on chain {chain.symbol}, type: {type(e)}, {str(e)}",
            )
            return
    finally:
        await client.aclose()


def schedule_task(loop: asyncio.AbstractEventLoop):
    async def main():
        start_time = time.monotonic()
        _ = [await loop.create_task(monitor(chain)) for chain in CHAINS_CONFIG.values()]
        # await asyncio.gather(*tasks)
        elapsed = time.monotonic() - start_time
        delay = max(DELAY - elapsed, 0)
        loop.call_later(delay, schedule_task, loop)

    loop.create_task(main())


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    schedule_task(loop)
    loop.run_forever()
