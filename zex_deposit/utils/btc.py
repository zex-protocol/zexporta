import hashlib
import logging
from typing import Dict

from bitcoinutils.keys import PublicKey
from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point

from zex_deposit.clients import BTCAsyncClient
from zex_deposit.config import BTC_PUBLIC_HEX
from zex_deposit.custom_types import (
    ChainConfig,
    ChainId,
    RawTransfer,
    TransferStatus,
)

logger = logging.getLogger(__name__)


def compute_create_btc_address(salt: int):
    # priv = PrivateKey.from_wif("cRPxBiKrJsH94FLugmiL4xnezMyoFqGcf4kdgNXGuypNERhMK6AT")
    # pub = priv.get_public_key()

    # pub = PublicKey.from_hex('03a957ff7ead882e4c95be2afa684ab0e84447149883aba60c067adc054472785b')
    pub = PublicKey.from_hex(BTC_PUBLIC_HEX)

    # Original pubkey point
    x = pub.key.pubkey.point.x()
    y = pub.key.pubkey.point.y()

    # Salt & hash tweak
    tweak = hashlib.sha256(pub.to_bytes() + str(salt).encode()).digest()
    tweak_int = int.from_bytes(tweak, "big")

    # Calculate the tweaked point
    G = SECP256k1.generator
    tweak_point = tweak_int * G
    original_point = Point(SECP256k1.curve, x, y, SECP256k1.order)
    tweaked_point = original_point + tweak_point

    # Convert tweaked point to compressed pubkey (BIP340 style)
    x_coord = tweaked_point.x()
    y_coord = tweaked_point.y()

    # Taproot keys use 0x02 if y is even, 0x03 if odd
    prefix = b"\x02" if (y_coord % 2 == 0) else b"\x03"
    tweaked_pub_bytes = prefix + x_coord.to_bytes(32, "big")

    # Use bitcoinutils to wrap and get Taproot address
    tweaked_pub_obj = PublicKey.from_hex(tweaked_pub_bytes.hex())
    taproot_addr = tweaked_pub_obj.get_taproot_address()

    return taproot_addr.to_string()


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


async def get_btc_finalized_block_number(client: BTCAsyncClient, chain: ChainConfig):
    number = await client.get_latest_block_number()
    return number and number - chain.finalize_block_count
