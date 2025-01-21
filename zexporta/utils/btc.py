import logging

from bitcoinutils.keys import PublicKey
from pyfrost.btc_utils import taproot_tweak_pubkey
from pyfrost.crypto_utils import code_to_pub

from zexporta.clients import BTCAsyncClient
from zexporta.clients.btc import Block
from zexporta.config import BTC_GROUP_KEY_PUB
from zexporta.custom_types import (
    BTCConfig,
    ChainSymbol,
    DepositStatus,
    Transfer,
)

logger = logging.getLogger(__name__)


def compute_create_btc_address(salt: int):
    _, public_key = taproot_tweak_pubkey(BTC_GROUP_KEY_PUB, str(salt).encode())
    public_key = code_to_pub(int(public_key.hex(), 16))
    x_hex = hex(public_key.x)[2:].zfill(64)
    y_hex = hex(public_key.y)[2:].zfill(64)
    prefix = "02" if int(y_hex, 16) % 2 == 0 else "03"
    compressed_pubkey = prefix + x_hex
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address


def extract_btc_transfer_from_block(
    block_number: int,
    block: Block,
    chain_symbol: ChainSymbol,
    transfer_status: DepositStatus = DepositStatus.PENDING,
) -> list[Transfer]:
    logger.debug(f"Observing block number {block_number} start")
    result = []
    if block.txs is None:
        return []
    for tx in block.txs:
        for out_put in tx.vout:
            if out_put.isAddress and out_put.addresses:
                result.append(
                    Transfer(
                        tx_hash=tx.txid,
                        block_number=block.height,
                        chain_symbol=chain_symbol,
                        to=out_put.addresses[0],
                        value=tx.value,
                        token=out_put.addresses[0],
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
