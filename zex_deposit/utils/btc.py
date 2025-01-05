import logging
from typing import Dict

from embit import bip32, script

from zex_deposit.clients import BTCAsyncClient
from zex_deposit.custom_types import ChainConfig, ChainId, RawTransfer, TransferStatus

logger = logging.getLogger(__name__)


def compute_create_btc_address(salt: int):
    from zex_deposit.config import BTC_DRIVE_PATH, BTC_NETWORK_CONFIG

    root_key = bip32.HDKey.from_seed(
        str(salt).encode(), version=BTC_NETWORK_CONFIG["xprv"]
    )
    derivation_path = BTC_DRIVE_PATH
    key = root_key.derive(derivation_path)
    tr_script = script.p2tr(key)
    return tr_script.address(BTC_NETWORK_CONFIG)


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
            if out_put["isAddress"] and tx["addresses"]:
                result.append(
                    RawTransfer(
                        tx_hash=tx["txid"],
                        block_number=block["height"],
                        chain_id=chain_id,
                        to=tx["addresses"][0],
                        value=tx["value"],
                        status=transfer_status,
                        token=tx.to,
                        block_timestamp=block["time"],
                    )
                )

    logger.debug(f"Observing block number {block_number} end")
    return result


async def get_btc_finalized_block_number(client: BTCAsyncClient, chain: ChainConfig):
    number = await client.get_latest_block_number()
    return number and number - chain.finalize_block_count
