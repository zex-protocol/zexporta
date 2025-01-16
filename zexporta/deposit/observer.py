import asyncio
import logging.config

import sentry_sdk

from zexporta.clients import get_btc_async_client
from zexporta.custom_types import BTCConfig, ChainConfig
from zexporta.db.address import get_active_address, insert_new_address_to_db
from zexporta.db.chain import (
    get_last_observed_block,
    upsert_chain_last_observed_block,
)
from zexporta.db.deposit import insert_deposits_if_not_exists
from zexporta.utils.btc import extract_btc_transfer_from_block
from zexporta.utils.btc_observer import BTCObserver
from zexporta.utils.evm_observer import Observer
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.web3 import (
    extract_transfer_from_block,
    get_web3_async_client,
)

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/observer.log"))
logger = logging.getLogger(__name__)


OBSERVERS = {BTCConfig: BTCObserver, ChainConfig: Observer}

CLIENTS_GETTER = {BTCConfig: get_btc_async_client, ChainConfig: get_web3_async_client}

EXTRACTORS = {
    BTCConfig: extract_btc_transfer_from_block,
    ChainConfig: extract_transfer_from_block,
}


def get_chain_observer(chain: ChainConfig | BTCConfig):
    observer = OBSERVERS[type(chain)]
    client = CLIENTS_GETTER[type(chain)]
    return observer(client=client(chain), chain=chain)


async def observe_deposit(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    last_observed_block = await get_last_observed_block(chain.chain_id)

    observer = get_chain_observer(chain=chain)

    while True:
        latest_block = await observer.get_latest_block_number()
        if last_observed_block is not None and last_observed_block == latest_block:
            _logger.info(f"Block {last_observed_block} already observed continue")
            await asyncio.sleep(chain.delay)
            continue
        last_observed_block = last_observed_block or latest_block
        to_block = min(latest_block, last_observed_block + chain.batch_block_size)
        if last_observed_block >= to_block:
            _logger.warning(
                f"last_observed_block: {last_observed_block} is bigger then to_block {to_block}"
            )
            continue
        await insert_new_address_to_db()
        accepted_addresses = await get_active_address(chain)
        accepted_transfers = await observer.observe(
            last_observed_block + 1,
            latest_block,
            accepted_addresses,
            EXTRACTORS[type(chain)],
            logger=_logger,
            batch_size=chain.batch_block_size,
            max_delay_per_block_batch=chain.delay,
        )

        if len(accepted_transfers) > 0:
            await insert_deposits_if_not_exists(accepted_transfers)
        await upsert_chain_last_observed_block(chain.chain_id, latest_block)
        last_observed_block = latest_block


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(observe_deposit(chain)) for chain in CHAINS_CONFIG.values()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
