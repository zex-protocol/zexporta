import logging
import os

from bitcoinutils.keys import PublicKey
from pyfrost.btc_utils import taproot_tweak_pubkey
from pyfrost.crypto_utils import code_to_pub, pub_compress

from clients.abstract import ChainAsyncClient
from clients.custom_types import BlockNumber, TxHash

from .custom_types import Address, BTCConfig, BTCTransfer
from .rpc.ankr import BTCAnkrAsyncClient, Transaction


class BTCAsyncClient(ChainAsyncClient):
    def __init__(self, chain: BTCConfig):
        self.chain = chain
        self.btc = None

    @property
    def client(self) -> BTCAnkrAsyncClient:
        if self.btc is not None:
            return self.btc
        self.btc = BTCAnkrAsyncClient(
            base_url=self.chain.private_rpc, indexer_url=self.chain.private_indexer_rpc
        )
        return self.btc

    async def get_transfer_by_tx_hash(self, tx_hash: TxHash) -> list[BTCTransfer]:
        tx = await self.client.get_tx_by_hash(tx_hash)
        return self._parse_transfer(tx)

    async def get_finalized_block_number(self) -> BlockNumber:
        finalize_block_count = self.chain.finalize_block_count or 0
        finalized_block_number = (
            await self.get_latest_block_number()
        ) - finalize_block_count
        return finalized_block_number

    async def get_token_decimals(self, token_address: Address) -> int:
        return 8

    async def is_transaction_successful(
        self, tx_hash: TxHash, logger: logging.Logger | logging.LoggerAdapter
    ) -> bool:
        if await self.client.get_tx_by_hash(tx_hash):
            return True
        return False

    async def get_block_tx_hash(
        self, block_number: BlockNumber, **kwargs
    ) -> list[TxHash]:
        block = await self.client.get_block_by_identifier(block_number)
        return [tx.txid for tx in block.txs]  # type: ignore

    async def get_latest_block_number(self) -> BlockNumber:
        return await self.client.get_latest_block_number()

    async def extract_transfer_from_block(
        self,
        block_number: BlockNumber,
        logger: logging.Logger | logging.LoggerAdapter,
        **kwargs,
    ) -> list[BTCTransfer]:
        logger.debug(f"Observing block number {block_number} start")
        block = await self.client.get_block_by_identifier(block_number)
        result = []
        for tx in block.txs:  # type: ignore
            transfer = self._parse_transfer(tx)
            if transfer:
                result.extend(transfer)
        logger.debug(f"Observing block number {block_number} end")
        return result

    def _parse_transfer(self, tx: Transaction) -> list[BTCTransfer]:
        transfers = []
        for output in tx.vout:
            if output.isAddress:
                transfers.append(
                    BTCTransfer(
                        tx_hash=tx.txid,
                        block_number=tx.blockHeight,
                        chain_symbol=self.chain.chain_symbol,
                        to=output.addresses[0],  # type: ignore
                        value=output.value,
                        token="0x0000000000000000000000000000000000000000",
                        index=output.n,
                    )
                )
        return transfers


_async_clients: dict[str, BTCAsyncClient] = {}


def get_btc_async_client(chain: BTCConfig) -> BTCAsyncClient:
    if client := _async_clients.get(chain.chain_symbol):
        return client
    client = BTCAsyncClient(chain)
    _async_clients[chain.chain_symbol] = client
    return client


def compute_btc_address(salt: int) -> Address:
    btc_group_key_pub = int(os.environ["BTC_GROUP_KEY_PUB"])
    public_key = code_to_pub(btc_group_key_pub)
    public_key = pub_compress(public_key=public_key)
    taproot_public_key, _ = taproot_tweak_pubkey(
        public_key, salt.to_bytes(8, byteorder="big")
    )
    x_hex = hex(taproot_public_key.x)[2:].zfill(64)
    y_hex = hex(taproot_public_key.y)[2:].zfill(64)
    prefix = "02" if int(y_hex, 16) % 2 == 0 else "03"
    compressed_pubkey = prefix + x_hex
    taproot_public_key = PublicKey(compressed_pubkey)
    taproot_address = taproot_public_key.get_taproot_address()
    return taproot_address.to_string()
