import asyncio
import logging.config
from unittest.mock import DEFAULT

import sentry_sdk
from eth_typing import ChecksumAddress

from zex_deposit.clients import get_btc_async_client
from zex_deposit.custom_types import ChainConfig, RawTransfer
from zex_deposit.db.address import get_active_address, insert_new_address_to_db
from zex_deposit.db.chain import (
    get_last_observed_block,
    upsert_chain_last_observed_block,
)
from zex_deposit.db.transfer import insert_transfers_if_not_exists
from zex_deposit.utils.btc import extract_btc_transfer_from_block
from zex_deposit.utils.btc_observer import BTCObserver
from zex_deposit.utils.evm_observer import Observer
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.web3 import (
    extract_transfer_from_block,
    get_web3_async_client,
)

from .config import CHAINS_CONFIG, LOGGER_PATH, SENTRY_DNS

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/observer.log"))
logger = logging.getLogger(__name__)


async def filter_transfer(
    transfers: list[RawTransfer], accepted_addresses: set[ChecksumAddress]
) -> tuple[RawTransfer, ...]:
    return tuple(filter(lambda transfer: transfer.to in accepted_addresses, transfers))


OBSERVERS = {"BTC": BTCObserver, DEFAULT: Observer}

CLIENTS_GETTER = {"BTC": get_btc_async_client, DEFAULT: get_web3_async_client}

EXTRACTORS = {
    "BTC": extract_btc_transfer_from_block,
    DEFAULT: extract_transfer_from_block,
}


def get_chain_observer(chain: ChainConfig):
    observer = OBSERVERS.get(chain.symbol, OBSERVERS[DEFAULT])
    client = CLIENTS_GETTER.get(chain.symbol, CLIENTS_GETTER[DEFAULT])
    return observer(client=client, chain=chain)


async def observe_deposit(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    last_observed_block = await get_last_observed_block(chain.chain_id)

    observer = get_chain_observer(chain=chain)

    while True:
        accepted_addresses = await get_active_address()
        latest_block = await observer.get_latest_block_number()
        if last_observed_block is not None and last_observed_block == latest_block:
            _logger.info(f"Block {last_observed_block} already observed continue")
            await asyncio.sleep(chain.delay)
            continue
        last_observed_block = last_observed_block or latest_block
        if last_observed_block >= latest_block:
            _logger.warning(
                f"last_observed_block: {last_observed_block} is bigger then latest_block {latest_block}"
            )
            continue
        await insert_new_address_to_db()

        accepted_transfers = await observer.observe(
            last_observed_block + 1,
            latest_block,
            accepted_addresses,
            EXTRACTORS.get(chain.symbol, EXTRACTORS[DEFAULT]),
            logger=_logger,
            batch_size=chain.batch_block_size,
            max_delay_per_block_batch=chain.delay,
        )

        if len(accepted_transfers) > 0:
            await insert_transfers_if_not_exists(accepted_transfers)
        # todo :: fix last_observed_block race condition ()
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
