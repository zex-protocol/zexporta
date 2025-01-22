from typing import Any

import httpx
from bitcoinutils.keys import PublicKey
from pydantic import BaseModel
from pyfrost.btc_utils import taproot_tweak_pubkey
from pyfrost.crypto_utils import code_to_pub

from zexporta.clients import ChainAsyncClient
from zexporta.config import BTC_GROUP_KEY_PUB
from zexporta.custom_types import (
    URL,
    Address,
    BlockNumber,
    BTCConfig,
    BTCTransfer,
    TxHash,
    Value,
)
from zexporta.utils.logger import ChainLoggerAdapter


# Model for Address Details
class AddressDetails(BaseModel):
    page: int
    totalPages: int
    itemsOnPage: int
    address: str
    balance: int
    totalReceived: int
    totalSent: int
    unconfirmedBalance: int
    unconfirmedTxs: int
    txs: int
    txids: list[str]


# Model for UTXO (Unspent Transaction Outputs)
class UTXO(BaseModel):
    txid: str
    vout: Value
    value: Value
    height: int
    confirmations: int
    coinbase: bool | None = None


# Common Model for all Transaction outputs (vout)
class Vout(BaseModel):
    value: Value
    n: int
    addresses: list[str] | None = None
    isAddress: bool
    hex: str | None = None
    scriptPubKey: dict | None = None


# Common Model for all Transaction inputs (vin)
class Vin(BaseModel):
    sequence: int | None = None
    n: int | None = None
    isAddress: bool | None = None
    coinbase: str | None = None
    txinwitness: list[str] | None = None


# Model for Transaction Details
class Transaction(BaseModel):
    txid: str
    vin: list[Vin]
    vout: list[Vout]
    blockHash: str
    blockHeight: int
    confirmations: int
    blockTime: int
    vsize: int
    value: Value
    valueIn: Value
    fees: Value


# Response for getting block by identifier (including multiple pages)
class Block(BaseModel):
    page: int
    totalPages: int
    itemsOnPage: int
    hash: str
    previousBlockHash: str
    nextBlockHash: str | None = None
    height: int
    confirmations: int
    size: int
    time: int
    version: int
    merkleRoot: str
    nonce: str
    difficulty: str
    bits: str
    txCount: int
    txs: list[Transaction] | None = None


class BTCClientError(Exception):
    """Base exception for BTCAsyncClient errors."""


class BTCRequestError(BTCClientError):
    """Exception raised for errors during HTTP requests."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BTCConnectionError(BTCClientError):
    """Exception raised for connection-related errors."""


class BTCTimeoutError(BTCClientError):
    """Exception raised when a request times out."""


class BTCResponseError(BTCClientError):
    """Exception raised for invalid or unexpected responses."""


class BTCAnkrAsyncClient:
    def __init__(self, base_url: URL, indexer_url: URL):
        self.base_url = base_url
        self.block_book_base_url = indexer_url
        self._client = httpx.AsyncClient()

    @property
    def client(self):
        if self._client.is_closed:
            self._client = httpx.AsyncClient()
        return self._client

    async def _request(
        self,
        method: str = "GET",
        url: str = "",
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_data: Any = None,  # Add json_data parameter
    ) -> dict[str, Any]:
        try:
            # Choose between data and json based on the request
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": 15,
            }
            if json_data is not None:
                request_kwargs["json"] = json_data
            elif data is not None:
                request_kwargs["data"] = data

            response = await self.client.request(**request_kwargs)
            response.raise_for_status()
            resp = response.json()

            if isinstance(resp, dict) and resp.get("error"):
                raise BTCRequestError(f"Ankr error occurred: {resp.get('error')}")
            return resp
        except httpx.HTTPStatusError as http_err:
            # Raised for non-2xx responses
            raise BTCRequestError(
                f"HTTP error occurred: {http_err.response.status_code} {http_err.response.reason_phrase}",
                status_code=http_err.response.status_code,
            ) from http_err
        except httpx.ConnectError as conn_err:
            # Raised for connection-related errors
            raise BTCConnectionError(
                f"Connection error occurred: {conn_err}"
            ) from conn_err
        except httpx.TimeoutException as timeout_err:
            # Raised when a request times out
            raise BTCTimeoutError(f"Request timed out: {timeout_err}") from timeout_err
        except httpx.RequestError as req_err:
            # Base class for all other request-related errors
            raise BTCClientError(
                f"An error occurred while requesting {req_err.request.url!r}."
            ) from req_err
        except ValueError as json_err:
            # Raised if response.json() fails
            raise BTCResponseError(
                f"Failed to parse JSON response: {json_err}"
            ) from json_err

    async def get_tx_by_hash(self, tx_hash: TxHash) -> Transaction:
        url = f"{self.block_book_base_url}/api/v2/tx/{tx_hash}"
        data = await self._request("GET", url)
        return Transaction.model_validate(data)

    async def get_address_details(
        self, address: str, details: str | None = "txids"
    ) -> AddressDetails:
        url = f"{self.block_book_base_url}/api/v2/address/{address}"
        params = {"details": details}
        data = await self._request("GET", url, params=params)
        return AddressDetails.model_validate(data)

    async def get_utxo(self, address: str, confirmed: bool = True) -> list[UTXO]:
        url = f"{self.block_book_base_url}/api/v2/utxo/{address}"
        params = {"confirmed": str(confirmed).lower()}
        data = await self._request("GET", url, params=params)
        return [UTXO.model_validate(i) for i in data]

    async def get_block_by_identifier(self, identifier: str | int) -> Block:
        page = 1
        all_txs = []  # List to store all transactions across pages
        while True:
            url = f"{self.block_book_base_url}/api/v2/block/{identifier}"
            params = {"page": page}
            response = await self._request("GET", url, params=params)
            data = response
            txs = response.get("txs", [])
            all_txs.extend(txs)  # Add the current page's txs to the overall list

            total_pages = response.get("totalPages", 1)
            if page >= total_pages:
                break  # Exit the loop if we've reached the last page

            page += 1  # Move to the next page
        data["txs"] = all_txs
        return Block.model_validate(data)

    async def send_tx(self, hex_tx_data: str) -> str | None:
        url = f"{self.block_book_base_url}/api/v2/sendtx/{hex_tx_data}"
        resp = await self._request("GET", url)
        return resp and resp["result"]  # type: ignore

    async def get_latest_block(self) -> Block:
        number = await self.get_latest_block_number()
        return await self.get_block_by_identifier(number)

    async def get_latest_block_number(self) -> BlockNumber:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "getblockchaininfo", "params": []}
        headers = {
            "Content-Type": "application/json",
        }
        resp = await self._request("POST", url, headers=headers, json_data=data)
        return resp["result"]["blocks"]  # type: ignore


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
        self, tx_hash: TxHash, logger: ChainLoggerAdapter
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
        logger: ChainLoggerAdapter,
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
    if client := _async_clients.get(chain.chain_symbol.value):
        return client
    client = BTCAsyncClient(chain)
    _async_clients[chain.chain_symbol.value] = client
    return client


def compute_btc_address(salt: int) -> str:
    _, public_key = taproot_tweak_pubkey(BTC_GROUP_KEY_PUB, str(salt).encode())
    public_key = code_to_pub(int(public_key.hex(), 16))
    x_hex = hex(public_key.x)[2:].zfill(64)
    y_hex = hex(public_key.y)[2:].zfill(64)
    prefix = "02" if int(y_hex, 16) % 2 == 0 else "03"
    compressed_pubkey = prefix + x_hex
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address.to_string()
