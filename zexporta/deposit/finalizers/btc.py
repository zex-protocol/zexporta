import asyncio
import logging.config

from zexporta.clients import get_btc_async_client
from zexporta.custom_types import BTCConfig, DepositStatus
from zexporta.db.deposit import find_deposit_by_status, to_finalized, to_reorg
from zexporta.deposit.config import LOGGER_PATH
from zexporta.utils.btc import get_btc_finalized_block_number
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

logging.config.dictConfig(get_logger_config(logger_path=f"{LOGGER_PATH}/finalizer.log"))  # type: ignore
logger = logging.getLogger(__name__)


# min block confirmation 6
async def update_btc_finalized_deposits(chain: BTCConfig, delay: int = 10):
    _logger = ChainLoggerAdapter(logger, chain.symbol)
    client = get_btc_async_client(chain)
    _logger.info(f"{chain.symbol} start finalizing")

    while True:
        finalized_block_number = await get_btc_finalized_block_number(
            client=client, chain=chain
        )
        _logger.info(
            f"finalizing {chain.symbol}, finalized_block_number: {finalized_block_number}"
        )
        pending_transfers = await find_deposit_by_status(
            chain_id=chain.chain_id,
            to_block=finalized_block_number,
            status=DepositStatus.PENDING,
        )

        if len(pending_transfers) == 0:
            _logger.info(
                f"No pending tx has been found. finalized_block_number: {finalized_block_number}"
            )
            await asyncio.sleep(delay)
            continue
        to_finalize_txs = []
        to_reorg_txs = []

        for transfer in pending_transfers:
            tx = await client.get_tx_by_hash(transfer.tx_hash)
            if tx:
                to_finalize_txs.append(transfer.tx_hash)
            else:
                to_reorg_txs.append(transfer.tx_hash)

        if to_finalize_txs:
            await to_finalized(
                chain_id=chain.chain_id,
                finalized_block_number=finalized_block_number,
                tx_hashes=to_finalize_txs,
            )
        if to_reorg_txs:
            await to_reorg(
                chain_id=chain.id,
                from_block=0,
                to_block=finalized_block_number,
                tx_hashes=to_reorg_txs,
            )
