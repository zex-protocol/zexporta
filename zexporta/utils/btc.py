import logging
from typing import Dict

from pyfrost.btc_utils import taproot_tweak_pubkey

from zexporta.clients import BTCAsyncClient
from zexporta.config import BTC_GROUP_KEY_PUB
from zexporta.custom_types import (
    BTCConfig,
    ChainId,
    RawTransfer,
    TransferStatus,
)

logger = logging.getLogger(__name__)


def compute_create_btc_address(salt: int):
    _, tweaked_pubkey = taproot_tweak_pubkey(BTC_GROUP_KEY_PUB, str(salt).encode())
    return tweaked_pubkey


def extract_btc_transfer_from_block(
    block_number: int,
    block: Dict,
    chain_id: ChainId,
    transfer_status: TransferStatus = TransferStatus.PENDING,
) -> list[RawTransfer]:
    logger.debug(f"Observing block number {block_number} start")
    result = []
    for tx in block["txs"]:
        for out_put in tx["vout"]:
            if out_put["isAddress"] and out_put["addresses"]:
                result.append(
                    RawTransfer(
                        tx_hash=tx["txid"],
                        block_number=block["height"],
                        chain_id=chain_id,
                        to=out_put["addresses"][0],
                        value=tx["value"],
                        status=transfer_status,
                        token=out_put["addresses"][0],
                        block_timestamp=block["time"],
                    )
                )

    logger.debug(f"Observing block number {block_number} end")
    return result


async def get_btc_finalized_block_number(
    client: BTCAsyncClient, chain: BTCConfig
) -> int:
    number = await client.get_latest_block_number()
    if number is None or not isinstance(number, int) or number <= 0:
        raise ValueError("Invalid block number received")
    return number and number - chain.finalize_block_count
