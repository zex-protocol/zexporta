import asyncio
import logging.config

from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config

from ...clients import get_btc_async_client
from ...custom_types import ChainConfig, TransferStatus
from ...db.transfer import find_transactions_by_status, to_finalized
from ...utils.btc import get_btc_finalized_block_number
from ..config import LOGGER_PATH

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


# min block confirmation 6
async def update_btc_finalized_transfers(
    chain: ChainConfig, delay: int = 10, block_confirmation: int = 6
):
    _logger = ChainLoggerAdapter(logger, chain.symbol)
    client = get_btc_async_client(chain)
    while True:
        finalized_block_number = await get_btc_finalized_block_number(
            client=client, chain=chain
        )
        pending_transfers = await find_transactions_by_status(
            chain_id=chain.chain_id,
            to_block=finalized_block_number - block_confirmation,
            status=TransferStatus.PENDING,
        )

        if len(pending_transfers) == 0:
            _logger.info(
                f"No pending tx has been found. finalized_block_number: {finalized_block_number}"
            )
            await asyncio.sleep(delay)
            continue

        for transfer in pending_transfers:
            tx = await client.get_tx_by_hash(transfer.tx_hash)
            if tx:
                await to_finalized(
                    chain_id=chain.id,
                    finalized_block_number=finalized_block_number,
                    tx_hashes=[transfer.tx_hash],
                )

        # await to_reorg(chain.id, min(blocks_to_check), max(blocks_to_check))  # todo :: ???
